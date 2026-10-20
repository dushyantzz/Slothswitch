"""Integration tests for end-to-end routing using the SlothSwitch API and config."""

from pathlib import Path

from slothswitch.api import create_router
from slothswitch.evaluation import EvaluationResult, load_dataset
from slothswitch.schemas import RouteCategory, RoutingRequest


def test_create_router_from_yaml_config(tmp_path: Path):
    # Use default routing config
    router = create_router("config/routing.yaml")
    assert router is not None
    assert router.policy is not None
    assert len(router.task_adapters) > 0


def test_end_to_end_routing_pipeline():
    router = create_router("config/routing.yaml")

    # 1. Test standard billing request
    req1 = RoutingRequest(
        request_id="e2e-01",
        content="Where can I see my previous monthly invoices?",
    )
    rec1 = router.process(req1)
    assert rec1.request_id == "e2e-01"
    assert rec1.route_decision.accepted is True
    assert rec1.task_result is not None
    assert rec1.task_result.success is True

    # 2. Test high risk / legal request
    req2 = RoutingRequest(
        request_id="e2e-02",
        content="Our legal team is demanding a signed DPA under GDPR compliance.",
        metadata={"category": "legal"},
    )
    rec2 = router.process(req2)
    assert rec2.route_decision.chosen_route in (RouteCategory.HUMAN_REVIEW, RouteCategory.LARGE_LLM)

    # 3. Test baseline mode
    baseline_router = create_router("config/routing.yaml", baseline_mode=True)
    rec3 = baseline_router.process(req1)
    assert rec3.route_decision.chosen_route == RouteCategory.LARGE_LLM
    assert rec3.route_decision.decision_model == "baseline"


def test_evaluate_dataset_end_to_end():
    dataset = load_dataset("datasets/customer_support_routing.json")
    router = create_router("config/routing.yaml")
    eval_result = EvaluationResult()

    for item in dataset:
        req = RoutingRequest(
            request_id=item["request_id"],
            content=item["content"],
        )
        record = router.process(req)
        cost = record.task_result.estimated_cost_usd if record.task_result else 0.0
        latency = record.route_decision.latency_ms or 0.0

        eval_result.add(
            predicted=record.route_decision.chosen_route.value,
            acceptable=item["acceptable_routes"],
            latency_ms=latency,
            cost_usd=cost,
        )

    summary = eval_result.summary()
    assert summary["total_examples"] == len(dataset)
    assert summary["accuracy"] > 0.0
    assert "macro_f1" in summary
