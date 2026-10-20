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
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Optional

from slothswitch.schemas import RouteCategory

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

    Uses deterministic shuffling to avoid leakage.
    """
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
    """Container for evaluation metrics."""

    def __init__(self) -> None:
        self.total: int = 0
        self.correct: int = 0
        self.predictions: list[str] = []
        self.gold_labels: list[list[str]] = []
        self.per_route_tp: Counter = Counter()
        self.per_route_fp: Counter = Counter()
        self.per_route_fn: Counter = Counter()
        self.latencies_ms: list[float] = []
        self.costs_usd: list[float] = []
        self.fallback_count: int = 0

    def add(
        self,
        predicted: str,
        acceptable: list[str],
        latency_ms: float = 0.0,
        cost_usd: float = 0.0,
    ) -> None:
        """Record a single prediction against acceptable gold labels."""
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

    @property
    def accuracy(self) -> float:
        return self.correct / self.total if self.total else 0.0

    @property
    def fallback_rate(self) -> float:
        return self.fallback_count / self.total if self.total else 0.0

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
            "fallback_rate": round(self.fallback_rate, 4),
            "per_route_precision": {k: round(v, 4) for k, v in self.per_route_precision().items()},
            "per_route_recall": {k: round(v, 4) for k, v in self.per_route_recall().items()},
            "avg_latency_ms": round(
                sum(self.latencies_ms) / len(self.latencies_ms), 2
            ) if self.latencies_ms else 0.0,
            "total_estimated_cost_usd": round(sum(self.costs_usd), 4),
        }
