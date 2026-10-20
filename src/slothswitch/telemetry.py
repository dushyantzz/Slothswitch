"""Privacy-aware structured telemetry for SlothSwitch.

Records routing decisions and outcomes WITHOUT logging raw prompts by default.
Supports opt-in diagnostic samples for debugging.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Optional

from slothswitch.schemas import RoutingRecord

logger = logging.getLogger(__name__)


class TelemetryRecorder:
    """Records routing decisions and task outcomes as structured JSONL.

    Privacy defaults:
    - Raw request text is NEVER included unless `log_raw_prompts=True`
    - Only route metadata, timing, and cost information are recorded
    """

    def __init__(
        self,
        output_path: Optional[str] = None,
        enabled: bool = True,
        log_raw_prompts: bool = False,
    ) -> None:
        self.enabled = enabled
        self.log_raw_prompts = log_raw_prompts
        self.output_path = output_path
        self._records: list[dict] = []

        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    def record(self, routing_record: RoutingRecord) -> None:
        """Record a routing outcome."""
        if not self.enabled:
            return

        entry = {
            "request_id": routing_record.request_id,
            "timestamp": routing_record.timestamp,
            "route": routing_record.route_decision.chosen_route.value,
            "confidence": routing_record.route_decision.confidence,
            "accepted": routing_record.route_decision.accepted,
            "fallback_reason": routing_record.route_decision.fallback_reason,
            "decision_model": routing_record.route_decision.decision_model,
            "decision_latency_ms": routing_record.route_decision.latency_ms,
        }

        if routing_record.task_result:
            tr = routing_record.task_result
            entry.update({
                "task_success": tr.success,
                "task_error": tr.error,
                "task_model": tr.model_used,
                "task_latency_ms": tr.latency_ms,
                "token_usage": tr.token_usage,
                "estimated_cost_usd": tr.estimated_cost_usd,
            })

        if routing_record.config_version:
            entry["config_version"] = routing_record.config_version

        self._records.append(entry)

        # Write to file if configured
        if self.output_path:
            try:
                with open(self.output_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry) + "\n")
            except OSError as e:
                logger.warning("Failed to write telemetry: %s", e)

    def get_records(self) -> list[dict]:
        """Return all in-memory records (for testing and evaluation)."""
        return list(self._records)

    def summary(self) -> dict:
        """Return aggregate summary statistics."""
        if not self._records:
            return {"total_requests": 0}

        total = len(self._records)
        routes = {}
        accepted = 0
        fallbacks = 0
        total_latency = 0.0

        for r in self._records:
            route = r.get("route", "UNKNOWN")
            routes[route] = routes.get(route, 0) + 1
            if r.get("accepted"):
                accepted += 1
            if route == "FALLBACK":
                fallbacks += 1
            if r.get("decision_latency_ms"):
                total_latency += r["decision_latency_ms"]

        return {
            "total_requests": total,
            "route_distribution": routes,
            "acceptance_rate": accepted / total if total else 0,
            "fallback_rate": fallbacks / total if total else 0,
            "avg_decision_latency_ms": total_latency / total if total else 0,
        }
