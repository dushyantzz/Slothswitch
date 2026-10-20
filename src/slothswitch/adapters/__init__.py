"""Adapter base interfaces for decision models and task models.

All model-specific code lives behind these interfaces so the core
router and policy engine remain provider-neutral.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from slothswitch.preprocessing import RoutingFeatures
from slothswitch.schemas import RouteCategory, RouteDecision, RoutingRequest, TaskResult


class DecisionAdapter(ABC):
    """Interface for decision models that propose a route for a request.

    The decision adapter answers a bounded question ("which route?"),
    it does NOT generate the final user-facing response.
    """

    @abstractmethod
    def predict_route(
        self,
        request: RoutingRequest,
        features: RoutingFeatures,
        available_routes: list[RouteCategory],
    ) -> RouteDecision:
        """Propose a routing decision for the given request.

        Args:
            request: The incoming request (used for context, not raw logging).
            features: Pre-extracted routing features.
            available_routes: The set of routes currently enabled by config.

        Returns:
            A RouteDecision with the proposed route and confidence.
        """
        ...

    def health_check(self) -> bool:
        """Return True if the adapter is ready to serve requests."""
        return True

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable adapter identifier."""
        ...


class TaskModelAdapter(ABC):
    """Interface for task execution models (small LLM, large LLM, deterministic handlers)."""

    @abstractmethod
    def execute(
        self,
        request: RoutingRequest,
        route: RouteCategory,
        context: dict[str, Any] | None = None,
    ) -> TaskResult:
        """Execute the task for the given request and route.

        Args:
            request: The original request.
            route: The validated route that was selected.
            context: Optional extra context (e.g., system prompt, template).

        Returns:
            A TaskResult with the generated output.
        """
        ...

    def health_check(self) -> bool:
        """Return True if the adapter is ready to serve requests."""
        return True

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable adapter identifier."""
        ...
