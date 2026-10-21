"""Workflow registry for SlothSwitch.

Maintains registered workflows and ensures typed validation, preventing
duplicate action definitions and providing dynamic discovery.
"""

from __future__ import annotations

import logging

from slothswitch.workflows.base import WorkflowDefinition

logger = logging.getLogger(__name__)


class WorkflowRegistry:
    """Registry maintaining active workflow definitions."""

    def __init__(self) -> None:
        self._workflows: dict[str, WorkflowDefinition] = {}

    def register(self, workflow: WorkflowDefinition, overwrite: bool = False) -> None:
        """Register a workflow definition.

        Args:
            workflow: The workflow definition to register.
            overwrite: If True, allow replacing an existing workflow with the same name.

        Raises:
            ValueError: If workflow name is invalid, workflow is already registered
                        and overwrite is False, or duplicate action IDs exist within
                        the workflow.
        """
        if not workflow.name or not workflow.name.strip():
            raise ValueError("Workflow name cannot be empty")

        if workflow.name in self._workflows and not overwrite:
            raise ValueError(
                f"Workflow '{workflow.name}' is already registered. Set overwrite=True to replace it."
            )

        # Check for duplicate action IDs within the workflow
        seen_action_ids: set[str] = set()
        for action in workflow.actions:
            if action.action_id in seen_action_ids:
                raise ValueError(
                    f"Duplicate action_id '{action.action_id}' found in workflow '{workflow.name}'"
                )
            seen_action_ids.add(action.action_id)

        self._workflows[workflow.name] = workflow
        logger.info(
            "Registered workflow '%s' (v%s) with %d actions",
            workflow.name,
            workflow.version,
            len(workflow.actions),
        )

    def get(self, name: str) -> WorkflowDefinition | None:
        """Retrieve a workflow by name, or None if not found."""
        return self._workflows.get(name)

    def require(self, name: str) -> WorkflowDefinition:
        """Retrieve a workflow by name, or raise KeyError if not found."""
        wf = self._workflows.get(name)
        if wf is None:
            raise KeyError(f"Workflow '{name}' is not registered. Available: {self.list_workflows()}")
        return wf

    def list_workflows(self) -> list[str]:
        """Return a sorted list of registered workflow names."""
        return sorted(self._workflows.keys())

    def unregister(self, name: str) -> bool:
        """Remove a workflow from the registry. Returns True if removed, False if not found."""
        if name in self._workflows:
            del self._workflows[name]
            logger.info("Unregistered workflow '%s'", name)
            return True
        return False

    def clear(self) -> None:
        """Clear all registered workflows."""
        self._workflows.clear()


# ---------------------------------------------------------------------------
# Global default registry instance
# ---------------------------------------------------------------------------

_GLOBAL_REGISTRY: WorkflowRegistry | None = None


def get_default_registry() -> WorkflowRegistry:
    """Return the global default workflow registry instance."""
    global _GLOBAL_REGISTRY
    if _GLOBAL_REGISTRY is None:
        _GLOBAL_REGISTRY = WorkflowRegistry()
    return _GLOBAL_REGISTRY


def register_workflow(workflow: WorkflowDefinition, overwrite: bool = False) -> None:
    """Register a workflow in the default registry."""
    get_default_registry().register(workflow, overwrite=overwrite)


def get_workflow(name: str) -> WorkflowDefinition | None:
    """Retrieve a workflow from the default registry."""
    return get_default_registry().get(name)
