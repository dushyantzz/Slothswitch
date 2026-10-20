"""Unit tests for the deterministic RoutingPolicy engine."""


from slothswitch.policy import RoutingPolicy
from slothswitch.schemas import RouteCategory, RouteDecision, RoutingRequest


def test_policy_accepts_valid_decision():
    policy = RoutingPolicy(acceptance_threshold=0.7)
    req = RoutingRequest(request_id="r1", content="Regular query")
    dec = RouteDecision(
        request_id="r1",
        chosen_route=RouteCategory.SMALL_LLM,
        confidence=0.85,
    )
    result = policy.validate_and_apply(dec, req)
    assert result.accepted is True
    assert result.chosen_route == RouteCategory.SMALL_LLM
    assert result.fallback_reason is None


def test_policy_falls_back_on_disabled_route():
    policy = RoutingPolicy(
        enabled_routes={RouteCategory.FAST_PATH, RouteCategory.LARGE_LLM}
    )
    req = RoutingRequest(request_id="r2", content="Disabled small route query")
    dec = RouteDecision(
        request_id="r2",
        chosen_route=RouteCategory.SMALL_LLM,
        confidence=0.9,
    )
    result = policy.validate_and_apply(dec, req)
    assert result.accepted is False
    assert result.chosen_route == RouteCategory.FALLBACK
    assert "disabled" in result.fallback_reason.lower()


def test_policy_enforces_caller_allowed_routes():
    policy = RoutingPolicy()
    req = RoutingRequest(
        request_id="r3",
        content="Constrained query",
        allowed_routes=[RouteCategory.FAST_PATH],
    )
    dec = RouteDecision(
        request_id="r3",
        chosen_route=RouteCategory.LARGE_LLM,
        confidence=0.95,
    )
    result = policy.validate_and_apply(dec, req)
    assert result.accepted is False
    assert result.chosen_route == RouteCategory.FALLBACK
    assert "allowed routes" in result.fallback_reason.lower()


def test_policy_enforces_max_cost_tier():
    policy = RoutingPolicy()
    req = RoutingRequest(
        request_id="r4",
        content="Cheap tier only",
        max_cost_tier=0,  # Only tier 0 allowed (e.g. FAST_PATH)
    )
    dec = RouteDecision(
        request_id="r4",
        chosen_route=RouteCategory.LARGE_LLM,  # Tier 2
        confidence=0.99,
    )
    result = policy.validate_and_apply(dec, req)
    assert result.accepted is False
    assert result.chosen_route == RouteCategory.FALLBACK
    assert "cost tier" in result.fallback_reason.lower()


def test_policy_escalates_on_high_risk_categories():
    policy = RoutingPolicy(high_risk_categories=["security", "financial"])
    req = RoutingRequest(request_id="r5", content="Potential security breach detected")
    dec = RouteDecision(
        request_id="r5",
        chosen_route=RouteCategory.FAST_PATH,
        confidence=0.95,
    )
    result = policy.validate_and_apply(dec, req, category_hints=["security"])
    assert result.chosen_route == RouteCategory.HUMAN_REVIEW
    assert result.accepted is True
    assert "High-risk" in result.fallback_reason


def test_policy_falls_back_on_low_confidence():
    policy = RoutingPolicy(acceptance_threshold=0.8)
    req = RoutingRequest(request_id="r6", content="Ambiguous query")
    dec = RouteDecision(
        request_id="r6",
        chosen_route=RouteCategory.SMALL_LLM,
        confidence=0.65,  # Below threshold 0.8
    )
    result = policy.validate_and_apply(dec, req)
    assert result.accepted is False
    assert result.chosen_route == RouteCategory.FALLBACK
    assert "below threshold" in result.fallback_reason.lower()


def test_policy_does_not_fall_back_low_confidence_for_abstentions():
    # CLARIFY, FALLBACK, HUMAN_REVIEW should NOT be rejected for having low confidence
    policy = RoutingPolicy(acceptance_threshold=0.8)
    req = RoutingRequest(request_id="r7", content="Missing info")
    dec = RouteDecision(
        request_id="r7",
        chosen_route=RouteCategory.CLARIFY,
        confidence=0.5,
    )
    result = policy.validate_and_apply(dec, req)
    assert result.chosen_route == RouteCategory.CLARIFY
    assert result.accepted is True
