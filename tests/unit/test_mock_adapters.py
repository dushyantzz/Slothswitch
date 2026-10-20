"""Unit tests for mock adapters (decision and task models)."""


from slothswitch.adapters.decision import MockDecisionAdapter
from slothswitch.adapters.task_models import (
    MockLargeLLMAdapter,
    MockSmallLLMAdapter,
    StaticResponseAdapter,
)
from slothswitch.preprocessing import RoutingFeatures
from slothswitch.schemas import RouteCategory, RoutingRequest


def test_mock_decision_adapter_rule_matching():
    adapter = MockDecisionAdapter()
    req = RoutingRequest(request_id="r1", content="My invoice is wrong, please refund")
    features = RoutingFeatures(
        request_id="r1",
        category_hints=["billing"],
        char_count=len(req.content),
    )
    decision = adapter.predict_route(
        req, features, available_routes=list(RouteCategory)
    )
    assert decision.request_id == "r1"
    assert decision.chosen_route == RouteCategory.FAST_PATH
    assert decision.confidence is not None
    assert decision.confidence > 0.8


def test_mock_decision_adapter_code_block_escalation():
    adapter = MockDecisionAdapter()
    req = RoutingRequest(request_id="r2", content="Bug here: ```def foo(): pass```")
    features = RoutingFeatures(
        request_id="r2",
        has_code_block=True,
        char_count=len(req.content),
    )
    decision = adapter.predict_route(
        req, features, available_routes=list(RouteCategory)
    )
    assert decision.chosen_route == RouteCategory.LARGE_LLM


def test_mock_decision_adapter_empty_query_clarify():
    adapter = MockDecisionAdapter()
    req = RoutingRequest(request_id="r3", content="Can you clarify what more info is needed?")
    features = RoutingFeatures(request_id="r3", word_count=8)
    decision = adapter.predict_route(
        req, features, available_routes=list(RouteCategory)
    )
    assert decision.chosen_route == RouteCategory.CLARIFY



def test_mock_decision_adapter_health_check():
    adapter = MockDecisionAdapter()
    assert adapter.health_check() is True


def test_mock_task_adapters():
    req = RoutingRequest(request_id="r_task", content="How do I cancel my plan?")

    # Small LLM
    small_adapter = MockSmallLLMAdapter()
    assert small_adapter.health_check() is True
    res_small = small_adapter.execute(req, RouteCategory.SMALL_LLM)
    assert res_small.success is True
    assert res_small.model_used == "mock-small"
    assert res_small.estimated_cost_usd is not None

    # Large LLM
    large_adapter = MockLargeLLMAdapter()
    assert large_adapter.health_check() is True
    res_large = large_adapter.execute(req, RouteCategory.LARGE_LLM)
    assert res_large.success is True
    assert res_large.model_used == "mock-large"
    assert res_large.estimated_cost_usd > res_small.estimated_cost_usd

    # Static response adapter
    static_adapter = StaticResponseAdapter("Your request is queued for human review.")
    assert static_adapter.health_check() is True
    res_static = static_adapter.execute(req, RouteCategory.HUMAN_REVIEW)
    assert res_static.success is True
    assert "human review" in res_static.output
