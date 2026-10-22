"""Mock decision adapter for testing without a real decision model.

This adapter uses simple heuristic rules to propose a route,
allowing the full routing pipeline to be tested end-to-end
without requiring Laya or any external model.
"""

from __future__ import annotations

from typing import Any

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

        # Check for missing information indicators or ambiguous fragments
        lower_content = request.content.lower().strip()
        missing_info_indicators = [
            "unclear", "what do you mean", "can you clarify", "more info",
            "broken", "doesn't work", "does not work", "help please", "failed",
            "something went wrong", "not working today", "not working", "error on page",
            "system issue", "problem with my account", "why is it doing this",
        ]
        punct_ratio = sum(1 for c in request.content if not c.isalnum() and not c.isspace()) / max(1, len(request.content))

        # Has code or long → large LLM
        if features.has_code_block or features.word_count > 45:
            route = RouteCategory.LARGE_LLM
            confidence = 0.85
            reasoning = "Complex or long request requiring capable model"

        # Check for malformed / non-linguistic input
        elif punct_ratio > 0.35 and features.word_count < 10:
            route = RouteCategory.FALLBACK
            confidence = 0.50
            reasoning = "Malformed or non-linguistic input; routing to safe fallback"

        # Check for missing information indicators or ambiguous fragments
        elif any(ind in lower_content for ind in missing_info_indicators) or (
            0 < features.word_count <= 2 and not features.category_hints
        ):
            route = RouteCategory.CLARIFY
            confidence = 0.90
            reasoning = "Request is ambiguous or missing required parameters"

        # Very short + has category hint → fast path
        elif features.word_count <= 15 and features.category_hints:
            route = RouteCategory.FAST_PATH
            confidence = 0.92
            reasoning = f"Short request with clear category: {features.category_hints}"

        # Medium length → small LLM
        else:
            route = RouteCategory.SMALL_LLM
            confidence = 0.85
            reasoning = "Standard request suitable for smaller model"

        # Ensure the route is in the available set
        if route not in available_routes:
            route = RouteCategory.FALLBACK
            confidence = 0.50
            reasoning = "Preferred route not available; falling back"


        return RouteDecision(
            request_id=request.request_id,
            chosen_route=route,
            confidence=confidence,
            reasoning=reasoning,
            decision_model=self.name,
        )

    def predict_action(
        self,
        request_content: str,
        workflow: Any,
        request_id: str = "req-action",
        allowed_actions: list[str] | None = None,
    ) -> Any:
        """Heuristically match request to a workflow action for testing."""
        from slothswitch.schemas import ActionDecision, DecisionOutcome

        candidate_actions = workflow.actions
        if allowed_actions is not None:
            candidate_actions = [a for a in candidate_actions if a.action_id in allowed_actions]

        if not candidate_actions:
            return ActionDecision(
                request_id=request_id,
                workflow_name=workflow.name,
                action_id="none",
                outcome=DecisionOutcome.FALLBACK,
                confidence=0.0,
                reasoning="No candidate actions available in workflow",
                decision_model=self.name,
            )

        lower_req = request_content.lower()

        if any(w in lower_req for w in ("delete", "force push", "charge", "grant admin", "drop table", "visibility", "transfer")):
            return ActionDecision(
                request_id=request_id,
                workflow_name=workflow.name,
                action_id="none",
                outcome=DecisionOutcome.ABSTAIN,
                confidence=self._default_confidence,
                reasoning="Mock heuristic detected destructive/out-of-scope query",
                decision_model=self.name,
                decision_latency_ms=1.0,
            )

        if lower_req.strip() in ("add a comment", "count them please", "get the labels", "is it passing tests?"):
            return ActionDecision(
                request_id=request_id,
                workflow_name=workflow.name,
                action_id="none",
                outcome=DecisionOutcome.CLARIFY,
                confidence=self._default_confidence,
                reasoning="Mock heuristic detected ambiguous query",
                decision_model=self.name,
                decision_latency_ms=1.0,
            )

        # Check for keyword matches in action descriptions
        selected_action = candidate_actions[0]
        max_matches = -1
        for action in candidate_actions:
            keywords = action.action_id.split("_")
            matches = sum(1 for kw in keywords if kw in lower_req)
            if matches > max_matches:
                max_matches = matches
                selected_action = action

        outcome = (
            DecisionOutcome.USE_GENERATIVE_MODEL
            if selected_action.allows_generative
            else DecisionOutcome.EXECUTE_TOOL
        )

        return ActionDecision(
            request_id=request_id,
            workflow_name=workflow.name,
            action_id=selected_action.action_id,
            outcome=outcome,
            confidence=self._default_confidence,
            reasoning=f"Mock heuristic selected '{selected_action.action_id}' (matches={max_matches})",
            requires_approval=selected_action.requires_approval,
            decision_model=self.name,
            decision_latency_ms=1.0,
        )
