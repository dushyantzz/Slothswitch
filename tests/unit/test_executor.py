"""Unit tests for ToolExecutor and safe tool execution protocol."""

from slothswitch.adapters.tools.system_ops_tool import SystemOpsToolAdapter
from slothswitch.executor import ToolExecutor
from slothswitch.policy import WorkflowPolicy
from slothswitch.schemas import ActionDecision, DecisionOutcome, ExecutionState
from slothswitch.workflows.system_ops import create_system_ops_workflow


def test_executor_successful_read_action() -> None:
    """Read-only action executes directly and returns SUCCEEDED with structured data."""
    wf = create_system_ops_workflow()
    adapter = SystemOpsToolAdapter()
    executor = ToolExecutor(adapters=[adapter])

    res = executor.execute(
        workflow=wf,
        action_id="get_system_health",
        params={},
        caller_permissions=["system:read"],
    )

    assert res.execution_state == ExecutionState.SUCCEEDED
    assert res.success is True
    assert res.output["status"] == "healthy"
    assert res.output["cpu_count"] > 0
    assert res.latency_ms is not None and res.latency_ms >= 0


def test_executor_unregistered_action() -> None:
    """Attempting to execute an unregistered action returns FAILED."""
    wf = create_system_ops_workflow()
    executor = ToolExecutor(adapters=[SystemOpsToolAdapter()])

    res = executor.execute(
        workflow=wf,
        action_id="format_hard_drive",
        params={},
    )

    assert res.execution_state == ExecutionState.FAILED
    assert res.success is False
    assert "not registered" in (res.error or "")


def test_executor_invalid_params() -> None:
    """Action with missing required parameters fails parameter validation."""
    wf = create_system_ops_workflow()
    executor = ToolExecutor(adapters=[SystemOpsToolAdapter()])

    # clean_temp_cache requires target_dir
    res = executor.execute(
        workflow=wf,
        action_id="clean_temp_cache",
        params={},
        caller_permissions=["admin:system"],
    )

    assert res.execution_state == ExecutionState.FAILED
    assert res.success is False
    assert "Missing required parameter 'target_dir'" in (res.error or "")


def test_executor_read_only_mode_blocks_mutating() -> None:
    """Policy in read_only_mode rejects mutating actions with ABSTAINED."""
    wf = create_system_ops_workflow()
    policy = WorkflowPolicy(read_only_mode=True)
    executor = ToolExecutor(adapters=[SystemOpsToolAdapter()], policy=policy)

    res = executor.execute(
        workflow=wf,
        action_id="clean_temp_cache",
        params={"target_dir": "scratch"},
        caller_permissions=["admin:system"],
    )

    assert res.execution_state == ExecutionState.ABSTAINED
    assert res.outcome == DecisionOutcome.ABSTAIN
    assert "read-only mode" in (res.error or "")


def test_executor_missing_permissions_blocks() -> None:
    """Caller without required permissions is denied execution."""
    wf = create_system_ops_workflow()
    executor = ToolExecutor(adapters=[SystemOpsToolAdapter()])

    # clean_temp_cache requires admin:system, caller only has system:read
    res = executor.execute(
        workflow=wf,
        action_id="clean_temp_cache",
        params={"target_dir": "scratch"},
        caller_permissions=["system:read"],
    )

    assert res.execution_state == ExecutionState.ABSTAINED
    assert "missing required permissions" in (res.error or "").lower()


def test_executor_approval_gating_flow() -> None:
    """Mutating action requiring approval pauses in WAITING_FOR_APPROVAL until token approved."""
    wf = create_system_ops_workflow()
    executor = ToolExecutor(adapters=[SystemOpsToolAdapter()])

    # 1. First invocation: without approval token
    res = executor.execute(
        workflow=wf,
        action_id="clean_temp_cache",
        params={"target_dir": "non_existent_scratch"},
        caller_permissions=["admin:system"],
    )

    assert res.execution_state == ExecutionState.WAITING_FOR_APPROVAL
    assert res.outcome == DecisionOutcome.HUMAN_REVIEW
    assert res.approval_token is not None

    token = res.approval_token

    # 2. Approve and resume execution
    res2 = executor.approve_and_execute(token)
    assert res2.execution_state == ExecutionState.SUCCEEDED
    assert res2.output["status"] == "directory_not_found"

    # 3. Re-using the same token fails (single-use)
    res3 = executor.approve_and_execute(token)
    assert res3.execution_state == ExecutionState.FAILED
    assert "Invalid or expired" in (res3.error or "")


def test_workflow_policy_evaluation() -> None:
    """WorkflowPolicy accurately checks denied actions, permitted sets, and confidence."""
    wf = create_system_ops_workflow()
    policy = WorkflowPolicy(
        denied_actions={"get_disk_usage"},
        min_confidence=0.8,
    )

    # Denied action
    dec1 = ActionDecision(
        request_id="1",
        workflow_name=wf.name,
        action_id="get_disk_usage",
        confidence=0.99,
    )
    res1 = policy.evaluate_action(dec1, wf, caller_permissions=["system:read"])
    assert res1.outcome == DecisionOutcome.ABSTAIN
    assert "denied by policy" in res1.reasoning

    # Low confidence action gets CLARIFY
    dec2 = ActionDecision(
        request_id="2",
        workflow_name=wf.name,
        action_id="get_system_health",
        confidence=0.5,
    )
    res2 = policy.evaluate_action(dec2, wf, caller_permissions=["system:read"])
    assert res2.outcome == DecisionOutcome.CLARIFY
    assert "below minimum threshold" in res2.reasoning
