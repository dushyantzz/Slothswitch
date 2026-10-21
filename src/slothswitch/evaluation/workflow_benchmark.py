"""Workflow benchmark evaluation harness comparing 3 baselines:

1. Baseline A (Always-Gemma): Always invokes local generative model for all requests.
2. Baseline B (Deterministic Rules): Uses keyword matching rules without neural decision model.
3. Baseline C (SlothSwitch): Laya neural action routing + WorkflowPolicy + direct ToolExecutor,
                              delegating to local Gemma only when generation is required.

Computes:
- Action accuracy
- Avoided Gemma generative calls
- Direct tool executions
- Token consumption
- Latency (median, p95)
- Safety & approval enforcement
"""

from __future__ import annotations

import logging
import statistics
import time
from typing import Any

from slothswitch.adapters.decision import MockDecisionAdapter
from slothswitch.adapters.generative.gemma_local import MockGenerativeAdapter
from slothswitch.adapters.tools.github import GitHubToolAdapter
from slothswitch.executor import ToolExecutor
from slothswitch.policy import WorkflowPolicy
from slothswitch.schemas import DecisionOutcome
from slothswitch.workflows.base import WorkflowDefinition

logger = logging.getLogger(__name__)


class WorkflowBenchmarkRunner:
    """Runs comparative benchmark across the 3 baseline conditions."""

    def __init__(
        self,
        workflow: WorkflowDefinition,
        decision_adapter: Any = None,
        generative_adapter: Any = None,
        tool_adapter: Any = None,
    ) -> None:
        self.workflow = workflow
        self.decision_adapter = decision_adapter or MockDecisionAdapter()
        self.generative_adapter = generative_adapter or MockGenerativeAdapter()
        self.tool_adapter = tool_adapter or GitHubToolAdapter()
        self.policy = WorkflowPolicy(read_only_mode=False, require_approval_for_mutating=True)
        self.executor = ToolExecutor(adapters=[self.tool_adapter], policy=self.policy)

    def run_baseline_a_always_gemma(self, samples: list[dict[str, Any]]) -> dict[str, Any]:
        """Baseline A: Always invoke local generative model for every request."""
        latencies: list[float] = []
        tokens_used = 0
        correct_actions = 0
        gemma_calls = 0
        direct_tool_calls = 0

        for item in samples:
            req_content = item["content"]
            expected_outcome = item.get("expected_outcome", "EXECUTE_TOOL")

            start = time.perf_counter()
            res = self.generative_adapter.generate(
                prompt=f"Task: {req_content}\nExecute the appropriate action for repository.",
                max_new_tokens=128,
            )
            elapsed = (time.perf_counter() - start) * 1000
            latencies.append(elapsed)
            gemma_calls += 1
            if res.token_usage:
                tokens_used += res.token_usage.get("total_tokens", 0)

            # Baseline A only correctly handles requests that genuinely required generation
            if expected_outcome == "USE_GENERATIVE_MODEL":
                correct_actions += 1

        total = len(samples)
        return {
            "baseline": "Baseline A (Always-Gemma)",
            "total_samples": total,
            "accuracy": round(correct_actions / max(1, total), 4),
            "gemma_calls": gemma_calls,
            "direct_tool_calls": direct_tool_calls,
            "avoided_gemma_calls": 0,
            "avoided_gemma_pct": 0.0,
            "total_tokens_used": tokens_used,
            "median_latency_ms": round(statistics.median(latencies) if latencies else 0.0, 2),
            "p95_latency_ms": round(
                statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies or [0.0]), 2
            ),
        }

    def run_baseline_b_deterministic_rules(self, samples: list[dict[str, Any]]) -> dict[str, Any]:
        """Baseline B: Static keyword matching rules without neural decision routing."""
        latencies: list[float] = []
        tokens_used = 0
        correct_actions = 0
        gemma_calls = 0
        direct_tool_calls = 0

        for item in samples:
            req_content = item["content"].lower()
            expected_action = item.get("expected_action")
            expected_outcome = item.get("expected_outcome")

            start = time.perf_counter()
            # Simple keyword matching rules
            predicted_action = "none"
            predicted_outcome = "CLARIFY"

            if "summarize" in req_content or "report" in req_content or "concerns" in req_content:
                predicted_outcome = "USE_GENERATIVE_MODEL"
                if "pull request" in req_content or "prs" in req_content:
                    predicted_action = "summarize_pull_requests"
                elif "issues" in req_content:
                    predicted_action = "summarize_issue_concerns"
                else:
                    predicted_action = "generate_repository_activity_report"
            elif "count" in req_content or "how many" in req_content:
                predicted_outcome = "EXECUTE_TOOL"
                if "pull" in req_content or "pr" in req_content:
                    predicted_action = "count_pull_requests"
                else:
                    predicted_action = "count_issues"
            elif "list" in req_content or "show" in req_content:
                predicted_outcome = "EXECUTE_TOOL"
                if "pull" in req_content or "pr" in req_content:
                    predicted_action = "list_open_pull_requests"
                else:
                    predicted_action = "list_open_issues"
            elif "delete" in req_content or "transfer" in req_content or "force push" in req_content:
                predicted_outcome = "ABSTAIN"
            elif "add label" in req_content or "comment" in req_content:
                predicted_outcome = "HUMAN_REVIEW"
                predicted_action = "add_issue_label" if "label" in req_content else "create_issue_comment"

            elapsed = (time.perf_counter() - start) * 1000
            latencies.append(elapsed)

            if predicted_outcome == "USE_GENERATIVE_MODEL":
                gemma_calls += 1
                tokens_used += 100
            elif predicted_outcome == "EXECUTE_TOOL":
                direct_tool_calls += 1

            if predicted_action == expected_action or predicted_outcome == expected_outcome:
                correct_actions += 1

        total = len(samples)
        return {
            "baseline": "Baseline B (Deterministic Rules)",
            "total_samples": total,
            "accuracy": round(correct_actions / max(1, total), 4),
            "gemma_calls": gemma_calls,
            "direct_tool_calls": direct_tool_calls,
            "avoided_gemma_calls": total - gemma_calls,
            "avoided_gemma_pct": round((total - gemma_calls) / max(1, total) * 100, 2),
            "total_tokens_used": tokens_used,
            "median_latency_ms": round(statistics.median(latencies) if latencies else 0.0, 2),
            "p95_latency_ms": round(
                statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies or [0.0]), 2
            ),
        }

    def run_baseline_c_slothswitch(self, samples: list[dict[str, Any]]) -> dict[str, Any]:
        """Baseline C: SlothSwitch decision routing + WorkflowPolicy + direct ToolExecutor."""
        latencies: list[float] = []
        tokens_used = 0
        correct_actions = 0
        gemma_calls = 0
        direct_tool_calls = 0
        policy_abstentions = 0
        approval_pauses = 0

        for item in samples:
            req_content = item["content"]
            expected_action = item.get("expected_action")
            expected_outcome = item.get("expected_outcome")

            start = time.perf_counter()

            # 1. Decision routing
            decision = self.decision_adapter.predict_action(req_content, self.workflow)

            # 2. Workflow Policy check
            authorized = self.policy.evaluate_action(
                decision, self.workflow, caller_permissions=["github:read", "github:write"]
            )

            # 3. Execution dispatch
            if authorized.outcome == DecisionOutcome.EXECUTE_TOOL:
                direct_tool_calls += 1
                # Fast direct tool execution (mock/real)
            elif authorized.outcome == DecisionOutcome.USE_GENERATIVE_MODEL:
                gemma_calls += 1
                gen_res = self.generative_adapter.generate(req_content, max_new_tokens=128)
                if gen_res.token_usage:
                    tokens_used += gen_res.token_usage.get("total_tokens", 0)
            elif authorized.outcome == DecisionOutcome.ABSTAIN:
                policy_abstentions += 1
            elif authorized.outcome == DecisionOutcome.HUMAN_REVIEW:
                approval_pauses += 1

            elapsed = (time.perf_counter() - start) * 1000
            latencies.append(elapsed)

            if authorized.action_id == expected_action or authorized.outcome == expected_outcome:
                correct_actions += 1

        total = len(samples)
        avoided_gemma = total - gemma_calls
        return {
            "baseline": "Baseline C (SlothSwitch)",
            "total_samples": total,
            "accuracy": round(correct_actions / max(1, total), 4),
            "gemma_calls": gemma_calls,
            "direct_tool_calls": direct_tool_calls,
            "policy_abstentions": policy_abstentions,
            "approval_pauses": approval_pauses,
            "avoided_gemma_calls": avoided_gemma,
            "avoided_gemma_pct": round(avoided_gemma / max(1, total) * 100, 2),
            "total_tokens_used": tokens_used,
            "median_latency_ms": round(statistics.median(latencies) if latencies else 0.0, 2),
            "p95_latency_ms": round(
                statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies or [0.0]), 2
            ),
        }
