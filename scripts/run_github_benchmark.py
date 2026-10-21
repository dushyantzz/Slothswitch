"""Benchmark execution script for comparing the 3 baselines on the GitHub workflow dataset.

Outputs both a structured JSON report and a formatted Markdown summary.
"""

from __future__ import annotations

import json
from pathlib import Path

from slothswitch.evaluation.workflow_benchmark import WorkflowBenchmarkRunner
from slothswitch.workflows.github_pr_management import create_github_workflow


def main() -> None:
    data_path = Path("datasets/github_workflow_benchmark.json")
    if not data_path.exists():
        print(f"Error: {data_path} not found. Run datasets/generate_github_benchmark.py first.")
        return

    with open(data_path, "r", encoding="utf-8") as f:
        samples = json.load(f)

    # Strictly evaluate on held-out test split
    test_samples = [s for s in samples if s.get("split") == "test"]
    print(f"Loaded {len(samples)} total samples. Evaluating on {len(test_samples)} held-out test samples...")

    wf = create_github_workflow()
    runner = WorkflowBenchmarkRunner(workflow=wf)

    res_a = runner.run_baseline_a_always_gemma(test_samples)
    res_b = runner.run_baseline_b_deterministic_rules(test_samples)
    res_c = runner.run_baseline_c_slothswitch(test_samples)

    report = {
        "dataset": "github_workflow_benchmark.json",
        "split": "test",
        "total_test_samples": len(test_samples),
        "baselines": [res_a, res_b, res_c],
    }

    out_json = Path("logs/github_benchmark_results.json")
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 70)
    print("SLOTHSWITCH ARCHITECTURE REFACTORING - BENCHMARK RESULTS")
    print("=" * 70)
    for b in [res_a, res_b, res_c]:
        print(f"\n[{b['baseline']}]")
        print(f"  Accuracy:            {b['accuracy'] * 100:.1f}%")
        print(f"  Gemma Model Calls:   {b['gemma_calls']} / {b['total_samples']}")
        print(f"  Direct Tool Calls:   {b['direct_tool_calls']}")
        print(f"  Avoided Gemma Calls: {b['avoided_gemma_calls']} ({b['avoided_gemma_pct']}%)")
        print(f"  Total Tokens:        {b['total_tokens_used']}")
        print(f"  Median Latency:      {b['median_latency_ms']} ms")
        print(f"  P95 Latency:         {b['p95_latency_ms']} ms")
    print("\n" + "=" * 70)
    print(f"Saved benchmark results to {out_json}")


if __name__ == "__main__":
    main()
