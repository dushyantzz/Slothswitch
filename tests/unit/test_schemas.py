"""Unit tests for SlothSwitch data schemas."""

import pytest
from pydantic import ValidationError

from slothswitch.schemas import (
    RouteCategory,
    RouteDecision,
    RoutingRecord,
    RoutingRequest,
    TaskResult,
)


def test_route_categories_contain_all_expected_enums():
    expected = {"FAST_PATH", "SMALL_LLM", "LARGE_LLM", "CLARIFY", "FALLBACK", "HUMAN_REVIEW"}
    actual = {r.value for r in RouteCategory}
    assert actual == expected


def test_routing_request_valid():
    req = RoutingRequest(
        request_id="req-123",
        content="I need help with my monthly invoice.",
        content_type="text/plain",
        metadata={"user_tier": "enterprise"},
    )
    assert req.request_id == "req-123"
    assert "invoice" in req.content
    assert req.allowed_routes is None
    assert req.max_cost_tier is None
    assert isinstance(req.timestamp, float)


def test_routing_request_missing_required_fields():
    with pytest.raises(ValidationError):
        RoutingRequest(content="Missing request ID")  # type: ignore


def test_routing_request_with_constraints():
    req = RoutingRequest(
        request_id="req-constrained",
        content="Simple query",
        allowed_routes=[RouteCategory.FAST_PATH, RouteCategory.SMALL_LLM],
        max_cost_tier=1,
    )
    assert req.allowed_routes == [RouteCategory.FAST_PATH, RouteCategory.SMALL_LLM]
    assert req.max_cost_tier == 1


def test_route_decision_defaults_and_validation():
    decision = RouteDecision(
        request_id="req-1",
        chosen_route=RouteCategory.FAST_PATH,
        confidence=0.95,
        reasoning="Exact rule match",
    )
    assert decision.accepted is True
    assert decision.fallback_reason is None
    assert decision.confidence == 0.95
    assert decision.chosen_route == RouteCategory.FAST_PATH


def test_route_decision_confidence_bounds():
    with pytest.raises(ValidationError):
        RouteDecision(
            request_id="req-1",
            chosen_route=RouteCategory.FAST_PATH,
            confidence=1.5,  # Out of [0, 1] bounds
        )
    with pytest.raises(ValidationError):
        RouteDecision(
            request_id="req-1",
            chosen_route=RouteCategory.FAST_PATH,
            confidence=-0.1,  # Out of [0, 1] bounds
        )


def test_task_result_fields():
    result = TaskResult(
        request_id="req-1",
        route_used=RouteCategory.SMALL_LLM,
        output="Your account balance is $45.00",
        success=True,
        model_used="mock-small",
        latency_ms=12.5,
        token_usage={"prompt_tokens": 15, "completion_tokens": 10, "total_tokens": 25},
        estimated_cost_usd=0.00005,
    )
    assert result.success is True
    assert result.estimated_cost_usd == 0.00005
    assert result.token_usage["total_tokens"] == 25


def test_routing_record_bundling():
    req_id = "req-bundle"
    dec = RouteDecision(
        request_id=req_id,
        chosen_route=RouteCategory.FAST_PATH,
        confidence=0.99,
    )
    res = TaskResult(
        request_id=req_id,
        route_used=RouteCategory.FAST_PATH,
        output="Deterministic answer",
    )
    record = RoutingRecord(
        request_id=req_id,
        route_decision=dec,
        task_result=res,
        config_version="v1.0",
    )
    assert record.request_id == req_id
    assert record.route_decision.chosen_route == RouteCategory.FAST_PATH
    assert record.task_result.output == "Deterministic answer"
