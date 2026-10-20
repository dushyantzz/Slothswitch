"""Mock decision adapter for testing without a real decision model.

This adapter uses simple heuristic rules to propose a route,
allowing the full routing pipeline to be tested end-to-end
without requiring Laya or any external model.
"""

from __future__ import annotations

from slothswitch.adapters import DecisionAdapter
from slothswitch.preprocessing import RoutingFeatures
from slothswitch.schemas import RouteCategory, RouteDecision, RoutingRequest


class MockDecisionAdapter(DecisionAdapter):
    """Rule-based mock that simulates a decision model using simple heuristics.

    Routing logic (intentionally simplistic — for testing only):
    - Very short requests with category hints → FAST_PATH
    - Requests with missing info indicators → CLARIFY
    - Medium complexity → SMALL_LLM
    - Long or complex requests → LARGE_LLM
    """

    def __init__(self, default_confidence: float = 0.85) -> None:
        self._default_confidence = default_confidence

    @property
    def name(self) -> str:
        return "mock-decision"

    def predict_route(
        self,
        request: RoutingRequest,
        features: RoutingFeatures,
        available_routes: list[RouteCategory],
    ) -> RouteDecision:
        """Apply simple heuristic rules to propose a route."""
        route = RouteCategory.SMALL_LLM
        confidence = self._default_confidence
        reasoning = ""

        # Check for missing information indicators
        lower_content = request.content.lower()
        missing_info_indicators = ["unclear", "what do you mean", "can you clarify", "more info"]
        if any(ind in lower_content for ind in missing_info_indicators):
            route = RouteCategory.CLARIFY
            confidence = 0.90
            reasoning = "Request appears to need clarification"

        # Very short + has category hint → fast path
        elif features.word_count <= 15 and features.category_hints:
            route = RouteCategory.FAST_PATH
            confidence = 0.92
            reasoning = f"Short request with clear category: {features.category_hints}"

        # Has code or long → large LLM
        elif features.has_code_block or features.word_count > 200:
            route = RouteCategory.LARGE_LLM
            confidence = 0.80
            reasoning = "Complex or long request requiring capable model"

        # Medium length → small LLM
        else:
            route = RouteCategory.SMALL_LLM
            confidence = 0.85
            reasoning = "Standard request suitable for smaller model"

        # Ensure the route is in the available set
        if route not in available_routes:
            route = RouteCategory.FALLBACK
            confidence = 0.50
            reasoning = f"Preferred route not available; falling back"

        return RouteDecision(
            request_id=request.request_id,
            chosen_route=route,
            confidence=confidence,
            reasoning=reasoning,
            decision_model=self.name,
        )
