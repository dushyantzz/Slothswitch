"""Workflow benchmark evaluation harness with strict metric verification.

Compares 3 baselines:
1. Baseline A (Always-Gemma): Invokes generative model for all requests.
2. Baseline B (Deterministic Rules): Uses keyword matching heuristics.
3. Baseline C (SlothSwitch): Neural Laya routing + WorkflowPolicy + direct ToolExecutor,
                              delegating to local Gemma only when generation is required.

Strictly separates:
- Action accuracy (strict exact match) vs Outcome accuracy vs End-to-end task success
- Direct tools selected vs attempted vs succeeded vs failed
- Latencies: decision, policy, tool, generative, and total end-to-end
- Real vs. simulated measurements
- Complete per-sample machine-readable audit records
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
    """Runs comparative benchmark across the 3 baseline conditions with rigorous accounting."""

    def __init__(
        self,
        workflow: WorkflowDefinition,
        decision_adapter: Any = None,
        generative_adapter: Any = None,
        tool_adapter: Any = None,
        policy: WorkflowPolicy | None = None,
        execute_live_tools: bool = False,
    ) -> None:
        self.workflow = workflow
        self.decision_adapter = decision_adapter or MockDecisionAdapter()
        self.generative_adapter = generative_adapter or MockGenerativeAdapter()
        self.tool_adapter = tool_adapter or GitHubToolAdapter()
        self.policy = policy or WorkflowPolicy(read_only_mode=False, require_approval_for_mutating=True)
        self.executor = ToolExecutor(adapters=[self.tool_adapter], policy=self.policy)
        self.execute_live_tools = execute_live_tools

    @property
    def is_real_inference(self) -> bool:
        """Return True if using live real neural models instead of mock adapters."""
        dec_is_real = not isinstance(self.decision_adapter, MockDecisionAdapter)
        gen_is_real = not isinstance(self.generative_adapter, MockGenerativeAdapter)
        return dec_is_real or gen_is_real

    def run_baseline_a_always_gemma(self, samples: list[dict[str, Any]]) -> dict[str, Any]:
        """Baseline A: Always invoke generative model for every request."""
        latencies: list[float] = []
        gen_tokens_list: list[int] = []
        detailed_records: list[dict[str, Any]] = []

        action_correct_count = 0
        outcome_correct_count = 0
        task_success_count = 0

        for item in samples:
            req_id = item["request_id"]
            req_content = item["content"]
            expected_action = item.get("expected_action", "none")
            expected_outcome = item.get("expected_outcome", "EXECUTE_TOOL")

            start = time.perf_counter()
            gen_res = self.generative_adapter.generate(
                prompt=f"Task: {req_content}\nExecute the appropriate action for repository.",
                max_new_tokens=128,
            )
            elapsed_ms = (time.perf_counter() - start) * 1000
            latencies.append(elapsed_ms)

            tokens = gen_res.token_usage.get("total_tokens", 0) if gen_res.token_usage else 0
            gen_tokens_list.append(tokens)

            # Always-Gemma treats all queries as generation
            predicted_outcome = DecisionOutcome.USE_GENERATIVE_MODEL.value
            # It generates text; it does not output a structured tool action ID
            predicted_action = "generative_text_response"

            is_action_match = (predicted_action == expected_action)
            is_outcome_match = (predicted_outcome == expected_outcome)
            is_task_success = is_outcome_match and gen_res.success

            if is_action_match:
                action_correct_count += 1
            if is_outcome_match:
                outcome_correct_count += 1
            if is_task_success:
                task_success_count += 1

            detailed_records.append({
                "request_id": req_id,
                "content": req_content,
                "expected_action": expected_action,
                "predicted_action": predicted_action,
                "action_match": is_action_match,
                "expected_outcome": expected_outcome,
                "predicted_outcome": predicted_outcome,
                "outcome_match": is_outcome_match,
                "task_success": is_task_success,
                "latencies_ms": {
                    "decision": 0.0,
                    "policy": 0.0,
                    "tool": 0.0,
                    "generative": elapsed_ms,
                    "total_e2e": elapsed_ms,
                },
                "tokens": {
                    "decision_tokens": 0,
                    "generative_tokens": tokens,
                    "total_tokens": tokens,
                },
                "model_used": self.generative_adapter.name,
                "error": None,
            })

        total = len(samples)
        return {
            "baseline": "Baseline A (Always-Gemma)",
            "total_samples": total,
            "is_real_inference": not isinstance(self.generative_adapter, MockGenerativeAdapter),
            "action_accuracy": round(action_correct_count / max(1, total), 4),
            "outcome_accuracy": round(outcome_correct_count / max(1, total), 4),
            "end_to_end_task_success_rate": round(task_success_count / max(1, total), 4),
            "gemma_calls": total,
            "direct_tools_selected": 0,
            "direct_tools_attempted": 0,
            "direct_tools_succeeded": 0,
            "direct_tools_failed": 0,
            "avoided_gemma_calls": 0,
            "avoided_gemma_pct": 0.0,
            "total_generative_tokens": sum(gen_tokens_list),
            "median_total_latency_ms": round(statistics.median(latencies) if latencies else 0.0, 2),
            "p95_total_latency_ms": round(
                statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies or [0.0]), 2
            ),
            "records": detailed_records,
        }

    def run_baseline_b_deterministic_rules(self, samples: list[dict[str, Any]]) -> dict[str, Any]:
        """Baseline B: Static keyword matching heuristics without neural decision routing."""
        latencies: list[float] = []
        gen_tokens_list: list[int] = []
        detailed_records: list[dict[str, Any]] = []

        action_correct_count = 0
        outcome_correct_count = 0
        task_success_count = 0
        gemma_calls = 0
        tools_selected = 0
        tools_attempted = 0
        tools_succeeded = 0
        tools_failed = 0

        for item in samples:
            req_id = item["request_id"]
            req_content = item["content"]
            lower_req = req_content.lower()
            expected_action = item.get("expected_action", "none")
            expected_outcome = item.get("expected_outcome", "EXECUTE_TOOL")

            start = time.perf_counter()
            predicted_action = "none"
            predicted_outcome = DecisionOutcome.CLARIFY.value

            # Keyword matching rules
            if "summarize" in lower_req or "report" in lower_req or "concerns" in lower_req:
                predicted_outcome = DecisionOutcome.USE_GENERATIVE_MODEL.value
                if "pull request" in lower_req or "prs" in lower_req or "pr " in lower_req:
                    predicted_action = "summarize_pull_requests"
                elif "issues" in lower_req or "issue " in lower_req:
                    predicted_action = "summarize_issue_concerns"
                else:
                    predicted_action = "generate_repository_activity_report"
            elif "count" in lower_req or "how many" in lower_req:
                predicted_outcome = DecisionOutcome.EXECUTE_TOOL.value
                if "pull" in lower_req or "pr" in lower_req:
                    predicted_action = "count_pull_requests"
                else:
                    predicted_action = "count_issues"
            elif "list" in lower_req or "show" in lower_req or "top " in lower_req:
                predicted_outcome = DecisionOutcome.EXECUTE_TOOL.value
                if "pull" in lower_req or "pr" in lower_req:
                    predicted_action = "list_open_pull_requests"
                elif "issues" in lower_req or "issue" in lower_req:
                    predicted_action = "list_open_issues"
                else:
                    predicted_action = "list_repository_labels"
            elif "details" in lower_req or "status" in lower_req:
                predicted_outcome = DecisionOutcome.EXECUTE_TOOL.value
                if "pull" in lower_req or "pr" in lower_req:
                    predicted_action = "get_pull_request_details"
                else:
                    predicted_action = "get_issue_details"
            elif "checks" in lower_req or "ci " in lower_req:
                predicted_outcome = DecisionOutcome.EXECUTE_TOOL.value
                predicted_action = "get_pull_request_checks"
            elif "delete" in lower_req or "transfer" in lower_req or "force push" in lower_req or "charge" in lower_req:
                predicted_outcome = DecisionOutcome.ABSTAIN.value
                predicted_action = "none"
            elif "add label" in lower_req or "comment" in lower_req:
                predicted_outcome = DecisionOutcome.HUMAN_REVIEW.value
                predicted_action = "add_issue_label" if "issue" in lower_req else "add_pull_request_label"

            rule_elapsed_ms = (time.perf_counter() - start) * 1000
            gen_elapsed_ms = 0.0
            tool_elapsed_ms = 0.0
            tokens = 0
            execution_success = True
            error_msg = None

            if predicted_outcome == DecisionOutcome.USE_GENERATIVE_MODEL.value:
                gemma_calls += 1
                g_start = time.perf_counter()
                gen_res = self.generative_adapter.generate(req_content, max_new_tokens=128)
                gen_elapsed_ms = (time.perf_counter() - g_start) * 1000
                if gen_res.token_usage:
                    tokens = gen_res.token_usage.get("total_tokens", 0)
                execution_success = gen_res.success
            elif predicted_outcome == DecisionOutcome.EXECUTE_TOOL.value:
                tools_selected += 1
                if self.execute_live_tools:
                    tools_attempted += 1
                    t_start = time.perf_counter()
                    t_res = self.executor.execute(
                        workflow=self.workflow,
                        action_id=predicted_action,
                        params=item.get("expected_parameters", {}),
                        caller_permissions=["github:read"],
                    )
                    tool_elapsed_ms = (time.perf_counter() - t_start) * 1000
                    execution_success = t_res.success
                    if not t_res.success:
                        tools_failed += 1
                        error_msg = t_res.error
                    else:
                        tools_succeeded += 1

            total_e2e_ms = rule_elapsed_ms + gen_elapsed_ms + tool_elapsed_ms
            latencies.append(total_e2e_ms)
            gen_tokens_list.append(tokens)

            is_action_match = (predicted_action == expected_action)
            is_outcome_match = (predicted_outcome == expected_outcome)
            is_task_success = is_action_match and is_outcome_match and execution_success

            if is_action_match:
                action_correct_count += 1
            if is_outcome_match:
                outcome_correct_count += 1
            if is_task_success:
                task_success_count += 1

            detailed_records.append({
                "request_id": req_id,
                "content": req_content,
                "expected_action": expected_action,
                "predicted_action": predicted_action,
                "action_match": is_action_match,
                "expected_outcome": expected_outcome,
                "predicted_outcome": predicted_outcome,
                "outcome_match": is_outcome_match,
                "task_success": is_task_success,
                "latencies_ms": {
                    "decision": rule_elapsed_ms,
                    "policy": 0.0,
                    "tool": tool_elapsed_ms,
                    "generative": gen_elapsed_ms,
                    "total_e2e": total_e2e_ms,
                },
                "tokens": {
                    "decision_tokens": 0,
                    "generative_tokens": tokens,
                    "total_tokens": tokens,
                },
                "model_used": "deterministic_rules",
                "error": error_msg,
            })

        total = len(samples)
        return {
            "baseline": "Baseline B (Deterministic Rules)",
            "total_samples": total,
            "is_real_inference": False,
            "action_accuracy": round(action_correct_count / max(1, total), 4),
            "outcome_accuracy": round(outcome_correct_count / max(1, total), 4),
            "end_to_end_task_success_rate": round(task_success_count / max(1, total), 4),
            "gemma_calls": gemma_calls,
            "direct_tools_selected": tools_selected,
            "direct_tools_attempted": tools_attempted,
            "direct_tools_succeeded": tools_succeeded,
            "direct_tools_failed": tools_failed,
            "avoided_gemma_calls": total - gemma_calls,
            "avoided_gemma_pct": round((total - gemma_calls) / max(1, total) * 100, 2),
            "total_generative_tokens": sum(gen_tokens_list),
            "median_total_latency_ms": round(statistics.median(latencies) if latencies else 0.0, 2),
            "p95_total_latency_ms": round(
                statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies or [0.0]), 2
            ),
            "records": detailed_records,
        }

    def run_baseline_c_slothswitch(self, samples: list[dict[str, Any]]) -> dict[str, Any]:
        """Baseline C: SlothSwitch (Laya Decision + Policy Gate + Direct ToolExecutor + Local Gemma)."""
        latencies: list[float] = []
        decision_latencies: list[float] = []
        policy_latencies: list[float] = []
        tool_latencies: list[float] = []
        gen_latencies: list[float] = []
        gen_tokens_list: list[int] = []
        detailed_records: list[dict[str, Any]] = []

        action_correct_count = 0
        outcome_correct_count = 0
        task_success_count = 0
        gemma_calls = 0
        tools_selected = 0
        tools_attempted = 0
        tools_succeeded = 0
        tools_failed = 0
        policy_abstentions = 0
        approval_pauses = 0

        for item in samples:
            req_id = item["request_id"]
            req_content = item["content"]
            expected_action = item.get("expected_action", "none")
            expected_outcome = item.get("expected_outcome", "EXECUTE_TOOL")

            start_e2e = time.perf_counter()

            # 1. Decision routing via DecisionAdapter (Laya or Mock)
            decision = self.decision_adapter.predict_action(req_content, self.workflow)
            d_latency = decision.decision_latency_ms or 0.0
            decision_latencies.append(d_latency)

            # 2. Workflow Policy Gate
            p_start = time.perf_counter()
            authorized = self.policy.evaluate_action(
                decision, self.workflow, caller_permissions=["github:read", "github:write"]
            )
            p_latency = (time.perf_counter() - p_start) * 1000
            policy_latencies.append(p_latency)

            # 3. Execution Dispatch
            t_latency = 0.0
            g_latency = 0.0
            tokens = 0
            execution_success = True
            error_msg = None

            if authorized.outcome == DecisionOutcome.EXECUTE_TOOL:
                tools_selected += 1
                if self.execute_live_tools:
                    tools_attempted += 1
                    t_start = time.perf_counter()
                    t_res = self.executor.execute(
                        workflow=self.workflow,
                        action_id=authorized.action_id,
                        params=item.get("expected_parameters", {}),
                        caller_permissions=["github:read"],
                    )
                    t_latency = (time.perf_counter() - t_start) * 1000
                    execution_success = t_res.success
                    if not t_res.success:
                        tools_failed += 1
                        error_msg = t_res.error
                    else:
                        tools_succeeded += 1

            elif authorized.outcome == DecisionOutcome.USE_GENERATIVE_MODEL:
                gemma_calls += 1
                g_start = time.perf_counter()
                gen_res = self.generative_adapter.generate(req_content, max_new_tokens=128)
                g_latency = (time.perf_counter() - g_start) * 1000
                if gen_res.token_usage:
                    tokens = gen_res.token_usage.get("total_tokens", 0)
                execution_success = gen_res.success

            elif authorized.outcome == DecisionOutcome.ABSTAIN:
                policy_abstentions += 1
                execution_success = (expected_outcome == DecisionOutcome.ABSTAIN.value)

            elif authorized.outcome == DecisionOutcome.HUMAN_REVIEW:
                approval_pauses += 1
                # Intercepted safely by approval gate
                execution_success = (expected_outcome == DecisionOutcome.HUMAN_REVIEW.value)

            tool_latencies.append(t_latency)
            gen_latencies.append(g_latency)
            gen_tokens_list.append(tokens)

            total_elapsed_ms = (time.perf_counter() - start_e2e) * 1000
            latencies.append(total_elapsed_ms)

            # Strict correctness metrics
            is_action_match = (authorized.action_id == expected_action)
            is_outcome_match = (authorized.outcome.value == expected_outcome)
            is_task_success = (
                is_action_match and is_outcome_match and execution_success
                if expected_outcome in (DecisionOutcome.EXECUTE_TOOL.value, DecisionOutcome.USE_GENERATIVE_MODEL.value)
                else is_outcome_match
            )

            if is_action_match:
                action_correct_count += 1
            if is_outcome_match:
                outcome_correct_count += 1
            if is_task_success:
                task_success_count += 1

            detailed_records.append({
                "request_id": req_id,
                "content": req_content,
                "expected_action": expected_action,
                "predicted_action": authorized.action_id,
                "action_match": is_action_match,
                "expected_outcome": expected_outcome,
                "predicted_outcome": authorized.outcome.value,
                "outcome_match": is_outcome_match,
                "confidence": authorized.confidence,
                "task_success": is_task_success,
                "latencies_ms": {
                    "decision": round(d_latency, 2),
                    "policy": round(p_latency, 3),
                    "tool": round(t_latency, 2),
                    "generative": round(g_latency, 2),
                    "total_e2e": round(total_elapsed_ms, 2),
                },
                "tokens": {
                    "decision_tokens": 0,
                    "generative_tokens": tokens,
                    "total_tokens": tokens,
                },
                "model_used": self.decision_adapter.name,
                "error": error_msg,
            })

        total = len(samples)
        avoided_gemma = total - gemma_calls
        return {
            "baseline": "Baseline C (SlothSwitch)",
            "total_samples": total,
            "is_real_inference": self.is_real_inference,
            "decision_model": self.decision_adapter.name,
            "generative_model": self.generative_adapter.name,
            "action_accuracy": round(action_correct_count / max(1, total), 4),
            "outcome_accuracy": round(outcome_correct_count / max(1, total), 4),
            "end_to_end_task_success_rate": round(task_success_count / max(1, total), 4),
            "gemma_calls": gemma_calls,
            "direct_tools_selected": tools_selected,
            "direct_tools_attempted": tools_attempted,
            "direct_tools_succeeded": tools_succeeded,
            "direct_tools_failed": tools_failed,
            "policy_abstentions": policy_abstentions,
            "approval_pauses": approval_pauses,
            "avoided_gemma_calls": avoided_gemma,
            "avoided_gemma_pct": round(avoided_gemma / max(1, total) * 100, 2),
            "total_generative_tokens": sum(gen_tokens_list),
            "median_total_latency_ms": round(statistics.median(latencies) if latencies else 0.0, 2),
            "p95_total_latency_ms": round(
                statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies or [0.0]), 2
            ),
            "median_decision_latency_ms": round(statistics.median(decision_latencies) if decision_latencies else 0.0, 2),
            "median_policy_latency_ms": round(statistics.median(policy_latencies) if policy_latencies else 0.0, 3),
            "records": detailed_records,
        }
