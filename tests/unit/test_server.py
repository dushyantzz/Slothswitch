"""Unit and integration tests for SlothSwitch REST API server."""

import pytest

from slothswitch.server import SlothSwitchState


@pytest.fixture
def mock_server_state() -> SlothSwitchState:
    """Fixture providing an isolated server state with mock adapters."""
    return SlothSwitchState(use_real_models=False)


def test_server_state_initialization(mock_server_state: SlothSwitchState) -> None:
    """Server state initializes workflows, policies, and seed traces."""
    assert "github_pr_management" in mock_server_state.registry.list_workflows()
    assert "system_ops" in mock_server_state.registry.list_workflows()
    assert len(mock_server_state.traces) > 0
    stats = mock_server_state.get_stats()
    assert stats["total_requests"] >= len(mock_server_state.traces)
    assert stats["avoided_generative_pct"] > 50.0


def test_server_stats_computation(mock_server_state: SlothSwitchState) -> None:
    """Stats calculation correctly accounts for outcomes."""
    mock_server_state.traces = [
        {"policy_outcome": "EXECUTE_TOOL"},
        {"policy_outcome": "EXECUTE_TOOL"},
        {"policy_outcome": "USE_GENERATIVE_MODEL"},
        {"policy_outcome": "ABSTAIN"},
        {"policy_outcome": "HUMAN_REVIEW"},
    ]
    stats = mock_server_state.get_stats()
    assert stats["total_requests"] == 5
    assert stats["direct_tool_executions"] == 2
    assert stats["generative_calls"] == 1
    assert stats["avoided_generative_calls"] == 4
    assert stats["avoided_generative_pct"] == 80.0
    assert stats["policy_abstentions"] == 1
    assert stats["human_approvals_required"] == 1


def test_server_trace_bounding(mock_server_state: SlothSwitchState) -> None:
    """Trace buffer caps at 100 entries to prevent memory unbounded growth."""
    for i in range(120):
        mock_server_state.record_trace({"trace_id": f"tr-{i}", "policy_outcome": "EXECUTE_TOOL"})
    assert len(mock_server_state.traces) == 100
    assert mock_server_state.traces[0]["trace_id"] == "tr-119"


def test_interactive_scenarios_structure() -> None:
    """Interactive scenarios return 5 representative tasks with complete comparisons."""
    from slothswitch.server import get_interactive_scenarios

    scenarios = get_interactive_scenarios()
    assert len(scenarios) == 5
    ids = [s["id"] for s in scenarios]
    assert "scenario-1" in ids
    assert "scenario-5" in ids
    for s in scenarios:
        assert "always_generative" in s
        assert "deterministic_rules" in s
        assert "slothswitch" in s
        assert s["slothswitch"]["policy_outcome"] in ("ALLOW", "USE_GENERATIVE_MODEL", "ABSTAIN", "CLARIFY")


def test_benchmark_csv_generation(tmp_path: pytest.TempPathFactory) -> None:
    """Benchmark CSV generator outputs valid CSV text with required headers."""
    import json
    from pathlib import Path

    from slothswitch.server import generate_benchmark_csv

    mock_audit = {
        "per_sample_audit_records": {
            "baseline_c": [
                {
                    "request_id": "test-1",
                    "content": "Count open PRs",
                    "expected_action": "count_pull_requests",
                    "predicted_action": "count_pull_requests",
                    "action_match": True,
                    "expected_outcome": "EXECUTE_TOOL",
                    "predicted_outcome": "EXECUTE_TOOL",
                    "outcome_match": True,
                    "task_success": True,
                    "latencies_ms": {"total_e2e": 2800.0, "decision": 1400.0},
                    "tokens": {"total_tokens": 0},
                    "model_used": "laya",
                }
            ]
        }
    }
    test_file = Path(str(tmp_path)) / "test_audit.json"
    with open(test_file, "w", encoding="utf-8") as f:
        json.dump(mock_audit, f)

    csv_text = generate_benchmark_csv(test_file)
    assert "baseline,request_id,content" in csv_text
    assert "baseline_c,test-1,Count open PRs" in csv_text

