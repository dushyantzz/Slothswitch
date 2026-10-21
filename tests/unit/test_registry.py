"""Unit tests for WorkflowDefinition, ActionDefinition, and WorkflowRegistry."""

import pytest

from slothswitch.registry import (
    WorkflowRegistry,
    get_default_registry,
    get_workflow,
    register_workflow,
)
from slothswitch.schemas import (
    ActionDecision,
    DecisionOutcome,
    ExecutionState,
    WorkflowExecutionResult,
)
from slothswitch.workflows.base import ActionDefinition, WorkflowDefinition
from slothswitch.workflows.system_ops import (
    create_system_ops_workflow,
    execute_clean_temp_cache,
    execute_get_disk_usage,
    execute_get_system_health,
)


def test_action_definition_parameter_validation() -> None:
    """ActionDefinition correctly validates presence of required parameters."""
    action = ActionDefinition(
        action_id="test_action",
        description="Test action with required param",
        parameters_schema={
            "properties": {
                "repo": {"type": "string"},
                "limit": {"type": "integer"},
            },
            "required": ["repo"],
        },
    )

    # Missing required parameter 'repo'
    valid, err = action.validate_parameters({"limit": 10})
    assert not valid
    assert "Missing required parameter 'repo'" in (err or "")

    # Providing required parameter 'repo'
    valid, err = action.validate_parameters({"repo": "octocat/Hello-World", "limit": 10})
    assert valid
    assert err is None


def test_workflow_definition_filtering() -> None:
    """WorkflowDefinition correctly filters read-only, mutating, and generative actions."""
    wf = WorkflowDefinition(
        name="test_wf",
        version="1.0.0",
        description="Workflow test",
        actions=[
            ActionDefinition(
                action_id="read_action",
                description="Read something",
                is_mutating=False,
                allows_generative=False,
                is_direct_execution=True,
            ),
            ActionDefinition(
                action_id="write_action",
                description="Write something",
                is_mutating=True,
                requires_approval=True,
                allows_generative=False,
                is_direct_execution=True,
            ),
            ActionDefinition(
                action_id="gen_action",
                description="Generate something",
                is_mutating=False,
                allows_generative=True,
                is_direct_execution=False,
            ),
        ],
    )

    assert wf.list_actions() == ["read_action", "write_action", "gen_action"]
    assert [a.action_id for a in wf.get_read_only_actions()] == ["read_action", "gen_action"]
    assert [a.action_id for a in wf.get_mutating_actions()] == ["write_action"]
    assert [a.action_id for a in wf.get_generative_actions()] == ["gen_action"]
    assert [a.action_id for a in wf.get_direct_execution_actions()] == ["read_action", "write_action"]
    assert wf.get_action("read_action") is not None
    assert wf.get_action("nonexistent") is None


def test_registry_registration_and_duplicate_handling() -> None:
    """Registry prevents empty names, duplicate actions, and accidental overwrites."""
    reg = WorkflowRegistry()

    # Reject empty workflow name
    with pytest.raises(ValueError, match="cannot be empty"):
        reg.register(WorkflowDefinition(name="", actions=[]))

    # Reject duplicate action IDs within workflow
    with pytest.raises(ValueError, match="Duplicate action_id 'dup'"):
        reg.register(
            WorkflowDefinition(
                name="bad_wf",
                actions=[
                    ActionDefinition(action_id="dup", description="first"),
                    ActionDefinition(action_id="dup", description="second"),
                ],
            )
        )

    # Valid registration
    wf1 = WorkflowDefinition(name="wf1", actions=[ActionDefinition(action_id="act1", description="act1")])
    reg.register(wf1)
    assert reg.get("wf1") == wf1
    assert reg.require("wf1") == wf1
    assert "wf1" in reg.list_workflows()

    # Prevent accidental overwrite
    wf1_v2 = WorkflowDefinition(name="wf1", version="2.0.0", actions=[])
    with pytest.raises(ValueError, match="already registered"):
        reg.register(wf1_v2, overwrite=False)

    # Allow explicit overwrite
    reg.register(wf1_v2, overwrite=True)
    assert reg.require("wf1").version == "2.0.0"

    # Unregister
    assert reg.unregister("wf1") is True
    assert reg.get("wf1") is None
    assert reg.unregister("wf1") is False

    with pytest.raises(KeyError, match="not registered"):
        reg.require("wf1")


def test_system_ops_workflow() -> None:
    """System ops workflow can be registered, queried, and its direct tools execute."""
    wf = create_system_ops_workflow()
    assert wf.name == "system_ops"
    assert len(wf.actions) == 4

    read_actions = [a.action_id for a in wf.get_read_only_actions()]
    assert "get_system_health" in read_actions
    assert "get_disk_usage" in read_actions

    mutating_actions = [a.action_id for a in wf.get_mutating_actions()]
    assert "clean_temp_cache" in mutating_actions
    clean_action = wf.get_action("clean_temp_cache")
    assert clean_action is not None
    assert clean_action.requires_approval is True
    assert "admin:system" in clean_action.required_permissions

    # Test actual live non-destructive tools
    health = execute_get_system_health()
    assert health["status"] == "healthy"
    assert health["cpu_count"] is not None and health["cpu_count"] > 0

    disk = execute_get_disk_usage(".")
    assert disk["free_gb"] > 0

    # Test cache cleaner on temp folder
    clean_res = execute_clean_temp_cache("non_existent_scratch_dir_xyz")
    assert clean_res["status"] == "directory_not_found"


def test_global_registry_helpers() -> None:
    """Global registry singleton helpers work as expected."""
    assert get_default_registry() is not None
    wf = create_system_ops_workflow()
    register_workflow(wf, overwrite=True)

    fetched = get_workflow("system_ops")
    assert fetched is not None
    assert fetched.name == "system_ops"


def test_action_decision_and_execution_schemas() -> None:
    """DecisionOutcome, ExecutionState, ActionDecision, and WorkflowExecutionResult instantiate cleanly."""
    decision = ActionDecision(
        request_id="req-123",
        workflow_name="system_ops",
        action_id="get_system_health",
        outcome=DecisionOutcome.EXECUTE_TOOL,
        confidence=0.98,
        reasoning="User requested host system diagnostics",
    )
    assert decision.outcome == DecisionOutcome.EXECUTE_TOOL
    assert decision.confidence == 0.98

    result = WorkflowExecutionResult(
        request_id="req-123",
        workflow_name="system_ops",
        action_id="get_system_health",
        outcome=DecisionOutcome.EXECUTE_TOOL,
        execution_state=ExecutionState.SUCCEEDED,
        output={"status": "healthy"},
        success=True,
    )
    assert result.execution_state == ExecutionState.SUCCEEDED
    assert result.output["status"] == "healthy"
