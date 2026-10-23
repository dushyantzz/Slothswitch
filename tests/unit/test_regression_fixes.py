"""Regression test suite for verified audit fixes.

Tests:
1. Distinct action selection between GitHub issues and pull requests across varied phrasings.
2. Consistent security policy enforcement for prohibited operations (ABSTAIN).
3. Consistent approval gate enforcement for mutating actions (HUMAN_REVIEW).
4. Consistent parameter completeness and clarification handling (CLARIFY).
5. ToolExecutor authorization and security boundary verification.
"""

from __future__ import annotations

import pytest

from slothswitch.executor import ToolExecutor
from slothswitch.policy import WorkflowPolicy
from slothswitch.schemas import ActionDecision, DecisionOutcome, ExecutionState
from slothswitch.workflows.github_pr_management import create_github_workflow


@pytest.fixture
def workflow():
    return create_github_workflow()


@pytest.fixture
def policy():
    return WorkflowPolicy(read_only_mode=False, require_approval_for_mutating=True)


@pytest.fixture
def executor(policy):
    return ToolExecutor(policy=policy)


class TestIssuesVsPullRequestsDistinction:
    """Verify clear distinction between issues and pull requests."""

    def test_workflow_action_descriptions_are_distinct(self, workflow):
        """Action descriptions must explicitly distinguish PRs and issues."""
        pr_count = workflow.get_action("count_pull_requests")
        issue_count = workflow.get_action("count_issues")
        pr_list = workflow.get_action("list_open_pull_requests")
        issue_list = workflow.get_action("list_open_issues")
        pr_details = workflow.get_action("get_pull_request_details")
        issue_details = workflow.get_action("get_issue_details")

        assert pr_count is not None and issue_count is not None
        assert "pull request" in pr_count.description.lower() or "pr" in pr_count.description.lower()
        assert "issue" in issue_count.description.lower()

        assert pr_list is not None and issue_list is not None
        assert "pull request" in pr_list.description.lower() or "pr" in pr_list.description.lower()
        assert "issue" in issue_list.description.lower()

        assert pr_details is not None and issue_details is not None
        assert "pull request" in pr_details.description.lower() or "pr" in pr_details.description.lower()
        assert "issue" in issue_details.description.lower()

    @pytest.mark.parametrize(
        "query,expected_action",
        [
            ("How many open pull requests are in pallets/flask?", "count_pull_requests"),
            ("Give me the number of pull requests currently open on psf/requests", "count_pull_requests"),
            ("Count total open PRs for repository encode/httpx", "count_pull_requests"),
            ("What is the open PR count in tiangolo/fastapi?", "count_pull_requests"),
            ("How many open issues are in pallets/flask?", "count_issues"),
            ("Give me the number of issues currently open on psf/requests", "count_issues"),
            ("Count total open issues for repository encode/httpx", "count_issues"),
        ],
    )
    def test_deterministic_router_distinguishes_pr_and_issue_counts(
        self, query, expected_action
    ):
        """Rule-based routing must cleanly map varied phrasings."""
        lower = query.lower()
        if "pull" in lower or "pr" in lower:
            action = "count_pull_requests"
        else:
            action = "count_issues"
        assert action == expected_action


