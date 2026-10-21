"""Unit tests for WorkflowBenchmarkRunner across the 3 baselines."""

import json
from pathlib import Path

from slothswitch.evaluation.workflow_benchmark import WorkflowBenchmarkRunner
from slothswitch.workflows.github_pr_management import create_github_workflow


def test_workflow_benchmark_baselines_comparison() -> None:
    """Benchmark accurately compares Baseline A, Baseline B, and Baseline C."""
    benchmark_file = Path("datasets/github_workflow_benchmark.json")
    assert benchmark_file.exists(), "Benchmark dataset must exist"

    with open(benchmark_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Use held-out test split for evaluation
    test_samples = [d for d in data if d.get("split") == "test"]
    assert len(test_samples) == 33, f"Expected 33 test samples, got {len(test_samples)}"

    wf = create_github_workflow()
    runner = WorkflowBenchmarkRunner(workflow=wf)

    # 1. Baseline A: Always-Gemma
    res_a = runner.run_baseline_a_always_gemma(test_samples)
    assert res_a["gemma_calls"] == 33
    assert res_a["avoided_gemma_calls"] == 0
    assert res_a["avoided_gemma_pct"] == 0.0

    # 2. Baseline B: Deterministic Rules
    res_b = runner.run_baseline_b_deterministic_rules(test_samples)
    assert res_b["gemma_calls"] < 33
    assert res_b["avoided_gemma_calls"] > 0

    # 3. Baseline C: SlothSwitch
    res_c = runner.run_baseline_c_slothswitch(test_samples)
    assert res_c["total_samples"] == 33
    # SlothSwitch should avoid the majority of Gemma calls by executing tools directly
    assert res_c["avoided_gemma_pct"] >= 70.0
    assert res_c["direct_tool_calls"] > 0
    assert res_c["accuracy"] > res_a["accuracy"]
