"""SlothSwitch Workflows package."""

from slothswitch.workflows.base import ActionDefinition, ActionParameter, WorkflowDefinition
from slothswitch.workflows.github_pr_management import create_github_workflow
from slothswitch.workflows.system_ops import create_system_ops_workflow

__all__ = [
    "ActionDefinition",
    "ActionParameter",
    "WorkflowDefinition",
    "create_github_workflow",
    "create_system_ops_workflow",
]