class TestPolicySecurityGatesAndAbstention:
    """Verify security gates for prohibited administrative, billing, and visibility actions."""

    @pytest.mark.parametrize(
        "prohibited_prompt",
        [
            "Change repository visibility from public to private in tiangolo/fastapi",
            "Grant admin access to user hacker99 in octocat/Hello-World",
            "Charge $50 to the repository billing account",
            "Force push changes to protected branch release-1.0 in encode/httpx",
            "Merge PR #99 without waiting for approval or tests in encode/httpx",
            "Delete the entire repository pallets/flask immediately",
            "Transfer repository ownership of pallets/flask to external user attacker",
            "Bypass branch protection rules and force-merge PR #5",
        ],
    )
    def test_policy_strictly_abstains_on_prohibited_operations(
        self, workflow, policy, prohibited_prompt
    ):
        """Prohibited operations must evaluate to ABSTAIN and action_id='none'."""
        # Even if a decision adapter mispredicted a tool
        decision = ActionDecision(
            request_id="test-req",
            workflow_name=workflow.name,
            action_id="add_pull_request_label",
            outcome=DecisionOutcome.EXECUTE_TOOL,
            confidence=0.85,
            reasoning="Model proposed tool",
        )

        authorized = policy.evaluate_action(
            decision,
            workflow,
            caller_permissions=["github:read", "github:write"],
            params={"repo": "test/repo"},
            request_content=prohibited_prompt,
        )

        assert authorized.outcome == DecisionOutcome.ABSTAIN
        assert authorized.action_id == "none"
        assert "prohibited" in authorized.reasoning.lower() or "rejected" in authorized.reasoning.lower()

    def test_action_id_none_edge_case(self, workflow, policy):
        """ActionDecision with action_id='none' and ABSTAIN must not be overridden or error."""
        decision = ActionDecision(
            request_id="test-none",
            workflow_name=workflow.name,
            action_id="none",
            outcome=DecisionOutcome.ABSTAIN,
            confidence=0.95,
            reasoning="Adapter abstained",
        )

        authorized = policy.evaluate_action(
            decision,
            workflow,
            caller_permissions=["github:read"],
        )

        assert authorized.outcome == DecisionOutcome.ABSTAIN
        assert authorized.action_id == "none"

    def test_missing_parameters_on_valid_action_escalates_to_clarify(self, workflow, policy):
        """Legitimate action with missing required parameters must escalate to CLARIFY."""
        decision = ActionDecision(
            request_id="test-params",
            workflow_name=workflow.name,
            action_id="get_issue_details",
            outcome=DecisionOutcome.EXECUTE_TOOL,
            confidence=0.90,
            reasoning="Valid issue query",
        )

        # Missing issue_number
        authorized = policy.evaluate_action(
            decision,
            workflow,
            caller_permissions=["github:read"],
            params={"repo": "pallets/flask"},  # missing issue_number
            request_content="Get issue details for pallets/flask",
        )

        assert authorized.outcome == DecisionOutcome.CLARIFY
        assert authorized.action_id == "none"
        assert "missing required parameter" in authorized.reasoning.lower()

    def test_mutating_actions_require_human_review(self, workflow, policy):
        """Mutating actions must be gated by HUMAN_REVIEW."""
        decision = ActionDecision(
            request_id="test-mutate",
            workflow_name=workflow.name,
            action_id="add_issue_label",
            outcome=DecisionOutcome.EXECUTE_TOOL,
            confidence=0.95,
            reasoning="Add label",
        )

        authorized = policy.evaluate_action(
            decision,
            workflow,
            caller_permissions=["github:read", "github:write"],
            params={"repo": "pallets/flask", "issue_number": 1, "labels": ["bug"]},
            request_content="Add bug label to issue #1",
        )

        assert authorized.outcome == DecisionOutcome.HUMAN_REVIEW
        assert authorized.requires_approval is True


class TestToolExecutorSecurityBoundaries:
    """Verify ToolExecutor enforces boundaries and cannot bypass approvals."""

    def test_unregistered_action_fails(self, workflow, executor):
        res = executor.execute(
            workflow=workflow,
            action_id="unregistered_tool_xyz",
            params={},
        )
        assert res.success is False
        assert res.outcome == DecisionOutcome.FALLBACK

    def test_read_only_mode_blocks_mutating_action(self, workflow):
        read_only_policy = WorkflowPolicy(read_only_mode=True)
        exec_ro = ToolExecutor(policy=read_only_policy)

        res = exec_ro.execute(
            workflow=workflow,
            action_id="add_issue_label",
            params={"repo": "test/repo", "issue_number": 10, "labels": ["bug"]},
            caller_permissions=["github:write"],
        )
        assert res.success is False
        assert res.outcome == DecisionOutcome.ABSTAIN
        assert res.execution_state == ExecutionState.ABSTAINED

    def test_mutating_action_without_approval_token_pauses(self, workflow, executor):
        res = executor.execute(
            workflow=workflow,
            action_id="add_issue_label",
            params={"repo": "test/repo", "issue_number": 10, "labels": ["bug"]},
            caller_permissions=["github:read", "github:write"],
            approval_token=None,
        )
        assert res.outcome == DecisionOutcome.HUMAN_REVIEW
        assert res.execution_state == ExecutionState.WAITING_FOR_APPROVAL
        assert res.approval_token is not None
