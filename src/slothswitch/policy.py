"""Routing policy engine.

The policy layer is the deterministic gatekeeper between the decision model's
proposal and actual task execution. It validates, constrains, and overrides
routes based on configured rules — model output is never trusted blindly.
"""

from __future__ import annotations

from slothswitch.schemas import RouteCategory, RouteDecision, RoutingRequest


class PolicyViolation(Exception):
    """Raised when a route decision violates a policy rule."""


class RoutingPolicy:
    """Deterministic policy engine that validates and constrains routing decisions.

    Policy authorizes; model proposes.
    """

    def __init__(
        self,
        enabled_routes: set[RouteCategory] | None = None,
        high_risk_categories: list[str] | None = None,
        acceptance_threshold: float = 0.7,
        max_cost_tier: int | None = None,
        route_cost_tiers: dict[RouteCategory, int] | None = None,
    ) -> None:
        self.enabled_routes = enabled_routes or set(RouteCategory)
        self.high_risk_categories = high_risk_categories or []
        self.acceptance_threshold = acceptance_threshold
        self.max_cost_tier = max_cost_tier
        self.route_cost_tiers = route_cost_tiers or {
            RouteCategory.FAST_PATH: 0,
            RouteCategory.SMALL_LLM: 1,
            RouteCategory.LARGE_LLM: 2,
            RouteCategory.CLARIFY: 0,
            RouteCategory.FALLBACK: 2,
            RouteCategory.HUMAN_REVIEW: 0,
        }

    def validate_and_apply(
        self,
        decision: RouteDecision,
        request: RoutingRequest,
        category_hints: list[str] | None = None,
    ) -> RouteDecision:
        """Validate a proposed route decision against policy rules.

        Returns a (possibly modified) RouteDecision with `accepted` and
        `fallback_reason` fields set appropriately.

        The policy checks, in order:
        1. Route membership — is the proposed route a valid RouteCategory?
        2. Route enabled — is the route enabled in configuration?
        3. Caller constraints — does the route satisfy allowed_routes / max_cost_tier?
        4. High-risk override — does the request category require escalation?
        5. Confidence threshold — is confidence high enough for acceptance?
        """
        # 1. Route membership (already enforced by Pydantic, but be explicit)
        if decision.chosen_route not in RouteCategory:
            return self._fallback(decision, f"Invalid route: {decision.chosen_route}")

        # 2. Route enabled
        if decision.chosen_route not in self.enabled_routes:
            return self._fallback(decision, f"Route {decision.chosen_route} is disabled")

        # 3. Caller constraints
        if request.allowed_routes and decision.chosen_route not in request.allowed_routes:
            return self._fallback(
                decision,
                f"Route {decision.chosen_route} not in caller's allowed routes",
            )

        if request.max_cost_tier is not None:
            tier = self.route_cost_tiers.get(decision.chosen_route, 99)
            if tier > request.max_cost_tier:
                return self._fallback(
                    decision,
                    f"Route {decision.chosen_route} cost tier {tier} exceeds max {request.max_cost_tier}",
                )

        if self.max_cost_tier is not None:
            tier = self.route_cost_tiers.get(decision.chosen_route, 99)
            if tier > self.max_cost_tier:
                return self._fallback(
                    decision,
                    f"Route {decision.chosen_route} cost tier {tier} exceeds policy max {self.max_cost_tier}",
                )

        # 4. High-risk override
        if category_hints:
            for cat in category_hints:
                if (
                    cat in self.high_risk_categories
                    and decision.chosen_route
                    not in (
                        RouteCategory.LARGE_LLM,
                        RouteCategory.HUMAN_REVIEW,
                        RouteCategory.FALLBACK,
                    )
                ):
                    return self._escalate(
                        decision,
                        f"High-risk category '{cat}' requires escalation",
                    )


        # 5. Confidence threshold
        if (
            decision.confidence is not None
            and decision.confidence < self.acceptance_threshold
            and decision.chosen_route
            not in (RouteCategory.CLARIFY, RouteCategory.FALLBACK, RouteCategory.HUMAN_REVIEW)
        ):
            return self._fallback(
                decision,
                f"Confidence {decision.confidence:.3f} below threshold {self.acceptance_threshold}",
            )

        # All checks passed
        decision.accepted = True
        return decision

    # ----- Internal helpers -----

    @staticmethod
    def _fallback(decision: RouteDecision, reason: str) -> RouteDecision:
        """Convert a decision to FALLBACK."""
        decision.chosen_route = RouteCategory.FALLBACK
        decision.accepted = False
        decision.fallback_reason = reason
        return decision

    @staticmethod
    def _escalate(decision: RouteDecision, reason: str) -> RouteDecision:
        """Escalate a decision to HUMAN_REVIEW."""
        decision.chosen_route = RouteCategory.HUMAN_REVIEW
        decision.accepted = True
        decision.fallback_reason = reason
        return decision
