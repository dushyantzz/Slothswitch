"""Laya decision adapter — wraps the Laya Router for SlothSwitch routing decisions.

This module is the ONLY place that imports `laya`. If Laya is not installed,
the rest of the application continues to work with the mock adapter.

Guidance from the Laya model card (verified 2024-10):
- Use `Router` class with `predict(state, questions)` API
- Use typed `choice` questions for route selection
- Do NOT gate on `action.act_probability`
- Validate confidence on held-out data before trusting it
- Select appropriate checkpoint (base, multilingual, typed-decisions)
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any

from slothswitch.adapters import DecisionAdapter
from slothswitch.preprocessing import RoutingFeatures
from slothswitch.schemas import RouteCategory, RouteDecision, RoutingRequest

logger = logging.getLogger(__name__)

# Route labels and descriptions for the Laya choice question
_ROUTE_CRITERIA: dict[str, str] = {
    "FAST_PATH": "Simple factual lookup, status check, or rule-based task with a deterministic answer",
    "SMALL_LLM": "Standard text generation, summarization, or routine customer support response",
    "LARGE_LLM": "Complex reasoning, multi-step analysis, code debugging, or nuanced generation",
    "CLARIFY": "The request is ambiguous or missing essential information needed to respond",
    "HUMAN_REVIEW": "The request involves sensitive, risky, or out-of-scope topics requiring human judgment",
}


class LayaDecisionAdapter(DecisionAdapter):
    """Adapter wrapping the Laya Router for structured route selection.

    Uses Laya's typed `choice` question to select from the configured routes.
    """

    def __init__(
        self,
        checkpoint: str = "convaiinnovations/laya",
        model_variant: str | None = None,
        preload: bool = False,
    ) -> None:
        self._checkpoint = checkpoint
        self._model_variant = model_variant
        self._router: Any = None
        self._loaded = False

        if preload:
            self._load()

    @property
    def name(self) -> str:
        return f"laya:{self._checkpoint}"

    def _load(self) -> None:
        """Lazily load the Laya Router."""
        if self._loaded:
            return
        try:
            # If checkpoint is already cached, avoid slow online HEAD checks
            try:
                from huggingface_hub.constants import HUGGINGFACE_HUB_CACHE
                repo_dir = f"models--{self._checkpoint.replace('/', '--')}"
                if (Path(HUGGINGFACE_HUB_CACHE) / repo_dir).exists():
                    os.environ.setdefault("HF_HUB_OFFLINE", "1")
            except Exception as e:
                logger.debug("Could not verify local HF cache status: %s", e)

            from laya import Router  # type: ignore[import-untyped]

            kwargs: dict[str, Any] = {}
            if self._model_variant:
                kwargs["model"] = self._model_variant
            self._router = Router(**kwargs)
            self._loaded = True
            logger.info("Laya Router loaded (checkpoint=%s)", self._checkpoint)
        except ImportError:
            raise ImportError(
                "Laya is not installed. Install with: pip install laya\n"
                "Or use the mock adapter for testing: adapter='mock'"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load Laya Router: {e}") from e

    def health_check(self) -> bool:
        """Check if Laya can be loaded."""
        try:
            self._load()
            return self._loaded
        except Exception:
            return False

    def predict_route(
        self,
        request: RoutingRequest,
        features: RoutingFeatures,
        available_routes: list[RouteCategory],
    ) -> RouteDecision:
        """Use Laya to predict the optimal route."""
        self._load()
        start_time = time.perf_counter()

        # Build the state for Laya — use redacted summary, not raw content
        state = {
            "subject": features.redacted_summary[:100] if features.redacted_summary else "",
            "body": features.redacted_summary if features.redacted_summary else "",
            "word_count": str(features.word_count),
            "has_code": str(features.has_code_block),
            "category_hints": ", ".join(features.category_hints) if features.category_hints else "none",
        }

        # Build criteria filtered to available routes
        criteria = {
            route.value: _ROUTE_CRITERIA.get(route.value, route.value)
            for route in available_routes
            if route.value in _ROUTE_CRITERIA
        }

        if not criteria:
            return RouteDecision(
                request_id=request.request_id,
                chosen_route=RouteCategory.FALLBACK,
                confidence=0.0,
                reasoning="No valid routes available for Laya choice question",
                decision_model=self.name,
            )

        questions = {
            "route": {
                "type": "choice",
                "instructions": "Which processing path is most appropriate for this request?",
                "criteria": criteria,
            }
        }

        try:
            result = self._router.predict(state, questions)
            elapsed_ms = (time.perf_counter() - start_time) * 1000

            # Extract route from result
            route_answer = result.get("answers", {}).get("route", {})
            chosen_label = route_answer.get("choice", "FALLBACK")
            probabilities = route_answer.get("probabilities", {})
            # Use answer_confidence (calibrated softmax probability of the chosen option)
            confidence = route_answer.get("answer_confidence")
            if confidence is None:
                confidence = probabilities.get(chosen_label, route_answer.get("confidence", 0.85))

            # Validate the returned label
            try:
                chosen_route = RouteCategory(chosen_label)
            except ValueError:
                logger.warning("Laya returned invalid route label: %s", chosen_label)
                chosen_route = RouteCategory.FALLBACK
                confidence = 0.0

            return RouteDecision(
                request_id=request.request_id,
                chosen_route=chosen_route,
                confidence=confidence,
                reasoning=f"Laya neural decision: {chosen_label} (prob={confidence:.4f})",
                decision_model=self.name,
                latency_ms=elapsed_ms,
                decision_latency_ms=elapsed_ms,
            )

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.error("Laya prediction failed: %s", e)
            return RouteDecision(
                request_id=request.request_id,
                chosen_route=RouteCategory.FALLBACK,
                confidence=0.0,
                reasoning=f"Laya prediction error: {e}",
                fallback_reason=f"Decision model error: {e}",
                decision_model=self.name,
                latency_ms=elapsed_ms,
            )

    def predict_action(
        self,
        request_content: str,
        workflow: Any,
        request_id: str = "req-action",
        allowed_actions: list[str] | None = None,
    ) -> Any:
        """Use Laya to dynamically select an action from the workflow's action space."""
        from slothswitch.schemas import ActionDecision, DecisionOutcome

        self._load()
        start_time = time.perf_counter()

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

        criteria = {action.action_id: action.description for action in candidate_actions}
        criteria["clarify"] = "The request is vague, ambiguous, or missing required details to determine what action to take."
        criteria["abstain"] = "The request is prohibited, out-of-scope, or involves administrative access, billing, repository visibility, or destructive actions."

        lower_content = request_content.lower()
        entity_cue = (
            "pull_request"
            if ("pull request" in lower_content or " pr" in lower_content or " prs" in lower_content or lower_content.startswith("pr"))
            else ("issue" if ("issue" in lower_content or "bug" in lower_content) else "general")
        )
        subject_prefix = entity_cue.replace("_", " ").title() if entity_cue != "general" else "Task"
        state = {
            "subject": f"{subject_prefix}: {request_content[:100]}",
            "body": request_content,
            "request": request_content[:300],
            "entity_focus": entity_cue,
            "workflow": workflow.name,
        }
        questions = {
            "action": {
                "type": "choice",
                "instructions": f"Which action in the {workflow.name} workflow best fulfills this request, or should it be clarified or abstained?",
                "criteria": criteria,
            }
        }

        try:
            result = self._router.predict(state, questions)
            elapsed_ms = (time.perf_counter() - start_time) * 1000

            ans = result.get("answers", {}).get("action", {})
            chosen_action_id = ans.get("choice")
            probabilities = ans.get("probabilities", {})
            confidence = ans.get("answer_confidence")
            if confidence is None:
                confidence = probabilities.get(chosen_action_id, ans.get("confidence", 0.85))

            if chosen_action_id == "abstain":
                return ActionDecision(
                    request_id=request_id,
                    workflow_name=workflow.name,
                    action_id="none",
                    outcome=DecisionOutcome.ABSTAIN,
                    confidence=float(confidence),
                    reasoning=f"Laya determined request is out-of-scope/unauthorized (prob={confidence:.4f})",
                    decision_model=self.name,
                    decision_latency_ms=elapsed_ms,
                )

            if chosen_action_id == "clarify":
                return ActionDecision(
                    request_id=request_id,
                    workflow_name=workflow.name,
                    action_id="none",
                    outcome=DecisionOutcome.CLARIFY,
                    confidence=float(confidence),
                    reasoning=f"Laya determined request requires clarification (prob={confidence:.4f})",
                    decision_model=self.name,
                    decision_latency_ms=elapsed_ms,
                )

            chosen_action = workflow.get_action(chosen_action_id)
            if chosen_action is None:
                logger.warning("Laya selected unknown action_id: %s", chosen_action_id)
                return ActionDecision(
                    request_id=request_id,
                    workflow_name=workflow.name,
                    action_id=chosen_action_id or "unknown",
                    outcome=DecisionOutcome.FALLBACK,
                    confidence=0.0,
                    reasoning=f"Laya proposed unknown action '{chosen_action_id}'",
                    decision_model=self.name,
                    decision_latency_ms=elapsed_ms,
                )

            outcome = (
                DecisionOutcome.USE_GENERATIVE_MODEL
                if chosen_action.allows_generative
                else DecisionOutcome.EXECUTE_TOOL
            )

            return ActionDecision(
                request_id=request_id,
                workflow_name=workflow.name,
                action_id=chosen_action.action_id,
                outcome=outcome,
                confidence=float(confidence),
                reasoning=f"Laya selected action '{chosen_action.action_id}' (prob={confidence:.4f})",
                requires_approval=chosen_action.requires_approval,
                decision_model=self.name,
                decision_latency_ms=elapsed_ms,
            )
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.error("Laya action prediction failed: %s", e)
            return ActionDecision(
                request_id=request_id,
                workflow_name=workflow.name,
                action_id="error",
                outcome=DecisionOutcome.FALLBACK,
                confidence=0.0,
                reasoning=f"Laya prediction error: {e}",
                decision_model=self.name,
                decision_latency_ms=elapsed_ms,
            )
