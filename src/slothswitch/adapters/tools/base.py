"""Base interface for safe tool execution adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ToolAdapter(ABC):
    """Abstract base class for all deterministic tool adapters."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this tool adapter."""
        ...

    @abstractmethod
    def supports_action(self, action_id: str) -> bool:
        """Return True if this adapter can execute the specified action."""
        ...

    @abstractmethod
    def execute(self, action_id: str, params: dict[str, Any]) -> dict[str, Any]:
        """Execute the action with the given parameters and return structured result.

        Args:
            action_id: Identifier of the action to execute.
            params: Validated input parameters.

        Returns:
            Dict containing output data or execution status.
        """
        ...
