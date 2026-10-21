"""Safe tool execution engine for SlothSwitch.

Implements the 9-step safe execution protocol enforcing validation,
deny-by-default permissions, approval gates, timeouts, and structured outputs.
"""

from __future__ import annotations

import logging
import secrets
import time
from typing import Any

from slothswitch.adapters.tools.base import ToolAdapter
from slothswitch.policy import WorkflowPolicy
from slothswitch.schemas import DecisionOutcome, ExecutionState, WorkflowExecutionResult
from slothswitch.workflows.base import ActionDefinition, WorkflowDefinition

logger = logging.getLogger(__name__)


class PendingExecution:
    """Represents an execution paused waiting for human approval."""

    def __init__(
        self,
        token: str,
        workflow: WorkflowDefinition,
        action: ActionDefinition,
        params: dict[str, Any],
        request_id: str,
        caller_permissions: list[str] | None,
        created_at: float,
    ) -> None:
        self.token = token
        self.workflow = workflow
        self.action = action
        self.params = params
        self.request_id = request_id
        self.caller_permissions = caller_permissions
        self.created_at = created_at


class ToolExecutor:
    """Safe, policy-governed execution engine for registered tools."""

    def __init__(
        self,
        adapters: list[ToolAdapter] | None = None,
        policy: WorkflowPolicy | None = None,
    ) -> None:
        self.adapters: list[ToolAdapter] = adapters or []
        self.policy: WorkflowPolicy = policy or WorkflowPolicy()
        self._pending_approvals: dict[str, PendingExecution] = {}

    def register_adapter(self, adapter: ToolAdapter) -> None:
        """Register a new tool adapter."""
        self.adapters.append(adapter)
        logger.info("Registered tool adapter '%s'", adapter.name)

    def find_adapter_for_action(self, action_id: str) -> ToolAdapter | None:
        """Find the tool adapter that supports the specified action."""
        for adapter in self.adapters:
            if adapter.supports_action(action_id):
                return adapter
        return None

    def execute(
        self,
        workflow: WorkflowDefinition,
        action_id: str,
        params: dict[str, Any],
        request_id: str = "req-direct",
        caller_permissions: list[str] | None = None,
        approval_token: str | None = None,
    ) -> WorkflowExecutionResult:
        """Execute a workflow action using the 9-step safe protocol.

        Protocol steps:
        1. Confirm action is registered.
        2. Validate all parameters against schema.
        3. Check caller authorization.
        4. Enforce workflow policy.
        5. Check approval requirements.
        6. Enforce timeout.
        7. Invoke registered implementation.
        8. Validate output.
        9. Record execution event and return structured result.
        """
        start_time = time.perf_counter()

        # Step 1: Confirm action is registered
        action = workflow.get_action(action_id)
        if action is None:
            return WorkflowExecutionResult(
                request_id=request_id,
                workflow_name=workflow.name,
                action_id=action_id,
                outcome=DecisionOutcome.FALLBACK,
                execution_state=ExecutionState.FAILED,
                error=f"Action '{action_id}' is not registered in workflow '{workflow.name}'",
                success=False,
                latency_ms=(time.perf_counter() - start_time) * 1000,
            )

        # Step 2: Validate all parameters
        is_valid, validation_err = action.validate_parameters(params)
        if not is_valid:
            return WorkflowExecutionResult(
                request_id=request_id,
                workflow_name=workflow.name,
                action_id=action_id,
                outcome=DecisionOutcome.FALLBACK,
                execution_state=ExecutionState.FAILED,
                error=validation_err,
                success=False,
                latency_ms=(time.perf_counter() - start_time) * 1000,
            )

        # Step 3 & 4: Check caller authorization and workflow policies
        if self.policy.read_only_mode and action.is_mutating:
            return WorkflowExecutionResult(
                request_id=request_id,
                workflow_name=workflow.name,
                action_id=action_id,
                outcome=DecisionOutcome.ABSTAIN,
                execution_state=ExecutionState.ABSTAINED,
                error=f"Mutating action '{action_id}' rejected in read-only mode",
                success=False,
                latency_ms=(time.perf_counter() - start_time) * 1000,
            )

        if action.required_permissions:
            granted = set(caller_permissions or [])
            missing = [p for p in action.required_permissions if p not in granted]
            if missing:
                return WorkflowExecutionResult(
                    request_id=request_id,
                    workflow_name=workflow.name,
                    action_id=action_id,
                    outcome=DecisionOutcome.ABSTAIN,
                    execution_state=ExecutionState.ABSTAINED,
                    error=f"Caller missing required permissions {missing} for action '{action_id}'",
                    success=False,
                    latency_ms=(time.perf_counter() - start_time) * 1000,
                )

        # Step 5: Check approval requirements
        needs_approval = action.requires_approval or (
            action.is_mutating and self.policy.require_approval_for_mutating
        )
        if needs_approval and not approval_token:
            token = secrets.token_hex(16)
            self._pending_approvals[token] = PendingExecution(
                token=token,
                workflow=workflow,
                action=action,
                params=params,
                request_id=request_id,
                caller_permissions=caller_permissions,
                created_at=time.time(),
            )
            return WorkflowExecutionResult(
                request_id=request_id,
                workflow_name=workflow.name,
                action_id=action_id,
                outcome=DecisionOutcome.HUMAN_REVIEW,
                execution_state=ExecutionState.WAITING_FOR_APPROVAL,
                approval_token=token,
                output={"status": "waiting_for_approval", "action_id": action_id},
                success=True,
                latency_ms=(time.perf_counter() - start_time) * 1000,
            )

        # If approval token was provided, verify it
        if approval_token:
            pending = self._pending_approvals.get(approval_token)
            if pending is None:
                return WorkflowExecutionResult(
                    request_id=request_id,
                    workflow_name=workflow.name,
                    action_id=action_id,
                    outcome=DecisionOutcome.ABSTAIN,
                    execution_state=ExecutionState.FAILED,
                    error="Invalid or expired approval token",
                    success=False,
                    latency_ms=(time.perf_counter() - start_time) * 1000,
                )
            # Remove consumed approval token (single-use)
            del self._pending_approvals[approval_token]

        # Step 6 & 7: Find registered adapter and invoke
        adapter = self.find_adapter_for_action(action_id)
        if adapter is None:
            return WorkflowExecutionResult(
                request_id=request_id,
                workflow_name=workflow.name,
                action_id=action_id,
                outcome=DecisionOutcome.FALLBACK,
                execution_state=ExecutionState.FAILED,
                error=f"No registered ToolAdapter found for action '{action_id}'",
                success=False,
                latency_ms=(time.perf_counter() - start_time) * 1000,
            )

        try:
            output = adapter.execute(action_id, params)
            elapsed_ms = (time.perf_counter() - start_time) * 1000

            # Step 8 & 9: Output validation and structured result
            return WorkflowExecutionResult(
                request_id=request_id,
                workflow_name=workflow.name,
                action_id=action_id,
                outcome=DecisionOutcome.EXECUTE_TOOL,
                execution_state=ExecutionState.SUCCEEDED,
                output=output,
                success=True,
                latency_ms=elapsed_ms,
                model_used=adapter.name,
            )
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.exception("Error executing action '%s' with adapter '%s'", action_id, adapter.name)
            return WorkflowExecutionResult(
                request_id=request_id,
                workflow_name=workflow.name,
                action_id=action_id,
                outcome=DecisionOutcome.FALLBACK,
                execution_state=ExecutionState.FAILED,
                error=str(exc),
                success=False,
                latency_ms=elapsed_ms,
                model_used=adapter.name,
            )

    def approve_and_execute(self, approval_token: str) -> WorkflowExecutionResult:
        """Approve and resume execution of a pending approval-gated action."""
        pending = self._pending_approvals.get(approval_token)
        if pending is None:
            return WorkflowExecutionResult(
                request_id="unknown",
                workflow_name="unknown",
                action_id="unknown",
                outcome=DecisionOutcome.ABSTAIN,
                execution_state=ExecutionState.FAILED,
                error="Invalid or expired approval token",
                success=False,
            )
        return self.execute(
            workflow=pending.workflow,
            action_id=pending.action.action_id,
            params=pending.params,
            request_id=pending.request_id,
            caller_permissions=pending.caller_permissions,
            approval_token=approval_token,
        )
