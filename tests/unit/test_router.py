"""Unit tests for the SlothSwitchRouter orchestration engine."""

import pytest

from slothswitch.adapters.decision import MockDecisionAdapter
from slothswitch.adapters.task_models import (
    MockLargeLLMAdapter,
    MockSmallLLMAdapter,
    StaticResponseAdapter,
)
from slothswitch.policy import RoutingPolicy
from slothswitch.router import SlothSwitchRouter
from slothswitch.schemas import RouteCategory, RoutingRequest
from slothswitch.telemetry import TelemetryRecorder


@pytest.fixture
def test_router():
    decision_adapter = MockDecisionAdapter()
    task_adapters = {
        RouteCategory.FAST_PATH: StaticResponseAdapter("Deterministic fast response"),
        RouteCategory.SMALL_LLM: MockSmallLLMAdapter(),
        RouteCategory.LARGE_LLM: MockLargeLLMAdapter(),
        RouteCategory.CLARIFY: StaticResponseAdapter("Please provide more details"),
        RouteCategory.FALLBACK: StaticResponseAdapter("Standard safe fallback response"),
        RouteCategory.HUMAN_REVIEW: StaticResponseAdapter("Sent to support specialist"),
    }
    policy = RoutingPolicy(acceptance_threshold=0.7)
    telemetry = TelemetryRecorder()
    return SlothSwitchRouter(
        decision_adapter=decision_adapter,
        task_adapters=task_adapters,
        policy=policy,
        telemetry=telemetry,
    )


def test_router_normal_flow(test_router):
    req = RoutingRequest(
        request_id="r10",
        content="I have a billing question regarding invoice 102.",
    )
    record = test_router.process(req)
    assert record.request_id == "r10"
    assert record.route_decision.accepted is True
    assert record.task_result is not None
    assert record.task_result.success is True
    assert record.route_decision.latency_ms is not None
    assert record.route_decision.latency_ms >= 0


def test_router_handles_empty_content_as_fallback(test_router):
    req = RoutingRequest(request_id="r_empty", content="   ")
    record = test_router.process(req)
    assert record.route_decision.chosen_route == RouteCategory.FALLBACK
    assert record.route_decision.accepted is False
    assert "validation failed" in record.route_decision.reasoning.lower()


def test_router_baseline_mode():
    decision_adapter = MockDecisionAdapter()
    task_adapters = {
        RouteCategory.LARGE_LLM: MockLargeLLMAdapter(),
    }
    policy = RoutingPolicy()
    telemetry = TelemetryRecorder()
    router = SlothSwitchRouter(
        decision_adapter=decision_adapter,
        task_adapters=task_adapters,
        policy=policy,
        telemetry=telemetry,
        baseline_mode=True,
        baseline_route=RouteCategory.LARGE_LLM,
    )
    req = RoutingRequest(request_id="r_base", content="Simple hello")
    record = router.process(req)
    assert record.route_decision.chosen_route == RouteCategory.LARGE_LLM
    assert record.route_decision.decision_model == "baseline"
    assert record.task_result.model_used == "mock-large"


def test_router_decision_adapter_failure_fallback(monkeypatch, test_router):
    # Simulate decision adapter raising an unexpected exception
    def broken_predict(*args, **kwargs):
        raise RuntimeError("Service connection failed")

    monkeypatch.setattr(test_router.decision_adapter, "predict_route", broken_predict)

    req = RoutingRequest(request_id="r_fail", content="Valid content but broken adapter")
    record = test_router.process(req)
    assert record.route_decision.chosen_route == RouteCategory.FALLBACK
    assert "error" in record.route_decision.reasoning.lower()
