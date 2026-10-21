"""Routing policy engine.

The policy layer is the deterministic gatekeeper between the decision model's
proposal and actual task execution. It validates, constrains, and overrides
routes based on configured rules — model output is never trusted blindly.
"""

from __future__ import annotations

from typing import Any

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
        features: Any = None,
    ) -> RouteDecision:
        """Validate a proposed route decision against policy rules.

        Returns a (possibly modified) RouteDecision with `accepted` and
        `fallback_reason` fields set appropriately.

        The policy checks, in order:
        1. Route membership — is the proposed route a valid RouteCategory?
        2. Route enabled — is the route enabled in configuration?
        3. Caller constraints — does the route satisfy allowed_routes / max_cost_tier?
        4. Feature-based escalation — escalate when cheap route is inadequate.
        5. High-risk override — does the request category require escalation?
        6. Confidence threshold — is confidence high enough for acceptance?
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

        # 4. Feature-based Escalation Gates (prevent forcing cheap route on complex or underspecified queries)
        if features is not None:
            # 4a. Malformed noise override → FALLBACK
            if getattr(features, "is_malformed_noise", False) and decision.chosen_route != RouteCategory.FALLBACK:
                return self._fallback(
                    decision,
                    "Malformed or non-linguistic noise detected; routed to safe fallback",
                )

            # 4b. Deep technical reasoning escalation → LARGE_LLM
            if (
                getattr(features, "is_deep_technical", False)
                and decision.chosen_route in (RouteCategory.FAST_PATH, RouteCategory.SMALL_LLM)
                and RouteCategory.LARGE_LLM in self.enabled_routes
            ):
                decision.chosen_route = RouteCategory.LARGE_LLM
                decision.accepted = True
                decision.fallback_reason = "Deep technical reasoning requirements detected; policy escalated from cheap route to preserve task quality"
                decision.reasoning += " [Policy escalated to LARGE_LLM for complex reasoning]"
                return decision

            # 4c. Missing action parameters escalation → CLARIFY
            if (
                getattr(features, "missing_required_identifier", False)
                and decision.chosen_route in (RouteCategory.FAST_PATH, RouteCategory.SMALL_LLM)
                and RouteCategory.CLARIFY in self.enabled_routes
            ):
                decision.chosen_route = RouteCategory.CLARIFY
                decision.accepted = True
                decision.fallback_reason = "Action request missing specific identifier or details; policy escalated to CLARIFY"
                decision.reasoning += " [Policy escalated to CLARIFY due to missing identifier]"
                return decision

        # 5. High-risk override
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


        # 6. Confidence threshold
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


# ---------------------------------------------------------------------------
# Workflow-level policy engine
# ---------------------------------------------------------------------------

class WorkflowPolicy:
    """Deterministic policy gatekeeper for workflow actions.

    Enforces permission checks, read-only mode constraints, mutating approval gates,
    and action deny-lists before execution is permitted.
    """

    def __init__(
        self,
        read_only_mode: bool = False,
        require_approval_for_mutating: bool = True,
        min_confidence: float = 0.65,
        denied_actions: set[str] | None = None,
        allowed_actions: set[str] | None = None,
    ) -> None:
        self.read_only_mode = read_only_mode
        self.require_approval_for_mutating = require_approval_for_mutating
        self.min_confidence = min_confidence
        self.denied_actions = denied_actions or set()
        self.allowed_actions = allowed_actions

    def evaluate_action(
        self,
        decision: Any,
        workflow: Any,
        caller_permissions: list[str] | None = None,
    ) -> Any:
        """Validate and authorize a proposed workflow action.

        Args:
            decision: ActionDecision proposing an action.
            workflow: WorkflowDefinition containing action specifications.
            caller_permissions: Permissions possessed by the caller.

        Returns:
            The authorized (or modified/rejected) ActionDecision.
        """
        from slothswitch.schemas import DecisionOutcome

        action_def = workflow.get_action(decision.action_id)
        if action_def is None:
            decision.outcome = DecisionOutcome.FALLBACK
            decision.reasoning = f"Action '{decision.action_id}' is not registered in workflow '{workflow.name}'"
            return decision

        # 1. Deny-list check
        if decision.action_id in self.denied_actions:
            decision.outcome = DecisionOutcome.ABSTAIN
            decision.reasoning = f"Action '{decision.action_id}' is denied by policy"
            return decision

        # 2. Allowed actions constraint
        if self.allowed_actions is not None and decision.action_id not in self.allowed_actions:
            decision.outcome = DecisionOutcome.ABSTAIN
            decision.reasoning = f"Action '{decision.action_id}' is not in the permitted action set"
            return decision

        # 3. Read-only mode constraint
        if self.read_only_mode and action_def.is_mutating:
            decision.outcome = DecisionOutcome.ABSTAIN
            decision.reasoning = f"Action '{decision.action_id}' is mutating and rejected in read-only mode"
            return decision

        # 4. Caller authorization (deny-by-default for actions requiring permissions)
        if action_def.required_permissions:
            granted = set(caller_permissions or [])
            missing = [p for p in action_def.required_permissions if p not in granted]
            if missing:
                decision.outcome = DecisionOutcome.ABSTAIN
                decision.reasoning = (
                    f"Caller lacks required permissions {missing} for action '{decision.action_id}'"
                )
                return decision

        # 5. Approval gate
        if action_def.requires_approval or (action_def.is_mutating and self.require_approval_for_mutating):
            decision.requires_approval = True

        # 6. Confidence threshold gate
        if (
            decision.confidence is not None
            and decision.confidence < self.min_confidence
            and decision.outcome not in (DecisionOutcome.CLARIFY, DecisionOutcome.ABSTAIN, DecisionOutcome.HUMAN_REVIEW)
        ):
            decision.outcome = DecisionOutcome.CLARIFY
            decision.reasoning = (
                f"Confidence {decision.confidence:.3f} below minimum threshold {self.min_confidence:.3f}; clarifying"
            )
            return decision

        return decision
