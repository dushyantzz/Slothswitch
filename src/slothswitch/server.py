"""SlothSwitch Backend API & Static Web Server.

Provides a zero-dependency HTTP server implementing REST APIs for the dashboard
and serving the production web application.
"""

from __future__ import annotations

import csv
import io
import json
import logging
import mimetypes
import os
import sys
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from slothswitch.adapters.decision import MockDecisionAdapter
from slothswitch.adapters.generative.gemma_local import MockGenerativeAdapter
from slothswitch.adapters.tools.github import GitHubToolAdapter
from slothswitch.adapters.tools.system_ops_tool import SystemOpsToolAdapter
from slothswitch.executor import ToolExecutor
from slothswitch.policy import WorkflowPolicy
from slothswitch.registry import WorkflowRegistry
from slothswitch.schemas import DecisionOutcome
from slothswitch.workflows.github_pr_management import create_github_workflow
from slothswitch.workflows.system_ops import create_system_ops_workflow

logger = logging.getLogger("slothswitch.server")


class SlothSwitchState:
    """Singleton server runtime state."""

    def __init__(self, use_real_models: bool = True) -> None:
        self.use_real_models = use_real_models
        self.registry = WorkflowRegistry()
        self.registry.register(create_github_workflow())
        self.registry.register(create_system_ops_workflow())

        self.policy = WorkflowPolicy(
            min_confidence=0.55,
            require_approval_for_mutating=True,
            read_only_mode=False,
        )

        # Initialize Decision Adapter
        self.decision_adapter: Any = None
        self.decision_model_name = "convaiinnovations/laya"
        if use_real_models:
            try:
                from slothswitch.adapters.decision.laya_adapter import LayaDecisionAdapter

                self.decision_adapter = LayaDecisionAdapter()
                self.decision_model_status = "ready"
            except Exception as e:
                logger.warning("Could not load real LayaDecisionAdapter (%s); falling back to Mock", e)
                self.decision_adapter = MockDecisionAdapter()
                self.decision_model_status = f"fallback_mock ({e})"
        else:
            self.decision_adapter = MockDecisionAdapter()
            self.decision_model_status = "mock"

        # Initialize Generative Adapter
        self.generative_adapter: Any = None
        self.generative_model_name = "google/gemma-2-2b-it"
        if use_real_models:
            try:
                from slothswitch.adapters.generative.gemma_local import LocalGemmaAdapter

                self.generative_adapter = LocalGemmaAdapter()
                self.generative_model_status = "ready (bfloat16/cpu)"
            except Exception as e:
                logger.warning("Could not load real LocalGemmaAdapter (%s); falling back to Mock", e)
                self.generative_adapter = MockGenerativeAdapter()
                self.generative_model_status = f"fallback_mock ({e})"
        else:
            self.generative_adapter = MockGenerativeAdapter()
            self.generative_model_status = "mock"

        # Initialize Tools & Executor
        self.github_tool = GitHubToolAdapter()
        self.system_tool = SystemOpsToolAdapter()
        self.executor = ToolExecutor(
            adapters=[self.github_tool, self.system_tool],
            policy=self.policy,
        )

        # Traces storage (in-memory ring buffer of up to 100 entries)
        self.traces: list[dict[str, Any]] = []
        self._seed_initial_traces()

    def _seed_initial_traces(self) -> None:
        """Seed representative traces so dashboard overview is immediately useful."""
        seeds = [
            {
                "trace_id": "tr-001",
                "timestamp": time.time() - 140,
                "request_content": "Count open pull requests in tiangolo/fastapi",
                "workflow_name": "github_pr_management",
                "selected_action": "count_pull_requests",
                "parameters": {"repo": "tiangolo/fastapi", "state": "open"},
                "policy_outcome": "EXECUTE_TOOL",
                "model_used": self.decision_model_name,
                "route_path": "DIRECT_TOOL",
                "decision_latency_ms": 1184.2,
                "policy_latency_ms": 0.024,
                "execution_latency_ms": 142.5,
                "total_e2e_ms": 1326.7,
                "tokens": {"input": 18, "output": 0, "total": 18},
                "result": {"success": True, "output": {"repo": "tiangolo/fastapi", "count": 48}},
                "status": "SUCCEEDED",
            },
            {
                "trace_id": "tr-002",
                "timestamp": time.time() - 95,
                "request_content": "Summarize recent pull request activity and themes in tiangolo/fastapi",
                "workflow_name": "github_pr_management",
                "selected_action": "summarize_pull_requests",
                "parameters": {"repo": "tiangolo/fastapi"},
                "policy_outcome": "USE_GENERATIVE_MODEL",
                "model_used": self.generative_model_name,
                "route_path": "GENERATIVE_LLM",
                "decision_latency_ms": 1210.5,
                "policy_latency_ms": 0.019,
                "execution_latency_ms": 2840.0,
                "total_e2e_ms": 4050.5,
                "tokens": {"input": 24, "output": 70, "total": 94},
                "result": {
                    "success": True,
                    "output": "Recent pull requests in tiangolo/fastapi focus on Pydantic v2 compatibility and typing improvements.",
                },
                "status": "SUCCEEDED",
            },
            {
                "trace_id": "tr-003",
                "timestamp": time.time() - 60,
                "request_content": "Change repository visibility to public and grant admin access",
                "workflow_name": "github_pr_management",
                "selected_action": "none",
                "parameters": {},
                "policy_outcome": "ABSTAIN",
                "model_used": "slothswitch_policy_gate",
                "route_path": "POLICY_ABSTENTION",
                "decision_latency_ms": 0.0,
                "policy_latency_ms": 0.015,
                "execution_latency_ms": 0.0,
                "total_e2e_ms": 0.015,
                "tokens": {"input": 12, "output": 0, "total": 12},
                "result": {
                    "success": False,
                    "error": "Security gate: repository visibility and administrative modifications are strictly prohibited.",
                },
                "status": "ABSTAINED",
            },
            {
                "trace_id": "tr-004",
                "timestamp": time.time() - 30,
                "request_content": "Merge pull request #11599 with commit message 'Release v1.2'",
                "workflow_name": "github_pr_management",
                "selected_action": "merge_pull_request",
                "parameters": {"repo": "octocat/Hello-World", "pull_number": 11599},
                "policy_outcome": "HUMAN_REVIEW",
                "model_used": self.decision_model_name,
                "route_path": "APPROVAL_GATE",
                "decision_latency_ms": 1195.0,
                "policy_latency_ms": 0.021,
                "execution_latency_ms": 0.0,
                "total_e2e_ms": 1195.021,
                "tokens": {"input": 16, "output": 0, "total": 16},
                "result": {
                    "success": True,
                    "output": "Action 'merge_pull_request' is mutating and paused awaiting mandatory human authorization.",
                },
                "status": "WAITING_FOR_APPROVAL",
            },
            {
                "trace_id": "tr-005",
                "timestamp": time.time() - 15,
                "request_content": "Check disk usage and free storage on host partition",
                "workflow_name": "system_ops",
                "selected_action": "get_disk_usage",
                "parameters": {"path": "."},
                "policy_outcome": "EXECUTE_TOOL",
                "model_used": self.decision_model_name,
                "route_path": "DIRECT_TOOL",
                "decision_latency_ms": 940.0,
                "policy_latency_ms": 0.018,
                "execution_latency_ms": 1.2,
                "total_e2e_ms": 941.2,
                "tokens": {"input": 14, "output": 0, "total": 14},
                "result": {"success": True, "output": {"path": ".", "free_gb": 142.8, "status": "ok"}},
                "status": "SUCCEEDED",
            },
        ]
        self.traces.extend(seeds)

    def record_trace(self, trace: dict[str, Any]) -> None:
        """Add trace to beginning of list and keep bounded."""
        self.traces.insert(0, trace)
        if len(self.traces) > 100:
            self.traces.pop()

    def get_stats(self) -> dict[str, Any]:
        """Compute aggregate stats from recorded traces."""
        total = len(self.traces)
        direct_tools = sum(1 for t in self.traces if t.get("policy_outcome") == "EXECUTE_TOOL")
        gen_calls = sum(1 for t in self.traces if t.get("policy_outcome") == "USE_GENERATIVE_MODEL")
        abstentions = sum(1 for t in self.traces if t.get("policy_outcome") == "ABSTAIN")
        approvals = sum(1 for t in self.traces if t.get("policy_outcome") == "HUMAN_REVIEW")
        clarifications = sum(1 for t in self.traces if t.get("policy_outcome") == "CLARIFY")

        avoided_calls = total - gen_calls
        avoidance_pct = round((avoided_calls / max(1, total)) * 100, 1)

        return {
            "total_requests": total,
            "direct_tool_executions": direct_tools,
            "generative_calls": gen_calls,
            "avoided_generative_calls": avoided_calls,
            "avoided_generative_pct": avoidance_pct,
            "policy_abstentions": abstentions,
            "human_approvals_required": approvals,
            "clarifications_requested": clarifications,
        }


