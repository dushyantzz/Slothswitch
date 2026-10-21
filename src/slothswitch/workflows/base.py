"""Core workflow and action definitions for SlothSwitch.

Separates workflow specifications (actions, schemas, permissions, policies)
from the core decision and execution engines.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ActionParameter(BaseModel):
    """Specification of an input parameter for a workflow action."""

    name: str
    type_name: str = "str"
    description: str = ""
    required: bool = True
    default: Any = None
    choices: list[Any] | None = None


class ActionDefinition(BaseModel):
    """Specification of an action within a workflow."""

    action_id: str = Field(..., description="Unique action identifier within the workflow")
    description: str = Field(..., description="Clear semantic description of what the action does")
    parameters_schema: dict[str, Any] = Field(
        default_factory=dict,
        description="JSON Schema or dict of parameter names to specs",
    )
    output_schema: dict[str, Any] | None = Field(
        default=None,
        description="Optional schema of the returned output",
    )
    required_permissions: list[str] = Field(
        default_factory=list,
        description="Permissions required by the caller to execute this action",
    )
    is_mutating: bool = Field(
        default=False,
        description="True if the action modifies external state (destructive/stateful)",
    )
    requires_approval: bool = Field(
        default=False,
        description="True if human approval is mandatory before execution",
    )
    allows_generative: bool = Field(
        default=False,
        description="True if this action can or must use a generative model (e.g. Gemma)",
    )
    is_direct_execution: bool = Field(
        default=True,
        description="True if this action executes deterministically via registered tool",
    )
    timeout_seconds: float = Field(
        default=30.0,
        ge=0.1,
        description="Maximum execution timeout in seconds",
    )
    idempotent: bool = Field(
        default=True,
        description="True if calling the action multiple times has the same effect",
    )
    retry_policy: dict[str, Any] = Field(
        default_factory=lambda: {"max_retries": 0, "backoff_ms": 100},
        description="Retry policy config for execution",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)

    def validate_parameters(self, params: dict[str, Any]) -> tuple[bool, str | None]:
        """Validate input parameters against this action's schema.

        Returns:
            (True, None) if valid, or (False, error_message) if invalid.
        """
        if not self.parameters_schema:
            return True, None

        # Check required fields if schema defines "properties" (JSON Schema style)
        if "properties" in self.parameters_schema:
            required = self.parameters_schema.get("required", [])
            for field in required:
                if field not in params or params[field] is None:
                    return False, f"Missing required parameter '{field}' for action '{self.action_id}'"
            return True, None

        # Simple dict style: {param_name: {"required": True, "type": "str"}}
        for param_name, spec in self.parameters_schema.items():
            if isinstance(spec, dict):
                is_req = spec.get("required", False)
                if is_req and (param_name not in params or params[param_name] is None):
                    return False, f"Missing required parameter '{param_name}' for action '{self.action_id}'"
            elif isinstance(spec, ActionParameter):
                if spec.required and (param_name not in params or params[param_name] is None):
                    return False, f"Missing required parameter '{param_name}' for action '{self.action_id}'"

        return True, None


class WorkflowDefinition(BaseModel):
    """Specification of an entire workflow with its defined actions and policies."""

    name: str = Field(..., description="Unique workflow name, e.g. 'github_pr_management'")
    version: str = Field(default="1.0.0", description="Semantic version of the workflow")
    description: str = Field(default="", description="Summary of the workflow's purpose")
    actions: list[ActionDefinition] = Field(
        default_factory=list,
        description="Explicit list of supported actions in this workflow",
    )
    policies: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Workflow-level policy rules and constraints",
    )
    default_timeout_seconds: float = Field(default=30.0, ge=0.1)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def get_action(self, action_id: str) -> ActionDefinition | None:
        """Find an action by ID."""
        for action in self.actions:
            if action.action_id == action_id:
                return action
        return None

    def list_actions(self) -> list[str]:
        """Return list of all action IDs."""
        return [a.action_id for a in self.actions]

    def get_read_only_actions(self) -> list[ActionDefinition]:
        """Return all non-mutating actions."""
        return [a for a in self.actions if not a.is_mutating]

    def get_mutating_actions(self) -> list[ActionDefinition]:
        """Return all mutating actions."""
        return [a for a in self.actions if a.is_mutating]

    def get_generative_actions(self) -> list[ActionDefinition]:
        """Return actions that require generative model processing."""
        return [a for a in self.actions if a.allows_generative]

    def get_direct_execution_actions(self) -> list[ActionDefinition]:
        """Return actions that can be executed deterministically without generative LLMs."""
        return [a for a in self.actions if a.is_direct_execution]
