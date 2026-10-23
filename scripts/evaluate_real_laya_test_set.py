"""Evaluate Real Laya ModernBERT checkpoint on the entire 48-sample held-out test set.

Measures:
- Strict action accuracy (exact action_id match)
- Outcome category accuracy
- Real decision latency (cold start vs warm per-sample)
- Calibrated confidence distribution
- Complete per-sample prediction log
"""

from __future__ import annotations

import json
import statistics
import time
from pathlib import Path

from slothswitch.adapters.decision.laya_adapter import LayaDecisionAdapter
from slothswitch.workflows.github_pr_management import create_github_workflow


def main() -> None:
    data_path = Path("datasets/github_workflow_benchmark.json")
    with open(data_path, "r", encoding="utf-8") as f:
        all_samples = json.load(f)

    test_samples = [s for s in all_samples if s.get("split") == "test"]
    print(f"Loaded {len(test_samples)} held-out test samples (strictly unseen repositories).")

    wf = create_github_workflow()
    print("Loading real Laya checkpoint ('convaiinnovations/laya')...")
    cold_start_t0 = time.perf_counter()
    laya = LayaDecisionAdapter(preload=True)
    cold_load_ms = (time.perf_counter() - cold_start_t0) * 1000
    print(f"Laya loaded in {cold_load_ms:.2f} ms.")

    records = []
    action_correct = 0
    outcome_correct = 0
    latencies: list[float] = []

    print("\nRunning live inference on 48 test samples...")
    for idx, sample in enumerate(test_samples, 1):
        req_id = sample["request_id"]
        content = sample["content"]
        exp_action = sample.get("expected_action", "none")
        exp_outcome = sample.get("expected_outcome", "EXECUTE_TOOL")

        t0 = time.perf_counter()
        decision = laya.predict_action(content, wf)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        latencies.append(elapsed_ms)

        pred_action = decision.action_id
        pred_outcome = decision.outcome.value

        is_action_match = (pred_action == exp_action)
        is_outcome_match = (pred_outcome == exp_outcome)

        if is_action_match:
            action_correct += 1
        if is_outcome_match:
            outcome_correct += 1

        print(f"[{idx:02d}/48] {req_id} | Match: {is_action_match} | Pred: {pred_action:35s} | Exp: {exp_action:35s} ({elapsed_ms:.1f} ms)")

        records.append({
            "request_id": req_id,
            "content": content,
            "expected_action": exp_action,
            "predicted_action": pred_action,
            "action_match": is_action_match,
            "expected_outcome": exp_outcome,
            "predicted_outcome": pred_outcome,
            "outcome_match": is_outcome_match,
            "confidence": decision.confidence,
            "reasoning": decision.reasoning,
            "latency_ms": round(elapsed_ms, 2),
        })

    total = len(test_samples)
    out_json = Path("logs/real_laya_test_predictions.json")
    out_json.parent.mkdir(parents=True, exist_ok=True)

    summary = {
        "model": "convaiinnovations/laya",
        "split": "test",
        "total_samples": total,
        "strict_action_accuracy": {
            "numerator": action_correct,
            "denominator": total,
            "value": round(action_correct / total, 4),
            "percentage": f"{action_correct / total * 100:.2f}%",
        },
        "outcome_category_accuracy": {
            "numerator": outcome_correct,
            "denominator": total,
            "value": round(outcome_correct / total, 4),
            "percentage": f"{outcome_correct / total * 100:.2f}%",
        },
        "latencies_ms": {
            "cold_load_ms": round(cold_load_ms, 2),
            "median_warm_ms": round(statistics.median(latencies), 2),
            "mean_warm_ms": round(statistics.mean(latencies), 2),
            "p95_warm_ms": round(statistics.quantiles(latencies, n=20)[18], 2),
            "min_warm_ms": round(min(latencies), 2),
            "max_warm_ms": round(max(latencies), 2),
        },
        "per_sample_predictions": records,
    }

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 70)
    print("REAL LAYA EVALUATION COMPLETE")
    print("=" * 70)
    print(f"Strict Action Accuracy:    {action_correct}/{total} ({action_correct/total*100:.2f}%)")
    print(f"Outcome Category Accuracy: {outcome_correct}/{total} ({outcome_correct/total*100:.2f}%)")
    print(f"Median Warm Latency:       {statistics.median(latencies):.2f} ms")
    print(f"P95 Warm Latency:          {statistics.quantiles(latencies, n=20)[18]:.2f} ms")
    print(f"Saved full predictions to: {out_json}")


if __name__ == "__main__":
    main()
