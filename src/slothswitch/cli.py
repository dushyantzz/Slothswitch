"""SlothSwitch CLI — command-line demo and evaluation runner."""

from __future__ import annotations

import argparse
import json
import logging
import sys
import uuid

from slothswitch.api import create_router
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
    eval_parser.add_argument("--baseline", action="store_true", help="Evaluate fixed-model baseline mode")
    eval_parser.add_argument("--test-only", action="store_true", help="Evaluate only on held-out test split")
    eval_parser.add_argument("--split-ratio", type=float, default=0.2, help="Held-out test split ratio")
    eval_parser.add_argument("--seed", type=int, default=42, help="Random seed for splitting")

    # --- demo command ---
    demo_parser = subparsers.add_parser("demo", help="Run demo with sample requests")
    demo_parser.add_argument("--config", default="config/routing.yaml", help="Config file path")
    demo_parser.add_argument("--baseline", action="store_true", help="Use baseline mode")

    # --- health command ---
    health_parser = subparsers.add_parser("health", help="Check system health")
    health_parser.add_argument("--config", default="config/routing.yaml", help="Config file path")

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
    """Evaluate routing accuracy and cost against a benchmark dataset."""
    from slothswitch.evaluation import EvaluationResult, load_dataset, split_dataset

    dataset = load_dataset(args.dataset)
    if args.test_only:
        _, test_set = split_dataset(dataset, test_ratio=args.split_ratio, seed=args.seed)
        eval_items = test_set
        split_desc = f"Held-out test split ({len(eval_items)} examples)"
    else:
        eval_items = dataset
        split_desc = f"Full dataset ({len(eval_items)} examples)"

    mode = "BASELINE (capable-model)" if args.baseline else "SLOTHSWITCH (policy-routed)"
    router = create_router(config_path=args.config, baseline_mode=args.baseline)
    eval_result = EvaluationResult()

    print(f"\n{'='*65}")
    print("  SlothSwitch Benchmark Evaluation")
    print(f"  Mode:     {mode}")
    print(f"  Dataset:  {args.dataset} [{split_desc}]")
    print(f"{'='*65}\n")

    for item in eval_items:
        req = RoutingRequest(
            request_id=item["request_id"],
            content=item["content"],
        )
        record = router.process(req)
        cost = (record.task_result.estimated_cost_usd or 0.0) if record.task_result else 0.0
        latency = record.route_decision.latency_ms or 0.0

        eval_result.add(
            predicted=record.route_decision.chosen_route.value,
            acceptable=item["acceptable_routes"],
            latency_ms=latency,
            cost_usd=cost,
        )

    summary = eval_result.summary()
    print("--- Aggregate Results ---")
    print(f"Total Requests:     {summary['total_examples']}")
    print(f"Routing Accuracy:   {summary['accuracy'] * 100:.1f}%")
    print(f"Macro F1 Score:     {summary['macro_f1']:.4f}")
    print(f"Fallback Rate:      {summary['fallback_rate'] * 100:.1f}%")

    avg_latency = sum(eval_result.latencies_ms) / len(eval_result.latencies_ms) if eval_result.latencies_ms else 0.0
    total_cost = sum(eval_result.costs_usd)
    print(f"Avg Latency:        {avg_latency:.2f} ms")
    print(f"Total Sim. Cost:    ${total_cost:.5f} USD")

    print("\n--- Per-Route Metrics ---")
    prec = summary.get("per_route_precision", {})
    rec = summary.get("per_route_recall", {})
    all_routes = sorted(set(list(prec.keys()) + list(rec.keys())))
    print(f"{'Route':<15} {'Precision':<12} {'Recall':<12}")
    print(f"{'-'*15} {'-'*12} {'-'*12}")
    for r in all_routes:
        print(f"{r:<15} {prec.get(r, 0.0):<12.3f} {rec.get(r, 0.0):<12.3f}")
    print(f"{'='*65}\n")


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
