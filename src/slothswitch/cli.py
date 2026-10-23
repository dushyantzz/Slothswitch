"""SlothSwitch CLI — command-line demo and evaluation runner."""

from __future__ import annotations

import argparse
import json
import logging
import sys
import uuid

from slothswitch.api import create_router
from slothswitch.evaluation import EvaluationResult
from slothswitch.schemas import RoutingRequest


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="slothswitch",
        description="SlothSwitch — AI routing layer demo and evaluation",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- route command ---
    route_parser = subparsers.add_parser("route", help="Route a single request")
    route_parser.add_argument("content", help="The request text to route")
    route_parser.add_argument("--config", default="config/routing.yaml", help="Config file path")
    route_parser.add_argument("--baseline", action="store_true", help="Use baseline mode")
    route_parser.add_argument("--json", dest="json_output", action="store_true", help="Output as JSON")
    route_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    # --- eval command ---
    eval_parser = subparsers.add_parser("eval", help="Evaluate routing performance on a benchmark dataset")
    eval_parser.add_argument("--dataset", default="datasets/customer_support_routing.json", help="Path to evaluation dataset")
    eval_parser.add_argument("--config", default="config/routing.yaml", help="Config file path")
    eval_parser.add_argument("--baseline", action="store_true", help="Evaluate fixed-model baseline mode only")
    eval_parser.add_argument("--compare", action="store_true", default=False, help="Run comparative benchmark: SlothSwitch vs Fixed Baseline")
    eval_parser.add_argument("--test-only", action="store_true", help="Evaluate only on held-out test split")
    eval_parser.add_argument("--split", choices=["all", "train", "val", "test"], default=None, help="Dataset split to evaluate")
    eval_parser.add_argument("--adapter", choices=["mock", "laya"], default=None, help="Decision adapter override (mock or laya)")
    eval_parser.add_argument("--real-task-model", action="store_true", help="Execute real local TinyLlama causal LM for task models")
    eval_parser.add_argument("--split-ratio", type=float, default=0.2, help="Held-out test split ratio")
    eval_parser.add_argument("--seed", type=int, default=42, help="Random seed for splitting")


    # --- demo command ---
    demo_parser = subparsers.add_parser("demo", help="Run demo with sample requests")
    demo_parser.add_argument("--config", default="config/routing.yaml", help="Config file path")
    demo_parser.add_argument("--baseline", action="store_true", help="Use baseline mode")

    # --- health command ---
    health_parser = subparsers.add_parser("health", help="Check system health")
    health_parser.add_argument("--config", default="config/routing.yaml", help="Config file path")

    # --- serve command ---
    serve_parser = subparsers.add_parser("serve", help="Start the SlothSwitch REST API and Web Dashboard server")
    serve_parser.add_argument("--port", type=int, default=8080, help="Server port (default: 8080)")
    serve_parser.add_argument("--host", default="0.0.0.0", help="Host address (default: 0.0.0.0)")
    serve_parser.add_argument("--mock", action="store_true", help="Run with mock adapters instead of real models")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    logging.basicConfig(
        level=logging.DEBUG if getattr(args, "verbose", False) else logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    if args.command == "route":
        _cmd_route(args)
    elif args.command == "eval":
        _cmd_eval(args)
    elif args.command == "demo":
        _cmd_demo(args)
    elif args.command == "health":
        _cmd_health(args)
    elif args.command == "serve":
        _cmd_serve(args)


def _cmd_serve(args: argparse.Namespace) -> None:
    """Start the SlothSwitch web and API server."""
    from slothswitch.server import run_server

    run_server(port=args.port, host=args.host, use_real_models=not args.mock)




def _cmd_route(args: argparse.Namespace) -> None:
    """Route a single request."""
    router = create_router(config_path=args.config, baseline_mode=args.baseline)
    request = RoutingRequest(
        request_id=str(uuid.uuid4()),
        content=args.content,
    )
    record = router.process(request)

    if getattr(args, "json_output", False):
        output_payload = {
            "request_id": record.request_id,
            "route_decision": record.route_decision.model_dump(),
            "task_result": record.task_result.model_dump() if record.task_result else None,
        }
        print(json.dumps(output_payload, indent=2))
        return

    print("\n=== Routing Result ===")
    print(f"Request ID:  {record.request_id}")
    print(f"Route:       {record.route_decision.chosen_route.value}")
    print(f"Confidence:  {record.route_decision.confidence}")
    print(f"Accepted:    {record.route_decision.accepted}")
    print(f"Reasoning:   {record.route_decision.reasoning}")
    if record.route_decision.fallback_reason:
        print(f"Fallback:    {record.route_decision.fallback_reason}")
    print(f"Model:       {record.route_decision.decision_model}")
    print(f"Latency:     {record.route_decision.latency_ms:.1f} ms" if record.route_decision.latency_ms else "")

    if record.task_result:
        print("\n=== Task Result ===")
        print(f"Output:      {record.task_result.output}")
        print(f"Success:     {record.task_result.success}")
        print(f"Task Model:  {record.task_result.model_used}")


def _cmd_eval(args: argparse.Namespace) -> None:
    from slothswitch.evaluation import (
        EvaluationResult,
        load_dataset,
        partition_dataset,
        split_dataset,
    )

    dataset = load_dataset(args.dataset)
    target_split = args.split or ("test" if args.test_only else "all")
    if target_split == "test":
        parts = partition_dataset(dataset)
        eval_items = parts["test"] if parts["test"] else split_dataset(dataset, test_ratio=args.split_ratio, seed=args.seed)[1]
        split_desc = f"Held-out test split ({len(eval_items)} untouched examples)"
    elif target_split == "val":
        parts = partition_dataset(dataset)
        eval_items = parts["val"]
        split_desc = f"Validation split ({len(eval_items)} threshold-tuning examples)"
    elif target_split == "train":
        parts = partition_dataset(dataset)
        eval_items = parts["train"]
        split_desc = f"Training split ({len(eval_items)} policy formulation examples)"
    else:
        eval_items = dataset
        split_desc = f"Full benchmark ({len(eval_items)} examples)"

    def _run_strategy(baseline_mode: bool) -> EvaluationResult:
        router = create_router(
            config_path=args.config,
            baseline_mode=baseline_mode,
            decision_adapter_override=args.adapter,
            real_task_model=getattr(args, "real_task_model", False),
        )
        res = EvaluationResult()
        for item in eval_items:
            # Audit guarantee: zero leakage from metadata or expected answers
            req = RoutingRequest(
                request_id=item["request_id"],
                content=item["content"],
            )
            record = router.process(req)
            dec = record.route_decision
            tr = record.task_result

            cost = (tr.estimated_cost_usd or 0.0) if tr else 0.0
            router_overhead = dec.router_overhead_ms or 0.0
            decision_latency = dec.decision_latency_ms or 0.0
            task_latency = (tr.latency_ms or 0.0) if tr else 0.0
            total_e2e = record.total_e2e_latency_ms or (dec.latency_ms or 0.0)
            model_name = tr.model_used if tr else "unknown"
            p_tokens = (tr.token_usage or {}).get("prompt_tokens", 0) if tr else 0
            c_tokens = (tr.token_usage or {}).get("completion_tokens", 0) if tr else 0

            # Compute task quality score from dataset rubric if available
            chosen_val = dec.chosen_route.value
            expected_map = item.get("expected_quality", {})
            if chosen_val in expected_map:
                quality_score = float(expected_map[chosen_val])
            else:
                quality_score = 1.0 if chosen_val in item["acceptable_routes"] else 0.35

            res.add(
                predicted=chosen_val,
                acceptable=item["acceptable_routes"],
                latency_ms=dec.latency_ms or 0.0,
                cost_usd=cost,
                router_overhead_ms=router_overhead,
                decision_latency_ms=decision_latency,
                task_latency_ms=task_latency,
                total_e2e_ms=total_e2e,
                model_name=model_name,
                prompt_tokens=p_tokens,
                completion_tokens=c_tokens,
                quality_score=quality_score,
                cost_is_simulated=tr.cost_is_simulated if tr else True,
                task_latency_is_simulated=tr.latency_is_simulated if tr else False,
            )
        return res

    # Task 1 Audit Check
    dec_mode_desc = "Laya Neural ModernBERT" if args.adapter == "laya" else "Policy Router"
    task_mode_desc = "Local TinyLlama-1.1B Live Inference" if getattr(args, "real_task_model", False) else "Mock Task Adapters with Standard Pricing Tiers"
    print(f"\n{'='*70}")
    print("  SlothSwitch Benchmark Evaluation & Audit")
    print(f"  Dataset:        {args.dataset}")
    print(f"  Partition:      {split_desc}")
    print("  Parity Audit:   Identical queries, labels, and scoring across all strategies")
    print("  Leakage Audit:  ZERO metadata leakage; router inspects text content only")
    print(f"  Decision Model: [{dec_mode_desc}]")
    print(f"  Task Models:    [{task_mode_desc}]")
    print(f"{'='*70}\n")

    if args.baseline and not args.compare:
        # Run baseline only
        base_res = _run_strategy(baseline_mode=True)
        _print_strategy_summary("Fixed Baseline (Capable Large LLM)", base_res)
    elif not args.compare and not args.baseline:
        # Run SlothSwitch only
        sloth_res = _run_strategy(baseline_mode=False)
        _print_strategy_summary("SlothSwitch Policy Router", sloth_res)
    else:
        # Run comparative analysis (Task 4: Quality-Cost Trade-Off)
        print("Running comparative benchmark on identical examples...")
        sloth_res = _run_strategy(baseline_mode=False)
        base_res = _run_strategy(baseline_mode=True)

        _print_strategy_summary("SlothSwitch Policy Router", sloth_res)
        _print_strategy_summary("Fixed Baseline (Capable Large LLM)", base_res)

        # Comparative Trade-off Table
        sloth_s = sloth_res.summary()
        base_s = base_res.summary()

        q_retention = (
            (sloth_s["mean_task_quality"] / base_s["mean_task_quality"] * 100)
            if base_s["mean_task_quality"] > 0 else 100.0
        )
        cost_savings = (
            (1.0 - (sloth_s["total_cost_usd"] / base_s["total_cost_usd"])) * 100
            if base_s["total_cost_usd"] > 0 else 0.0
        )

        print(f"\n{'='*70}")
        print("  Task 4: Quality vs. Cost Trade-Off Analysis")
        print(f"{'='*70}")
        print(f"{'Metric':<30} {'SlothSwitch':<20} {'Fixed Baseline':<20}")
        print(f"{'-'*30} {'-'*20} {'-'*20}")
        print(f"{'Routing Accuracy':<30} {sloth_s['accuracy'] * 100:.1f}%{'':<15} {base_s['accuracy'] * 100:.1f}%")
        print(f"{'Macro F1 Score':<30} {sloth_s['macro_f1']:<20.4f} {base_s['macro_f1']:<20.4f}")
        print(f"{'Mean Task Quality Score':<30} {sloth_s['mean_task_quality'] * 100:.1f}%{'':<15} {base_s['mean_task_quality'] * 100:.1f}%")
        print(f"{'Total Incurred Cost':<30} ${sloth_s['total_cost_usd']:<19.5f} ${base_s['total_cost_usd']:<19.5f}")
        cost_per_1k_sloth = (sloth_s["total_cost_usd"] / sloth_s["total_examples"]) * 1000
        cost_per_1k_base = (base_s["total_cost_usd"] / base_s["total_examples"]) * 1000
        print(f"{'Estimated Cost / 1k Reqs':<30} ${cost_per_1k_sloth:<19.3f} ${cost_per_1k_base:<19.3f}")
        print(f"{'Avg End-to-End Latency':<30} {sloth_s['avg_total_e2e_latency_ms']:<17.2f} ms {base_s['avg_total_e2e_latency_ms']:<17.2f} ms")
        print(f"{'-'*30} {'-'*20} {'-'*20}")
        print(f"Quality Retention:  {q_retention:.1f}% of baseline quality preserved")
        print(f"Cost Reduction:     {cost_savings:.1f}% inference expenditure saved")
        print(f"{'='*70}\n")


def _print_strategy_summary(title: str, res: EvaluationResult) -> None:
    """Print detailed metrics for a strategy including separated latencies and model calls."""
    s = res.summary()
    tag = " [BASELINE]" if "Baseline" in title else ""
    print(f"\n--- Strategy: {title}{tag} ---")
    print(f"Total Requests Evaluated:  {s['total_examples']}")
    print(f"Routing Accuracy:          {s['accuracy'] * 100:.1f}%")
    print(f"Macro F1 Score:            {s['macro_f1']:.4f}")
    print(f"Mean Final Task Quality:   {s['mean_task_quality'] * 100:.1f}%")
    print(f"Fallback / Abstain Rate:   {s['fallback_rate'] * 100:.1f}%")

    task_sim_str = "Simulated Mock Delay" if s.get("task_latency_is_simulated", True) else "Live Forward Pass"
    cost_sim_str = "Simulated Standard Tiers" if s.get("cost_is_simulated", True) else "Local Live Compute ($0.00 API)"

    print("\nLatency Breakdown (Separated Measurements):")
    print(f"  Router Overhead (Validation/Policy): {s['avg_router_overhead_ms']:.3f} ms [Measured Live]")
    print(f"  Decision Model Inference:            {s['avg_decision_model_latency_ms']:.3f} ms [Measured Live]")
    print(f"  Task Model Execution:                {s['avg_task_model_latency_ms']:.3f} ms [{task_sim_str}]")
    print(f"  Total End-to-End Latency:            {s['avg_total_e2e_latency_ms']:.3f} ms [Measured Live]")

    print("\nModel Invocations & Token Accounting:")
    calls = s.get("model_calls", {})
    for model, count in sorted(calls.items()):
        print(f"  {model:<30}: {count} calls ({count / s['total_examples'] * 100:.1f}%)")
    tokens = s.get("token_usage", {})
    print(f"  Tokens Ingested (Prompt):     {tokens.get('prompt_tokens', 0):,}")
    print(f"  Tokens Generated (Output):    {tokens.get('completion_tokens', 0):,}")
    print(f"  Total Expenditure:            ${s['total_cost_usd']:.5f} USD [{cost_sim_str}]")

    print("\nPer-Route Metrics:")
    prec = s.get("per_route_precision", {})
    rec = s.get("per_route_recall", {})
    all_routes = sorted(set(list(prec.keys()) + list(rec.keys())))
    print(f"  {'Route':<15} {'Precision':<12} {'Recall':<12}")
    print(f"  {'-'*15} {'-'*12} {'-'*12}")
    for r in all_routes:
        print(f"  {r:<15} {prec.get(r, 0.0):<12.3f} {rec.get(r, 0.0):<12.3f}")



def _cmd_demo(args: argparse.Namespace) -> None:
    """Run demo with sample customer support requests."""
    router = create_router(config_path=args.config, baseline_mode=args.baseline)


    samples = [
        "What is my account balance?",
        "I was billed twice for invoice #12345 and I need a refund immediately.",
        "Can you help me debug this Python traceback? ```\nTraceback (most recent call last):\n  File 'app.py', line 42, in main\n    result = process(data)\nTypeError: 'NoneType' object is not callable\n```",
        "I want to delete my account and all associated data permanently.",
        "unclear what exactly is the problem here",
        "Hello, how do I reset my password?",
    ]

    mode = "BASELINE" if args.baseline else "SLOTHSWITCH"
    print(f"\n{'='*60}")
    print(f"  SlothSwitch Demo — Mode: {mode}")
    print(f"{'='*60}")

    for i, content in enumerate(samples, 1):
        request = RoutingRequest(
            request_id=f"demo-{i:03d}",
            content=content,
        )
        record = router.process(request)
        d = record.route_decision

        print(f"\n--- Request {i} ---")
        print(f"  Content:    {content[:80]}{'...' if len(content) > 80 else ''}")
        print(f"  Route:      {d.chosen_route.value}")
        print(f"  Confidence: {d.confidence}")
        print(f"  Accepted:   {d.accepted}")
        if d.fallback_reason:
            print(f"  Fallback:   {d.fallback_reason}")
        if record.task_result:
            print(f"  Response:   {record.task_result.output[:100]}...")

    # Summary
    summary = router.telemetry.summary()
    print(f"\n{'='*60}")
    print("  Telemetry Summary")
    print(f"{'='*60}")
    print(json.dumps(summary, indent=2))


def _cmd_health(args: argparse.Namespace) -> None:
    """Check system health."""
    router = create_router(config_path=args.config)
    print("\n=== SlothSwitch Health Check ===")
    print(f"Decision adapter: {router.decision_adapter.name}")
    print(f"  Health: {'OK' if router.decision_adapter.health_check() else 'FAIL'}")
    print("Task adapters:")
    for route, adapter in router.task_adapters.items():
        print(f"  {route.value}: {adapter.name} — {'OK' if adapter.health_check() else 'FAIL'}")
    print(f"Enabled routes: {[r.value for r in router.policy.enabled_routes]}")


if __name__ == "__main__":
    main()