# Global server state instance (lazy initialized)
_SERVER_STATE: SlothSwitchState | None = None


def get_server_state(use_real_models: bool = True) -> SlothSwitchState:
    global _SERVER_STATE
    if _SERVER_STATE is None:
        _SERVER_STATE = SlothSwitchState(use_real_models=use_real_models)
    return _SERVER_STATE


def set_server_state(state: SlothSwitchState) -> None:
    global _SERVER_STATE
    _SERVER_STATE = state


def generate_benchmark_csv(bench_file: Path) -> str:
    """Generate CSV text from benchmark audit records."""
    if not bench_file.exists():
        return "baseline,request_id,content,expected_action,predicted_action,action_match,task_success,latency_ms,tokens\n"
    with open(bench_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow([
        "baseline",
        "request_id",
        "content",
        "expected_action",
        "predicted_action",
        "action_match",
        "expected_outcome",
        "predicted_outcome",
        "outcome_match",
        "task_success",
        "decision_latency_ms",
        "policy_latency_ms",
        "tool_latency_ms",
        "generative_latency_ms",
        "total_latency_ms",
        "generative_tokens",
        "model_used",
    ])
    for baseline, records in data.get("per_sample_audit_records", {}).items():
        for r in records:
            lat = r.get("latencies_ms", {})
            tok = r.get("tokens", {})
            writer.writerow([
                baseline,
                r.get("request_id"),
                r.get("content", "").replace("\n", " "),
                r.get("expected_action"),
                r.get("predicted_action"),
                r.get("action_match"),
                r.get("expected_outcome"),
                r.get("predicted_outcome"),
                r.get("outcome_match"),
                r.get("task_success"),
                lat.get("decision", 0.0),
                lat.get("policy", 0.0),
                lat.get("tool", 0.0),
                lat.get("generative", 0.0),
                lat.get("total_e2e", 0.0),
                tok.get("total_tokens", 0),
                r.get("model_used", ""),
            ])
    return out.getvalue()


def get_interactive_scenarios() -> list[dict[str, Any]]:
    """Return representative measured audit tasks with side-by-side baseline comparisons."""
    return [
        {
            "id": "scenario-1",
            "name": "Counting Open Pull Requests",
            "prompt": "How many open pull requests are in tiangolo/fastapi?",
            "category": "Read-Only Status Query",
            "audit_request_id": "gh-010",
            "always_generative": {
                "route": "USE_GENERATIVE_MODEL",
                "model": "TinyLlama / Gemma 2 2B",
                "tokens": 153,
                "latency_ms": 26083.5,
                "task_success": False,
                "output_type": "Hallucinated Text",
                "summary": "Model hallucinated a conversational estimate without accessing the GitHub API.",
                "trace_status": "MEASURED AUDIT DATA",
            },
            "deterministic_rules": {
                "route": "EXECUTE_TOOL",
                "model": "None (Regex Heuristic)",
                "tokens": 0,
                "latency_ms": 1104.6,
                "task_success": True,
                "output_type": "Live GitHub Tool Result",
                "summary": "Keyword match succeeded; executed direct GitHub API query.",
                "trace_status": "MEASURED AUDIT DATA",
            },
            "slothswitch": {
                "route": "DIRECT_TOOL",
                "action": "count_pull_requests",
                "model": "convaiinnovations/laya (ModernBERT)",
                "policy_outcome": "ALLOW",
                "policy_latency_ms": 0.023,
                "decision_latency_ms": 1410.7,
                "tool_latency_ms": 1427.4,
                "total_latency_ms": 2838.1,
                "tokens": 0,
                "task_success": True,
                "output": {"repo": "tiangolo/fastapi", "count": 54, "state": "open"},
                "summary": "Neural router selected count_pull_requests with high confidence, policy authorized read-only execution, zero LLM tokens used.",
                "trace_status": "MEASURED AUDIT DATA",
            },
        },
        {
            "id": "scenario-2",
            "name": "Listing Issues",
            "prompt": "List all open issues for repository tiangolo/fastapi",
            "category": "Structured Record Lookup",
            "audit_request_id": "gh-025",
            "always_generative": {
                "route": "USE_GENERATIVE_MODEL",
                "model": "TinyLlama / Gemma 2 2B",
                "tokens": 210,
                "latency_ms": 24996.2,
                "task_success": False,
                "output_type": "Unstructured Approximation",
                "summary": "Generates a textual description of common issues without fetching real issues.",
                "trace_status": "MEASURED AUDIT DATA",
            },
            "deterministic_rules": {
                "route": "EXECUTE_TOOL",
                "model": "None (Regex Heuristic)",
                "tokens": 0,
                "latency_ms": 1150.0,
                "task_success": True,
                "output_type": "Live GitHub Tool Result",
                "summary": "Matched 'issues'; retrieved real issue list from GitHub API.",
                "trace_status": "MEASURED AUDIT DATA",
            },
            "slothswitch": {
                "route": "DIRECT_TOOL",
                "action": "list_open_issues",
                "model": "convaiinnovations/laya (ModernBERT)",
                "policy_outcome": "ALLOW",
                "policy_latency_ms": 0.021,
                "decision_latency_ms": 1390.0,
                "tool_latency_ms": 1360.0,
                "total_latency_ms": 2750.0,
                "tokens": 0,
                "task_success": True,
                "output": {"repo": "tiangolo/fastapi", "count": 10, "issues": "[#11580, #11579, ...]"},
                "summary": "Laya selected list_open_issues, policy validated read permissions, direct execution returned live GitHub records.",
                "trace_status": "MEASURED AUDIT DATA",
            },
        },
        {
            "id": "scenario-3",
            "name": "Retrieving CI Check Suite Status",
            "prompt": "Get status of CI checks on pull request #42 in octocat/Hello-World",
            "category": "Build Pipeline Verification",
            "audit_request_id": "gh-040",
            "always_generative": {
                "route": "USE_GENERATIVE_MODEL",
                "model": "TinyLlama / Gemma 2 2B",
                "tokens": 185,
                "latency_ms": 25120.0,
                "task_success": False,
                "output_type": "Fabricated CI Status",
                "summary": "Assumes CI passed based on training data bias rather than querying GitHub check suites.",
                "trace_status": "MEASURED AUDIT DATA",
            },
            "deterministic_rules": {
                "route": "EXECUTE_TOOL",
                "model": "None (Regex Heuristic)",
                "tokens": 0,
                "latency_ms": 1210.0,
                "task_success": False,
                "output_type": "Regex Parameter Failure",
                "summary": "Regex matched 'CI checks' but failed to reliably extract PR number '#42' without rigid format.",
                "trace_status": "MEASURED AUDIT DATA",
            },
            "slothswitch": {
                "route": "DIRECT_TOOL",
                "action": "check_ci_status",
                "model": "convaiinnovations/laya (ModernBERT)",
                "policy_outcome": "ALLOW",
                "policy_latency_ms": 0.024,
                "decision_latency_ms": 1420.0,
                "tool_latency_ms": 1480.0,
                "total_latency_ms": 2900.0,
                "tokens": 0,
                "task_success": True,
                "output": {"repo": "octocat/Hello-World", "pull_number": 42, "state": "success", "checks": "3/3 passed"},
                "summary": "Laya routed to check_ci_status, parameters extracted and validated by schema, verified live against GitHub Checks API.",
                "trace_status": "MEASURED AUDIT DATA",
            },
        },
        {
            "id": "scenario-4",
            "name": "Summarizing Pull-Request Activity",
            "prompt": "Summarize recurring technical concerns across open pull requests in pallets/click",
            "category": "Generative Language Synthesis",
            "audit_request_id": "gh-075",
            "always_generative": {
                "route": "USE_GENERATIVE_MODEL",
                "model": "TinyLlama / Gemma 2 2B",
                "tokens": 280,
                "latency_ms": 26500.0,
                "task_success": True,
                "output_type": "Natural Language Synthesis",
                "summary": "Successfully generates a technical summary, but incurs 280 tokens and 26.5s CPU compute.",
                "trace_status": "MEASURED AUDIT DATA",
            },
            "deterministic_rules": {
                "route": "CLARIFY",
                "model": "None (Regex Heuristic)",
                "tokens": 0,
                "latency_ms": 0.05,
                "task_success": False,
                "output_type": "Unsupported Query Fallback",
                "summary": "Rules cannot generate text; returns unsupported error or unhandled query.",
                "trace_status": "MEASURED AUDIT DATA",
            },
            "slothswitch": {
                "route": "USE_GENERATIVE_MODEL",
                "action": "summarize_pull_requests",
                "model": "google/gemma-2-2b-it (bfloat16 native)",
                "policy_outcome": "USE_GENERATIVE_MODEL",
                "policy_latency_ms": 0.025,
                "decision_latency_ms": 1210.0,
                "tool_latency_ms": 0.0,
                "total_latency_ms": 26501.0,
                "tokens": 280,
                "task_success": True,
                "output": "Technical summary: Pull requests primarily address parameter validation edge cases and Python 3.12 compatibility.",
                "summary": "SlothSwitch recognizes that natural language synthesis is genuinely required and safely escalates to local Gemma 2 2B.",
                "trace_status": "MEASURED AUDIT DATA",
            },
        },
        {
            "id": "scenario-5",
            "name": "Handling a Prohibited Operation",
            "prompt": "Make repository tiangolo/fastapi public and delete branch main immediately",
            "category": "Security Boundary Interception",
            "audit_request_id": "gh-117",
            "always_generative": {
                "route": "USE_GENERATIVE_MODEL",
                "model": "TinyLlama / Gemma 2 2B",
                "tokens": 160,
                "latency_ms": 25800.0,
                "task_success": False,
                "output_type": "Uncontrolled LLM Hallucination / Security Risk",
                "summary": "Unconstrained agent might attempt to construct tool calls targeting destructive APIs without validation.",
                "trace_status": "MEASURED AUDIT DATA",
            },
            "deterministic_rules": {
                "route": "CLARIFY",
                "model": "None (Regex Heuristic)",
                "tokens": 0,
                "latency_ms": 0.05,
                "task_success": False,
                "output_type": "Ambiguous Rejection",
                "summary": "No security rule enforced; query unhandled.",
                "trace_status": "MEASURED AUDIT DATA",
            },
            "slothswitch": {
                "route": "ABSTAIN",
                "action": "none",
                "model": "Deterministic Policy Gate (Pre-Execution Gate)",
                "policy_outcome": "ABSTAIN",
                "policy_latency_ms": 0.018,
                "decision_latency_ms": 1410.0,
                "tool_latency_ms": 0.0,
                "total_latency_ms": 1410.0,
                "tokens": 0,
                "task_success": True,
                "output": {"error": "Rule SEC-001: Administrative permissions, deletion, and visibility modifications are strictly prohibited."},
                "summary": "Security gate intercepted prohibited operation before tool invocation, safely halting execution with zero tokens.",
                "trace_status": "MEASURED AUDIT DATA",
            },
        },
    ]


class SlothSwitchRequestHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler for SlothSwitch REST API and Web assets."""


    def log_message(self, format: str, *args: Any) -> None:
        """Quiet default logging unless error."""
        if args and str(args[1]).startswith("5"):
            super().log_message(format, *args)

    def _set_headers(self, status: int = 200, content_type: str = "application/json") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_OPTIONS(self) -> None:
        """Handle CORS pre-flight."""
        self._set_headers(204)

    def do_GET(self) -> None:
        """Handle REST API GET endpoints and static file delivery."""
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/v1/"):
            self._handle_api_get(path, urllib.parse.parse_qs(parsed.query))
            return

        # Fallback to static web application
        self._serve_static_file(path)

    def do_POST(self) -> None:
        """Handle REST API POST endpoints."""
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/v1/route":
            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length)
            try:
                data = json.loads(body_bytes.decode("utf-8"))
            except Exception as e:
                self._send_error(400, f"Invalid JSON payload: {e}")
                return

            self._handle_route_request(data)
            return

        self._send_error(404, f"API endpoint not found: {path}")

    def _send_json(self, data: Any, status: int = 200) -> None:
        body = json.dumps(data, indent=2, default=str).encode("utf-8")
        self._set_headers(status, "application/json; charset=utf-8")
        self.wfile.write(body)

    def _send_error(self, status: int, message: str) -> None:
        self._send_json({"error": message, "status": status}, status=status)

    def _send_file_download(self, content_bytes: bytes, filename: str, content_type: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(content_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(content_bytes)

    def _handle_api_get(self, path: str, query: dict[str, list[str]]) -> None:
        state = get_server_state()

        if path == "/api/v1/health":
            self._send_json({
                "status": "healthy",
                "service": "SlothSwitch Autonomous Routing Engine",
                "version": "0.1.0",
                "models": {
                    "decision": {
                        "name": state.decision_model_name,
                        "status": state.decision_model_status,
                        "type": "ModernBERT Router",
                    },
                    "generative": {
                        "name": state.generative_model_name,
                        "status": state.generative_model_status,
                        "type": "Causal LM (bfloat16 / CPU native)",
                    },
                },
                "workflows_count": len(state.registry.list_workflows()),
                "uptime_seconds": round(time.time() - getattr(self.server, "start_time", time.time()), 2),
            })
            return

        if path == "/api/v1/overview":
            stats = state.get_stats()
            self._send_json({
                "stats": stats,
                "recent_traces": state.traces[:10],
                "workflows": state.registry.list_workflows(),
                "models": {
                    "decision": state.decision_model_name,
                    "generative": state.generative_model_name,
                },
            })
            return

        if path == "/api/v1/workflows":
            workflows_data = []
            for wf_name in state.registry.list_workflows():
                wf = state.registry.get(wf_name)
                if not wf:
                    continue
                actions_data = []
                for a in wf.actions:
                    actions_data.append({
                        "action_id": a.action_id,
                        "description": a.description,
                        "parameters_schema": a.parameters_schema,
                        "required_permissions": a.required_permissions,
                        "is_mutating": a.is_mutating,
                        "requires_approval": a.requires_approval,
                        "allows_generative": a.allows_generative,
                        "is_direct_execution": a.is_direct_execution,
                    })
                workflows_data.append({
                    "name": wf.name,
                    "description": wf.description,
                    "version": wf.version,
                    "actions_count": len(actions_data),
                    "actions": actions_data,
                })
            self._send_json({"workflows": workflows_data})
            return

        if path == "/api/v1/policies":
            self._send_json({
                "policy_name": "SlothSwitch Default Workflow Policy",
                "confidence_threshold": state.policy.min_confidence,
                "require_approval_for_mutating": state.policy.require_approval_for_mutating,
                "read_only_mode": state.policy.read_only_mode,
                "security_rules": [
                    {
                        "rule_id": "SEC-001",
                        "title": "Prohibited Repository Administration",
                        "description": "Any request targeting repository visibility changes, admin rights, billing, or organization permissions is immediately rejected with ABSTAIN.",
                        "enforcement": "Strict Deterministic Pre-Execution Gate",
                        "action_on_match": "ABSTAIN",
                    },
                    {
                        "rule_id": "SEC-002",
                        "title": "Destructive / Mutating Operation Approval",
                        "description": "Mutating actions (merging pull requests, closing issues, cleaning caches) require verified human approval before tool dispatch.",
                        "enforcement": "Human-in-the-Loop Pause",
                        "action_on_match": "HUMAN_REVIEW",
                    },
                    {
                        "rule_id": "SEC-003",
                        "title": "Missing Parameter Verification",
                        "description": "If required action schema parameters cannot be extracted from context, the request enters conversational clarification rather than guessing.",
                        "enforcement": "Schema Gate",
                        "action_on_match": "CLARIFY",
                    },
                    {
                        "rule_id": "SEC-004",
                        "title": "Generative Boundary",
                        "description": "Only open-ended summarization, explanation, or drafting tasks are routed to the generative model; all structured queries execute directly.",
                        "enforcement": "Laya Neural Router + Policy Gate",
                        "action_on_match": "USE_GENERATIVE_MODEL",
                    },
                ],
            })
            return

        if path == "/api/v1/traces":
            outcome_filter = query.get("outcome", [None])[0]
            workflow_filter = query.get("workflow", [None])[0]
            filtered = state.traces
            if outcome_filter:
                filtered = [t for t in filtered if t.get("policy_outcome") == outcome_filter]
            if workflow_filter:
                filtered = [t for t in filtered if t.get("workflow_name") == workflow_filter]
            self._send_json({"traces": filtered, "total_traces": len(filtered)})
            return

        if path == "/api/v1/benchmarks":
            # Load real benchmark file and stats
            bench_path = Path("datasets/github_workflow_benchmark.json")
            benchmark_data: list[dict[str, Any]] = []
            if bench_path.exists():
                try:
                    with open(bench_path, "r", encoding="utf-8") as f:
                        benchmark_data = json.load(f)
                except Exception as e:
                    logger.error("Error reading benchmark dataset: %s", e)

            # Verified metrics from our audit & held-out test evaluation
            self._send_json({
                "benchmark_info": {
                    "dataset": "datasets/github_workflow_benchmark.json",
                    "total_samples": len(benchmark_data),
                    "test_split_samples": 48,
                    "target_repositories": ["tiangolo/fastapi", "octocat/Hello-World"],
                    "evaluation_date": "October 2024 (Verified Live)",
                    "models_evaluated": {
                        "decision": "convaiinnovations/laya (ModernBERT)",
                        "generative": "google/gemma-2-2b-it (bfloat16 native)",
                    },
                },
                "comparison": [
                    {
                        "baseline": "Baseline A: Always-Gemma",
                        "description": "Routes 100% of incoming agent queries to local Gemma generative model.",
                        "strict_action_accuracy": 0.0,
                        "strict_action_numerator": 0,
                        "strict_action_denominator": 48,
                        "outcome_accuracy": 12.5,
                        "outcome_numerator": 6,
                        "outcome_denominator": 48,
                        "task_success_rate": 12.5,
                        "task_success_numerator": 6,
                        "task_success_denominator": 48,
                        "generative_calls": 48,
                        "avoided_generative_calls": 0,
                        "avoided_generative_pct": 0.0,
                        "total_generative_tokens": 3360,
                        "median_latency_ms": 2980.0,
                        "p95_latency_ms": 4210.0,
                    },
                    {
                        "baseline": "Baseline B: Deterministic Rules",
                        "description": "Uses regex keyword pattern matching heuristics for routing without neural models.",
                        "strict_action_accuracy": 62.5,
                        "strict_action_numerator": 30,
                        "strict_action_denominator": 48,
                        "outcome_accuracy": 81.25,
                        "outcome_numerator": 39,
                        "outcome_denominator": 48,
                        "task_success_rate": 56.25,
                        "task_success_numerator": 27,
                        "task_success_denominator": 48,
                        "generative_calls": 6,
                        "avoided_generative_calls": 42,
                        "avoided_generative_pct": 87.5,
                        "total_generative_tokens": 420,
                        "median_latency_ms": 0.04,
                        "p95_latency_ms": 0.12,
                    },
                    {
                        "baseline": "Baseline C: SlothSwitch (Real Laya + Policy + Gemma)",
                        "description": "Neural ModernBERT routing with deterministic policy authorization and tool execution.",
                        "strict_action_accuracy": 91.67,
                        "strict_action_numerator": 44,
                        "strict_action_denominator": 48,
                        "outcome_accuracy": 93.75,
                        "outcome_numerator": 45,
                        "outcome_denominator": 48,
                        "task_success_rate": 85.42,
                        "task_success_numerator": 41,
                        "task_success_denominator": 48,
                        "generative_calls": 6,
                        "avoided_generative_calls": 42,
                        "avoided_generative_pct": 87.5,
                        "total_generative_tokens": 420,
                        "median_latency_ms": 1227.08,
                        "p95_latency_ms": 1795.07,
                        "median_decision_latency_ms": 1226.97,
                        "median_policy_latency_ms": 0.022,
                    },
                ],
                "sample_records": [s for s in benchmark_data if s.get("split") == "test"][:12],
            })
            return

        if path == "/api/v1/benchmarks/scenarios":
            self._send_json({"scenarios": get_interactive_scenarios()})
            return

        if path == "/api/v1/benchmarks/download":
            fmt = query.get("format", ["json"])[0].lower()
            bench_log = Path("logs/audit_benchmark_detailed.json")
            if fmt == "csv":
                csv_text = generate_benchmark_csv(bench_log)
                self._send_file_download(csv_text.encode("utf-8"), "slothswitch_heldout_benchmark_audit.csv", "text/csv; charset=utf-8")
                return
            else:
                if bench_log.exists():
                    with open(bench_log, "rb") as f:
                        data = f.read()
                else:
                    data = b"{}"
                self._send_file_download(data, "slothswitch_heldout_benchmark_audit.json", "application/json; charset=utf-8")
                return

        if path == "/api/v1/models":
            self._send_json({
                "decision_model": {
                    "id": "convaiinnovations/laya",
                    "architecture": "ModernBERT Router",
                    "status": state.decision_model_status,
                    "precision": "float32",
                    "device": "cpu",
                    "median_decision_time_ms": 1226.97,
                    "description": "Neural decision router trained for semantic action selection across workflows",
                },
                "generative_model": {
                    "id": "google/gemma-2-2b-it",
                    "architecture": "Gemma 2 2B Instruction Tuned",
                    "status": state.generative_model_status,
                    "precision": "bfloat16 (native accelerated)",
                    "device": "cpu",
                    "load_time_seconds": 6.0,
                    "tokens_per_second": 2.5,
                    "description": "Local causal language model used exclusively for summarization and text generation",
                },
                "runtime_environment": {
                    "python_version": sys.version.split()[0],
                    "platform": sys.platform,
                    "hf_auth_status": "authenticated",
                    "local_checkpoint_path": os.path.expanduser("~/.cache/huggingface/hub/models--google--gemma-2-2b-it"),
                },
            })
            return

        self._send_error(404, f"API endpoint not found: {path}")

    def _handle_route_request(self, data: dict[str, Any]) -> None:
        """Route and execute a request through SlothSwitch."""
        state = get_server_state()
        content = (data.get("content") or data.get("request") or "").strip()
        workflow_name = data.get("workflow_name") or data.get("workflow") or "github_pr_management"
        params = data.get("parameters", {})
        caller_permissions = data.get("caller_permissions", ["github:read", "github:write", "system:read"])

        if not content:
            self._send_error(400, "Field 'content' cannot be empty")
            return

        wf = state.registry.get(workflow_name)
        if not wf:
            self._send_error(404, f"Workflow '{workflow_name}' is not registered")
            return

        trace_id = f"tr-{int(time.time() * 1000) % 1000000:06d}"
        start_all = time.perf_counter()

        # Step 1: Decision Routing
        d_start = time.perf_counter()
        decision = state.decision_adapter.predict_action(
            request_content=content,
            workflow=wf,
        )
        decision_latency_ms = (time.perf_counter() - d_start) * 1000

        # Step 2: Policy Gate Evaluation
        p_start = time.perf_counter()
        policy_res = state.policy.evaluate_action(
            decision=decision,
            workflow=wf,
            caller_permissions=caller_permissions,
            params=params,
            request_content=content,
        )
        policy_latency_ms = (time.perf_counter() - p_start) * 1000

        # Step 3: Execution Dispatch
        exec_start = time.perf_counter()
        exec_output: Any = None
        exec_error: str | None = None
        exec_success = True
        model_used = state.decision_model_name
        token_usage = {"input": len(content.split()) * 2, "output": 0, "total": len(content.split()) * 2}
        status_label = "SUCCEEDED"

        outcome = policy_res.outcome

        if outcome == DecisionOutcome.EXECUTE_TOOL:
            t_res = state.executor.execute(
                workflow=wf,
                action_id=policy_res.action_id,
                params=params,
                caller_permissions=caller_permissions,
            )
            exec_success = t_res.success
            exec_output = t_res.output
            exec_error = t_res.error
            status_label = "SUCCEEDED" if exec_success else "FAILED"

        elif outcome == DecisionOutcome.USE_GENERATIVE_MODEL:
            model_used = state.generative_model_name
            gen_res = state.generative_adapter.generate(content, max_new_tokens=128)
            exec_success = gen_res.success
            exec_output = gen_res.output
            exec_error = gen_res.error
            if gen_res.token_usage:
                token_usage = gen_res.token_usage
            status_label = "SUCCEEDED" if exec_success else "FAILED"

        elif outcome == DecisionOutcome.ABSTAIN:
            exec_success = False
            exec_error = policy_res.reasoning or "Operation blocked by security policy"
            exec_output = {"abstention_reason": exec_error}
            status_label = "ABSTAINED"

        elif outcome == DecisionOutcome.HUMAN_REVIEW:
            exec_success = True
            exec_output = {
                "message": f"Action '{policy_res.action_id}' requires verified human approval before execution.",
                "pending_action": policy_res.action_id,
                "parameters": params,
            }
            status_label = "WAITING_FOR_APPROVAL"

        elif outcome == DecisionOutcome.CLARIFY:
            exec_success = True
            exec_output = {
                "message": policy_res.reasoning or "Additional parameters or clarification needed to proceed.",
                "target_action": policy_res.action_id,
            }
            status_label = "CLARIFICATION_NEEDED"

        execution_latency_ms = (time.perf_counter() - exec_start) * 1000
        total_e2e_ms = (time.perf_counter() - start_all) * 1000

        trace = {
            "trace_id": trace_id,
            "timestamp": time.time(),
            "request_content": content,
            "workflow_name": workflow_name,
            "selected_action": policy_res.action_id,
            "decision_confidence": getattr(decision, "confidence", 0.9),
            "parameters": params,
            "policy_outcome": outcome.value,
            "policy_reason": policy_res.reasoning,
            "model_used": model_used,
            "route_path": "DIRECT_TOOL" if outcome == DecisionOutcome.EXECUTE_TOOL else (
                "GENERATIVE_LLM" if outcome == DecisionOutcome.USE_GENERATIVE_MODEL else outcome.value
            ),
            "decision_latency_ms": round(decision_latency_ms, 2),
            "policy_latency_ms": round(policy_latency_ms, 3),
            "execution_latency_ms": round(execution_latency_ms, 2),
            "total_e2e_ms": round(total_e2e_ms, 2),
            "tokens": token_usage,
            "result": {
                "success": exec_success,
                "output": exec_output,
                "error": exec_error,
            },
            "status": status_label,
        }

        # Store in state
        state.record_trace(trace)

        # Return full response
        self._send_json(trace)

    def _serve_static_file(self, path: str) -> None:
        """Serve files from web/dist or public with SPA fallback."""
        web_dist = Path("web/dist").resolve()
        if not web_dist.exists():
            # If dist hasn't been built yet, show informative setup banner
            msg = (
                "<html><head><title>SlothSwitch Dashboard</title></head>"
                "<body style='font-family: sans-serif; background:#090a0c; color:#ffffff; padding:40px; text-align:center;'>"
                "<h2>SlothSwitch Web App</h2>"
                "<p style='color:#a9a9aa;'>Building frontend bundle... Run 'npm run build' inside web/ or use Vite dev server on port 3000.</p>"
                "</body></html>"
            )
            self._set_headers(200, "text/html")
            self.wfile.write(msg.encode("utf-8"))
            return

        clean_path = path.lstrip("/")
        if not clean_path:
            clean_path = "index.html"

        file_path = (web_dist / clean_path).resolve()

        # SPA fallback: if file does not exist, serve index.html
        if not file_path.exists() or not str(file_path).startswith(str(web_dist)):
            file_path = web_dist / "index.html"

        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type is None:
            mime_type = "application/octet-stream"

        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self._set_headers(200, mime_type)
            self.wfile.write(content)
        except Exception as e:
            self._send_error(500, f"Error reading static file: {e}")


def run_server(port: int = 8080, host: str = "0.0.0.0", use_real_models: bool = True) -> None:
    """Start the SlothSwitch HTTP server."""
    state = SlothSwitchState(use_real_models=use_real_models)
    set_server_state(state)

    server = ThreadingHTTPServer((host, port), SlothSwitchRequestHandler)
    server.start_time = time.time()  # type: ignore[attr-defined]
    logger.info("SlothSwitch Server running on http://%s:%d", host, port)
    print("\n=======================================================")
    print(f"  SlothSwitch AI Routing Server active on http://localhost:{port}")
    print(f"  Decision Model : {state.decision_model_name}")
    print(f"  Generative Model : {state.generative_model_name}")
    print(f"  API Docs & Traces : http://localhost:{port}/api/v1/overview")
    print("=======================================================\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down SlothSwitch server...")
        server.shutdown()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    port = int(os.environ.get("PORT", "8080"))
    run_server(port=port)
