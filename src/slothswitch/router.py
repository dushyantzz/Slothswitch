"""Core routing engine — orchestrates the full decision pipeline.

Pipeline steps:
1. Validate input
2. Apply deterministic checks
3. Extract routing features
4. Ask the decision model
5. Validate via policy gate
6. Dispatch to task model
7. Validate output
8. Record outcome
"""

from __future__ import annotations

import logging
import time

from slothswitch.adapters import DecisionAdapter, TaskModelAdapter
from slothswitch.policy import RoutingPolicy
from slothswitch.preprocessing import (
    ValidationError,
    extract_features,
    validate_request,
)
from slothswitch.schemas import (
    RouteCategory,
    RouteDecision,
    RoutingRecord,
    RoutingRequest,
    TaskResult,
)
from slothswitch.telemetry import TelemetryRecorder

logger = logging.getLogger(__name__)


class SlothSwitchRouter:
    """The main routing engine that ties together preprocessing, decision, policy, and task execution."""

    def __init__(
        self,
        decision_adapter: DecisionAdapter,
        task_adapters: dict[RouteCategory, TaskModelAdapter],
        policy: RoutingPolicy,
        telemetry: TelemetryRecorder | None = None,
        max_request_length: int = 10_000,
        supported_content_types: list[str] | None = None,
        include_redacted_summary: bool = True,
        baseline_mode: bool = False,
        baseline_route: RouteCategory = RouteCategory.LARGE_LLM,
    ) -> None:
        self.decision_adapter = decision_adapter
        self.task_adapters = task_adapters
        self.policy = policy
        self.telemetry = telemetry or TelemetryRecorder()
        self.max_request_length = max_request_length
        self.supported_content_types = supported_content_types or ["text/plain"]
        self.include_redacted_summary = include_redacted_summary
        self.baseline_mode = baseline_mode
        self.baseline_route = baseline_route

    def process(self, request: RoutingRequest) -> RoutingRecord:
        """Run the full routing pipeline for a single request.

        Returns a RoutingRecord containing the route decision and task result.
        """
        pipeline_start = time.perf_counter()

        # Step 1: Validate input
        try:
            validate_request(
                request,
                max_length=self.max_request_length,
                supported_content_types=self.supported_content_types,
            )
        except ValidationError as e:
            decision = RouteDecision(
                request_id=request.request_id,
                chosen_route=RouteCategory.FALLBACK,
                confidence=0.0,
                reasoning=f"Input validation failed: {e}",
                accepted=False,
                fallback_reason=str(e),
            )
            record = RoutingRecord(request_id=request.request_id, route_decision=decision)
            self.telemetry.record(record)
            return record

        # Step 2: Extract routing features
        features = extract_features(
            request,
            include_redacted_summary=self.include_redacted_summary,
        )

        # Step 3: Get available routes
        available_routes = [
            rc for rc in RouteCategory if rc in self.policy.enabled_routes
        ]

        # Step 4: Decision
        decision_start = time.perf_counter()
        if self.baseline_mode:
            # Baseline: always use the configured baseline route
            decision_model_ms = (time.perf_counter() - decision_start) * 1000
            decision = RouteDecision(
                request_id=request.request_id,
                chosen_route=self.baseline_route,
                confidence=1.0,
                reasoning="Baseline mode — all requests use the same route",
                decision_model="baseline",
                decision_latency_ms=decision_model_ms,
            )
        else:
            # Ask the decision model
            try:
                decision = self.decision_adapter.predict_route(
                    request, features, available_routes
                )
                decision_model_ms = (time.perf_counter() - decision_start) * 1000
                if decision.decision_latency_ms is None:
                    decision.decision_latency_ms = decision_model_ms
            except Exception as e:
                decision_model_ms = (time.perf_counter() - decision_start) * 1000
                logger.error("Decision adapter failed: %s", e)
                decision = RouteDecision(
                    request_id=request.request_id,
                    chosen_route=RouteCategory.FALLBACK,
                    confidence=0.0,
                    reasoning=f"Decision adapter error: {e}",
                    fallback_reason=f"Decision adapter error: {e}",
                    decision_latency_ms=decision_model_ms,
                )

        # Step 5: Policy validation
        decision = self.policy.validate_and_apply(
            decision, request, category_hints=features.category_hints
        )

        routing_phase_ms = (time.perf_counter() - pipeline_start) * 1000
        decision.latency_ms = routing_phase_ms
        dec_lat = decision.decision_latency_ms or 0.0
        decision.router_overhead_ms = max(0.0, routing_phase_ms - dec_lat)

        # Step 6: Dispatch to task model
        task_start = time.perf_counter()
        task_result: TaskResult | None = None
        adapter = self.task_adapters.get(decision.chosen_route)
        if adapter is not None:
            try:
                task_result = adapter.execute(request, decision.chosen_route)
            except Exception as e:
                task_elapsed = (time.perf_counter() - task_start) * 1000
                logger.error("Task adapter failed for route %s: %s", decision.chosen_route, e)
                task_result = TaskResult(
                    request_id=request.request_id,
                    route_used=decision.chosen_route,
                    output="",
                    success=False,
                    error=str(e),
                    latency_ms=task_elapsed,
                )
        else:
            logger.warning("No task adapter for route %s", decision.chosen_route)

        total_e2e_ms = (time.perf_counter() - pipeline_start) * 1000

        # Step 7: Record outcome
        record = RoutingRecord(
            request_id=request.request_id,
            route_decision=decision,
            task_result=task_result,
            total_e2e_latency_ms=total_e2e_ms,
        )
        self.telemetry.record(record)

        return record

