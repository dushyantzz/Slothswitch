"""Evaluation harness for comparing SlothSwitch routing strategies against baselines.

Supports:
- Fixed capable-model baseline (all requests → one model)
- Deterministic baseline (rules only)
- SlothSwitch (decision model + policy routing)
- Metrics: route accuracy, macro-F1, per-route precision/recall, coverage, cost
"""

from __future__ import annotations

import json
import logging
from collections import Counter
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dataset loading
# ---------------------------------------------------------------------------

def load_dataset(path: str) -> list[dict[str, Any]]:
    """Load a JSON evaluation dataset.

    Expected format: list of objects with at minimum:
    - "request_id": str
    - "content": str
    - "acceptable_routes": list[str]  (gold labels — may have multiple acceptable)
    """
    data_path = Path(path)
    if not data_path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    with open(data_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    if not isinstance(dataset, list) or not dataset:
        raise ValueError("Dataset must be a non-empty JSON array")

    return dataset


def split_dataset(
    dataset: list[dict],
    test_ratio: float = 0.2,
    seed: int = 42,
) -> tuple[list[dict], list[dict]]:
    """Split dataset into dev/validation and held-out test sets.

    If items contain an explicit 'split' key ('dev' vs 'test'), uses that partitioning.
    Otherwise uses deterministic shuffling with the provided seed to prevent leakage.
    """
    has_explicit = any("split" in item for item in dataset)
    if has_explicit:
        dev_items = [item for item in dataset if item.get("split") == "dev"]
        test_items = [item for item in dataset if item.get("split") == "test"]
        if dev_items and test_items:
            return dev_items, test_items

    import random

    rng = random.Random(seed)
    shuffled = list(dataset)
    rng.shuffle(shuffled)

    split_idx = max(1, int(len(shuffled) * (1 - test_ratio)))
    return shuffled[:split_idx], shuffled[split_idx:]



# ---------------------------------------------------------------------------
# Evaluation metrics
# ---------------------------------------------------------------------------

class EvaluationResult:
    """Container for evaluation metrics, separated latencies, and quality-cost accounting."""

    def __init__(self) -> None:
        self.total: int = 0
        self.correct: int = 0
        self.predictions: list[str] = []
        self.gold_labels: list[list[str]] = []
        self.per_route_tp: Counter = Counter()
        self.per_route_fp: Counter = Counter()
        self.per_route_fn: Counter = Counter()
        self.latencies_ms: list[float] = []
        self.router_overhead_ms: list[float] = []
        self.decision_latencies_ms: list[float] = []
        self.task_latencies_ms: list[float] = []
        self.total_e2e_latencies_ms: list[float] = []
        self.costs_usd: list[float] = []
        self.model_calls: Counter = Counter()
        self.total_prompt_tokens: int = 0
        self.total_completion_tokens: int = 0
        self.quality_scores: list[float] = []
        self.fallback_count: int = 0
        self.cost_is_simulated: bool = True

    def add(
        self,
        predicted: str,
        acceptable: list[str],
        latency_ms: float = 0.0,
        cost_usd: float = 0.0,
        router_overhead_ms: float = 0.0,
        decision_latency_ms: float = 0.0,
        task_latency_ms: float = 0.0,
        total_e2e_ms: float = 0.0,
        model_name: str | None = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        quality_score: float | None = None,
        cost_is_simulated: bool = True,
    ) -> None:
        """Record a single prediction against acceptable gold labels and its execution metrics."""
        self.total += 1
        self.predictions.append(predicted)
        self.gold_labels.append(acceptable)

        is_correct = predicted in acceptable
        if is_correct:
            self.correct += 1
            self.per_route_tp[predicted] += 1
        else:
            self.per_route_fp[predicted] += 1
            for gold in acceptable:
                self.per_route_fn[gold] += 1

        if predicted == "FALLBACK":
            self.fallback_count += 1

        self.latencies_ms.append(latency_ms)
        self.costs_usd.append(cost_usd)
        self.router_overhead_ms.append(router_overhead_ms)
        self.decision_latencies_ms.append(decision_latency_ms)
        self.task_latencies_ms.append(task_latency_ms)
        self.total_e2e_latencies_ms.append(total_e2e_ms or latency_ms)

        if model_name:
            self.model_calls[model_name] += 1

        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.cost_is_simulated = self.cost_is_simulated and cost_is_simulated

        # Task quality score (default to 1.0 if route is acceptable, else 0.4 if unknown)
        if quality_score is not None:
            self.quality_scores.append(quality_score)
        else:
            self.quality_scores.append(1.0 if is_correct else 0.4)

    @property
    def accuracy(self) -> float:
        return self.correct / self.total if self.total else 0.0

    @property
    def fallback_rate(self) -> float:
        return self.fallback_count / self.total if self.total else 0.0

    @property
    def mean_task_quality(self) -> float:
        return sum(self.quality_scores) / len(self.quality_scores) if self.quality_scores else 0.0

    def per_route_precision(self) -> dict[str, float]:
        """Precision per route."""
        routes = set(list(self.per_route_tp.keys()) + list(self.per_route_fp.keys()))
        result = {}
        for r in routes:
            tp = self.per_route_tp[r]
            fp = self.per_route_fp[r]
            result[r] = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        return result

    def per_route_recall(self) -> dict[str, float]:
        """Recall per route."""
        routes = set(list(self.per_route_tp.keys()) + list(self.per_route_fn.keys()))
        result = {}
        for r in routes:
            tp = self.per_route_tp[r]
            fn = self.per_route_fn[r]
            result[r] = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        return result

    def macro_f1(self) -> float:
        """Macro-averaged F1 across routes."""
        precision = self.per_route_precision()
        recall = self.per_route_recall()
        all_routes = set(precision.keys()) | set(recall.keys())
        f1s = []
        for r in all_routes:
            p = precision.get(r, 0)
            rec = recall.get(r, 0)
            f1 = 2 * p * rec / (p + rec) if (p + rec) > 0 else 0.0
            f1s.append(f1)
        return sum(f1s) / len(f1s) if f1s else 0.0

    def summary(self) -> dict[str, Any]:
        """Return a summary dictionary of all metrics."""
        return {
            "total_examples": self.total,
            "accuracy": round(self.accuracy, 4),
            "macro_f1": round(self.macro_f1(), 4),
            "mean_task_quality": round(self.mean_task_quality, 4),
            "fallback_rate": round(self.fallback_rate, 4),
            "per_route_precision": {k: round(v, 4) for k, v in self.per_route_precision().items()},
            "per_route_recall": {k: round(v, 4) for k, v in self.per_route_recall().items()},
            "avg_routing_latency_ms": round(
                sum(self.latencies_ms) / len(self.latencies_ms), 3
            ) if self.latencies_ms else 0.0,
            "avg_router_overhead_ms": round(
                sum(self.router_overhead_ms) / len(self.router_overhead_ms), 3
            ) if self.router_overhead_ms else 0.0,
            "avg_decision_model_latency_ms": round(
                sum(self.decision_latencies_ms) / len(self.decision_latencies_ms), 3
            ) if self.decision_latencies_ms else 0.0,
            "avg_task_model_latency_ms": round(
                sum(self.task_latencies_ms) / len(self.task_latencies_ms), 3
            ) if self.task_latencies_ms else 0.0,
            "avg_total_e2e_latency_ms": round(
                sum(self.total_e2e_latencies_ms) / len(self.total_e2e_latencies_ms), 3
            ) if self.total_e2e_latencies_ms else 0.0,
            "total_cost_usd": round(sum(self.costs_usd), 6),
            "cost_is_simulated": self.cost_is_simulated,
            "model_calls": dict(self.model_calls),
            "token_usage": {
                "prompt_tokens": self.total_prompt_tokens,
                "completion_tokens": self.total_completion_tokens,
                "total_tokens": self.total_prompt_tokens + self.total_completion_tokens,
            },
        }

