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
    route_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

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
        print(f"\n=== Task Result ===")
        print(f"Output:      {record.task_result.output}")
        print(f"Success:     {record.task_result.success}")
        print(f"Task Model:  {record.task_result.model_used}")


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
    print(f"Task adapters:")
    for route, adapter in router.task_adapters.items():
        print(f"  {route.value}: {adapter.name} — {'OK' if adapter.health_check() else 'FAIL'}")
    print(f"Enabled routes: {[r.value for r in router.policy.enabled_routes]}")


if __name__ == "__main__":
    main()
