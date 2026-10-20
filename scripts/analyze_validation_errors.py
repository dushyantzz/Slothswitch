"""Analyze routing errors on the validation partition (42 examples).

Used strictly for threshold tuning, error diagnosis, and policy improvement
without touching the 63-example held-out test set.
"""

from __future__ import annotations

import json
from pathlib import Path

from slothswitch.api import create_router
from slothswitch.schemas import RoutingRequest


def main():
    dataset_path = Path("datasets/customer_support_routing.json")
    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Filter strictly for validation partition
    val_items = [x for x in data if x.get("split") == "val"]
    print(f"Total Validation Items for Policy Tuning: {len(val_items)}")

    router = create_router()

    errors = []
    underprovisioned = []  # Sent to an inadequate/cheap processing path
    overprovisioned = []   # Sent to an unnecessarily expensive path

    for item in val_items:
        req = RoutingRequest(request_id=item["request_id"], content=item["content"])
        rec = router.process(req)
        chosen = rec.route_decision.chosen_route.value
        acceptable = item["acceptable_routes"]
        quality_map = item.get("expected_quality", {})
        chosen_quality = quality_map.get(chosen, 0.40)
        baseline_quality = quality_map.get("LARGE_LLM", 0.90)

        is_error = chosen not in acceptable
        if is_error:
            error_entry = {
                "id": item["request_id"],
                "content": item["content"],
                "task_type": item["task_type"],
                "category": item["category"],
                "chosen": chosen,
                "acceptable": acceptable,
                "chosen_quality": chosen_quality,
                "baseline_quality": baseline_quality,
                "reasoning": rec.route_decision.reasoning,
                "fallback_reason": rec.route_decision.fallback_reason,
            }
            errors.append(error_entry)

            # Check if underprovisioned: acceptable required LARGE_LLM, but system picked SMALL_LLM, FAST_PATH, or CLARIFY
            if "LARGE_LLM" in acceptable and chosen in ("SMALL_LLM", "FAST_PATH", "CLARIFY"):
                underprovisioned.append(error_entry)
            elif "CLARIFY" in acceptable and chosen in ("SMALL_LLM", "FAST_PATH"):
                underprovisioned.append(error_entry)

    print(f"\n--- Validation Error Summary ---")
    print(f"Total Errors: {len(errors)} / {len(val_items)} ({len(errors)/len(val_items)*100:.1f}%)")
    print(f"Underprovisioned (Inadequate processing path): {len(underprovisioned)}")
    print(f"Other Errors: {len(errors) - len(underprovisioned)}")

    print("\n--- Detailed Underprovisioned Inadequate Path Cases ---")
    for u in underprovisioned:
        print(f"\n[ID: {u['id']}] Category: {u['category']} | Task: {u['task_type']}")
        print(f"  Content: {u['content'][:120]}...")
        print(f"  Chosen: {u['chosen']} (Quality: {u['chosen_quality']})")
        print(f"  Acceptable: {u['acceptable']} (Large LLM Quality: {u['baseline_quality']})")
        print(f"  Decision Reasoning: {u['reasoning']}")

    print("\n--- Other Misclassifications ---")
    for o in [e for e in errors if e not in underprovisioned]:
        print(f"\n[ID: {o['id']}] Category: {o['category']} | Task: {o['task_type']}")
        print(f"  Content: {o['content'][:120]}...")
        print(f"  Chosen: {o['chosen']} vs Acceptable: {o['acceptable']}")
        print(f"  Reasoning: {o['reasoning']}")


if __name__ == "__main__":
    main()
