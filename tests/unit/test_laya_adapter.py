"""Unit tests for LayaDecisionAdapter using a simulated Laya Router."""

from unittest.mock import MagicMock

import pytest

from slothswitch.adapters.decision.laya_adapter import LayaDecisionAdapter
from slothswitch.preprocessing import RoutingFeatures
from slothswitch.schemas import RouteCategory, RoutingRequest


@pytest.fixture
def mock_laya_router(monkeypatch):
    """Mock the laya.Router class to avoid downloading remote weights."""
    mock_router_instance = MagicMock()
    mock_router_class = MagicMock(return_value=mock_router_instance)

    monkeypatch.setattr("laya.Router", mock_router_class)
    return mock_router_instance


def test_laya_adapter_successful_prediction(mock_laya_router):
    # Configure mock prediction return value
    mock_laya_router.predict.return_value = {
        "answers": {
            "route": {
                "choice": "FAST_PATH",
                "confidence": 0.94,
            }
        },
        "routing": {"model": "convaiinnovations/laya"},
    }

    adapter = LayaDecisionAdapter(checkpoint="convaiinnovations/laya")
    req = RoutingRequest(request_id="req-laya-1", content="Where is my bill?")
    features = RoutingFeatures(request_id="req-laya-1", redacted_summary="Where is my bill?")

    decision = adapter.predict_route(
        req,
        features,
        available_routes=[RouteCategory.FAST_PATH, RouteCategory.SMALL_LLM],
    )

    assert decision.request_id == "req-laya-1"
    assert decision.chosen_route == RouteCategory.FAST_PATH
    assert decision.confidence == 0.94
    assert decision.decision_model == "laya:convaiinnovations/laya"
    assert decision.latency_ms is not None


def test_laya_adapter_invalid_label_fallback(mock_laya_router):
    # Return an unrecognized label
    mock_laya_router.predict.return_value = {
        "answers": {
            "route": {
                "choice": "UNRECOGNIZED_ROUTE",
                "confidence": 0.80,
            }
        }
    }

    adapter = LayaDecisionAdapter()
    req = RoutingRequest(request_id="req-laya-2", content="Uncertain request")
    features = RoutingFeatures(request_id="req-laya-2")

    decision = adapter.predict_route(
        req,
        features,
        available_routes=[RouteCategory.FAST_PATH, RouteCategory.SMALL_LLM],
    )

    # Should safely convert to FALLBACK with 0.0 confidence
    assert decision.chosen_route == RouteCategory.FALLBACK
    assert decision.confidence == 0.0


def test_laya_adapter_exception_handling(mock_laya_router):
    # Simulate inference crash / CUDA OOM / network timeout
    mock_laya_router.predict.side_effect = RuntimeError("GPU memory exhausted")

    adapter = LayaDecisionAdapter()
    req = RoutingRequest(request_id="req-laya-3", content="Heavy query")
    features = RoutingFeatures(request_id="req-laya-3")

    decision = adapter.predict_route(
        req,
        features,
        available_routes=[RouteCategory.FAST_PATH, RouteCategory.SMALL_LLM],
    )

    assert decision.chosen_route == RouteCategory.FALLBACK
    assert decision.confidence == 0.0
    assert "error" in decision.reasoning.lower()


def test_laya_adapter_no_available_routes(mock_laya_router):
    adapter = LayaDecisionAdapter()
    req = RoutingRequest(request_id="req-laya-4", content="Any query")
    features = RoutingFeatures(request_id="req-laya-4")

    # Pass empty available routes
    decision = adapter.predict_route(req, features, available_routes=[])
    assert decision.chosen_route == RouteCategory.FALLBACK
    assert decision.confidence == 0.0


def test_laya_adapter_predict_workflow_action(mock_laya_router):
    from slothswitch.schemas import DecisionOutcome
    from slothswitch.workflows.github_pr_management import create_github_workflow

    mock_laya_router.predict.return_value = {
        "answers": {
            "action": {
                "choice": "count_pull_requests",
                "answer_confidence": 0.94,
                "probabilities": {"count_pull_requests": 0.94, "list_open_pull_requests": 0.06},
            }
        }
    }

    adapter = LayaDecisionAdapter()
    wf = create_github_workflow()

    decision = adapter.predict_action(
        request_content="How many PRs are currently open in pallets/flask?",
        workflow=wf,
    )

    assert decision.action_id == "count_pull_requests"
    assert decision.outcome == DecisionOutcome.EXECUTE_TOOL
    assert decision.confidence == 0.94
    assert decision.decision_latency_ms is not None
