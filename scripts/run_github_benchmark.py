"""Comprehensive benchmark execution script with verified metrics and machine-readable audit logs.

Supports both:
- Simulated / Mock mode (for fast CI testing)
- Real Neural Mode: Real Laya ModernBERT decision adapter + Real local causal LM
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from slothswitch.adapters.decision import MockDecisionAdapter
from slothswitch.adapters.decision.laya_adapter import LayaDecisionAdapter
from slothswitch.adapters.generative.gemma_local import LocalGemmaAdapter, MockGenerativeAdapter
from slothswitch.adapters.tools.github import GitHubToolAdapter
from slothswitch.evaluation.workflow_benchmark import WorkflowBenchmarkRunner
from slothswitch.workflows.github_pr_management import create_github_workflow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("benchmark")


def main() -> None:
    parser = argparse.ArgumentParser(description="SlothSwitch GitHub Workflow Benchmark Runner")
    parser.add_argument("--real", action="store_true", help="Use real Laya and real local causal LM")
    parser.add_argument("--execute-tools", action="store_true", help="Execute tools against live GitHub API")
    parser.add_argument("--split", default="test", choices=["train", "val", "test", "all"], help="Dataset split to evaluate")
    args = parser.parse_args()

    data_path = Path("datasets/github_workflow_benchmark.json")
    if not data_path.exists():
        print(f"Error: {data_path} not found. Run datasets/generate_github_benchmark.py first.")
        return

    with open(data_path, "r", encoding="utf-8") as f:
        samples = json.load(f)

    if args.split != "all":
        eval_samples = [s for s in samples if s.get("split") == args.split]
    else:
        eval_samples = samples

    print("\n======================================================================")
    print(f"RUNNING BENCHMARK AUDIT (Mode: {'REAL NEURAL INFERENCE' if args.real else 'MOCK/SIMULATED'})")
    print(f"Split: {args.split.upper()} ({len(eval_samples)} samples)")
    print(f"Live Tools Execution: {args.execute_tools}")
    print("======================================================================\n")

    wf = create_github_workflow()
    tool_adapter = GitHubToolAdapter()

    if args.real:
        print("Initializing real Laya ModernBERT Decision Adapter (convaiinnovations/laya)...")
        decision_adapter = LayaDecisionAdapter(preload=True)
        print("Initializing real Local Causal LM Adapter (TinyLlama-1.1B)...")
        # Use TinyLlama as verified cached local causal LM
        generative_adapter = LocalGemmaAdapter(model_id="TinyLlama/TinyLlama-1.1B-Chat-v1.0", lazy_load=False)
    else:
        decision_adapter = MockDecisionAdapter()
        generative_adapter = MockGenerativeAdapter()

    runner = WorkflowBenchmarkRunner(
        workflow=wf,
        decision_adapter=decision_adapter,
        generative_adapter=generative_adapter,
        tool_adapter=tool_adapter,
        execute_live_tools=args.execute_tools,
    )

    print("Running Baseline A (Always-Gemma)...")
    res_a = runner.run_baseline_a_always_gemma(eval_samples)

    print("Running Baseline B (Deterministic Rules)...")
    res_b = runner.run_baseline_b_deterministic_rules(eval_samples)

    print("Running Baseline C (SlothSwitch)...")
    res_c = runner.run_baseline_c_slothswitch(eval_samples)

    # Prepare machine-readable per-example audit report
    audit_report = {
        "metadata": {
            "mode": "real_neural_inference" if args.real else "mock_simulated",
            "split": args.split,
            "sample_count": len(eval_samples),
            "decision_model": decision_adapter.name,
            "generative_model": generative_adapter.name,
            "execute_live_tools": args.execute_tools,
        },
        "summary": {
            "baseline_a": {k: v for k, v in res_a.items() if k != "records"},
            "baseline_b": {k: v for k, v in res_b.items() if k != "records"},
            "baseline_c": {k: v for k, v in res_c.items() if k != "records"},
        },
        "per_sample_audit_records": {
            "baseline_a": res_a["records"],
            "baseline_b": res_b["records"],
            "baseline_c": res_c["records"],
        },
    }

    out_json = Path("logs/audit_benchmark_detailed.json")
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(audit_report, f, indent=2)

    # Save summary json
    summary_path = Path("logs/github_benchmark_results.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(audit_report["summary"], f, indent=2)

    print("\n" + "=" * 70)
    print("SLOTHSWITCH AUDITED BENCHMARK RESULTS")
    print("=" * 70)
    for b in [res_a, res_b, res_c]:
        print(f"\n[{b['baseline']}] (Real Inference: {b['is_real_inference']})")
        print(f"  Strict Action Accuracy:    {b['action_accuracy'] * 100:.1f}% ({b['action_accuracy_numerator']} / {b['action_accuracy_denominator']})")
        print(f"  Outcome Category Accuracy: {b['outcome_accuracy'] * 100:.1f}% ({b['outcome_accuracy_numerator']} / {b['outcome_accuracy_denominator']})")
        print(f"  End-to-End Task Success:   {b['end_to_end_task_success_rate'] * 100:.1f}% ({b['task_success_numerator']} / {b['task_success_denominator']})")
        print(f"  Generative Model Calls:    {b['gemma_calls']} / {b['total_samples']}")
        print(f"  Direct Tools Selected:     {b['direct_tools_selected']}")
        print(f"  Direct Tools Attempted:    {b['direct_tools_attempted']}")
        print(f"  Direct Tools Succeeded:    {b['direct_tools_succeeded']}")
        print(f"  Avoided Generative Calls:  {b['avoided_gemma_calls']} / {b['total_samples']} ({b['avoided_gemma_pct']}%)")
        print(f"  Total Generative Tokens:   {b['total_generative_tokens']}")
        print(f"  Median Total Latency:      {b['median_total_latency_ms']} ms")
        print(f"  P95 Total Latency:         {b['p95_total_latency_ms']} ms")
        if "median_direct_path_latency_ms" in b:
            print(f"  Direct Path Latency:       Median: {b['median_direct_path_latency_ms']} ms | P95: {b['p95_direct_path_latency_ms']} ms")
        if "median_generative_path_latency_ms" in b:
            print(f"  Generative Path Latency:   Median: {b['median_generative_path_latency_ms']} ms | P95: {b['p95_generative_path_latency_ms']} ms")
        if "median_decision_latency_ms" in b:
            print(f"  Decision Overhead:         Median: {b['median_decision_latency_ms']} ms")
        if "median_policy_latency_ms" in b:
            print(f"  Policy Gate Overhead:      Median: {b['median_policy_latency_ms']} ms")

    print("\n" + "=" * 70)
    print(f"Audit report saved to: {out_json}")
    print(f"Summary report saved to: {summary_path}")


if __name__ == "__main__":
    main()
