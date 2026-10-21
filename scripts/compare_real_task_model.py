"""Compare SlothSwitch vs Fixed-Model Baseline using a REAL Task Model (TinyLlama-1.1B-Chat).

This script:
1. Takes representative evaluation requests (classification, extraction, generation, reasoning, clarification).
2. Runs SlothSwitch (routing + real model execution where appropriate).
3. Runs the Fixed Baseline (100% real model execution on every request).
4. Measures and prints REAL forward-pass latency, REAL prompt/completion tokens, and outputs.
"""

from __future__ import annotations

import time

from slothswitch.adapters.task_models import LocalTransformersTaskModelAdapter
from slothswitch.api import create_router
from slothswitch.schemas import RouteCategory, RoutingRequest


def main():
    print("=" * 70)
    print("  Comparing SlothSwitch vs Fixed Baseline with REAL Task Model")
    print("  Model: TinyLlama/TinyLlama-1.1B-Chat-v1.0 (Live Forward Pass)")
    print("=" * 70)

    # Preload the real model once so tokenizer/weights are in memory
    real_model = LocalTransformersTaskModelAdapter(
        model_name="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        max_new_tokens=30,
        preload=True,
    )

    test_queries = [
        # 1. Simple fast path (FAQ / Lookup)
        ("cs-fast", "What are your standard support operating hours?"),
        # 2. Ambiguous query (Needs Clarification)
        ("cs-clarify", "Can you reissue the invoice from yesterday?"),
        # 3. Routine support (Small LLM)
        ("cs-small", "Can you explain the difference between Pro and Enterprise subscription tiers?"),
        # 4. Complex reasoning / code debugging (Large LLM)
        ("cs-large", "Can you help me fix this Python bug? ```def fetch(): return None\nprint(fetch().val)```"),
        # 5. Security / compliance (Human Review)
        ("cs-security", "I discovered a remote code execution vulnerability in your OAuth callback endpoint."),
    ]

    # --- Strategy A: SlothSwitch Intelligent Router ---
    print("\n--- Strategy A: SlothSwitch Intelligent Routing ---")
    sloth_router = create_router()
    # Replace generation task models with our real TinyLlama instance
    sloth_router.task_adapters[RouteCategory.SMALL_LLM] = real_model
    sloth_router.task_adapters[RouteCategory.LARGE_LLM] = real_model

    sloth_total_ms = 0.0
    sloth_total_tokens = 0
    sloth_real_model_calls = 0

    for req_id, text in test_queries:
        req = RoutingRequest(request_id=req_id, content=text)
        rec = sloth_router.process(req)
        dec = rec.route_decision
        tr = rec.task_result

        lat = tr.latency_ms if tr else 0.0
        toks = (tr.token_usage or {}).get("total_tokens", 0) if tr else 0
        is_real = not (tr.latency_is_simulated if tr else True)

        sloth_total_ms += rec.total_e2e_latency_ms or 0.0
        sloth_total_tokens += toks
        if is_real and dec.chosen_route in (RouteCategory.SMALL_LLM, RouteCategory.LARGE_LLM):
            sloth_real_model_calls += 1

        print(f"\n[Query: '{text[:50]}...']")
        print(f"  Chosen Route:   {dec.chosen_route.value} (Confidence: {dec.confidence})")
        print(f"  Router Overhead: {dec.router_overhead_ms:.2f} ms")
        print(f"  Task Execution: {lat:.2f} ms [{'REAL FORWARD PASS' if is_real else 'DETERMINISTIC ZERO-COST'}]")
        print(f"  Tokens Used:    {toks} total")
        print(f"  Output Preview: {tr.output[:90] if tr else 'None'}...")

    # --- Strategy B: Fixed Capable-Model Baseline ---
    print("\n" + "=" * 70)
    print("--- Strategy B: Fixed Capable-Model Baseline (All -> Real TinyLlama) ---")
    base_total_ms = 0.0
    base_total_tokens = 0

    for req_id, text in test_queries:
        req = RoutingRequest(request_id=req_id, content=text)
        t0 = time.perf_counter()
        tr = real_model.execute(req, RouteCategory.LARGE_LLM)
        elapsed = (time.perf_counter() - t0) * 1000

        toks = (tr.token_usage or {}).get("total_tokens", 0)
        base_total_ms += elapsed
        base_total_tokens += toks

        print(f"\n[Query: '{text[:50]}...']")
        print("  Route:          LARGE_LLM (Fixed)")
        print(f"  Task Execution: {tr.latency_ms:.2f} ms [REAL FORWARD PASS]")
        print(f"  Tokens Used:    {toks} total")
        print(f"  Output Preview: {tr.output[:90]}...")

    # --- Comparative Summary ---
    print("\n" + "=" * 70)
    print("  Empirical Real Inference Comparison")
    print("=" * 70)
    print(f"{'Metric':<30} {'SlothSwitch':<20} {'Fixed Baseline':<20}")
    print(f"{'-'*30} {'-'*20} {'-'*20}")
    print(f"{'Real Model Invocations':<30} {sloth_real_model_calls} of {len(test_queries)}{'':<13} {len(test_queries)} of {len(test_queries)}")
    print(f"{'Total Tokens Consumed':<30} {sloth_total_tokens:<20} {base_total_tokens:<20}")
    print(f"{'Total Latency (5 Reqs)':<30} {sloth_total_ms:.1f} ms{'':<12} {base_total_ms:.1f} ms")
    lat_reduction = (1.0 - (sloth_total_ms / base_total_ms)) * 100 if base_total_ms > 0 else 0.0
    tok_reduction = (1.0 - (sloth_total_tokens / base_total_tokens)) * 100 if base_total_tokens > 0 else 0.0
    print(f"{'-'*30} {'-'*20} {'-'*20}")
    print(f"Real Token Savings:   {tok_reduction:.1f}% reduction in tokens generated/processed")
    print(f"Real Latency Savings: {lat_reduction:.1f}% reduction in total wall-clock execution time")
    print("=" * 70)


if __name__ == "__main__":
    main()
