"""Unit and live integration tests for GitHub PR and issue management workflow."""

from unittest.mock import patch

import pytest

from slothswitch.adapters.tools.github import GitHubToolAdapter
from slothswitch.executor import ToolExecutor
from slothswitch.schemas import ExecutionState
from slothswitch.workflows.github_pr_management import create_github_workflow


def test_github_workflow_definition_structure() -> None:
    """GitHub workflow defines all required read-only, mutating, and generative actions."""
    wf = create_github_workflow()
    assert wf.name == "github_pr_management"

    read_actions = [a.action_id for a in wf.get_read_only_actions()]
    assert "list_open_pull_requests" in read_actions
    assert "count_pull_requests" in read_actions
    assert "get_pull_request_details" in read_actions
    assert "list_open_issues" in read_actions
    assert "count_issues" in read_actions
    assert "get_issue_details" in read_actions
    assert "get_pull_request_checks" in read_actions
    assert "list_repository_labels" in read_actions

    mutating_actions = [a.action_id for a in wf.get_mutating_actions()]
    assert "add_issue_label" in mutating_actions
    assert "add_pull_request_label" in mutating_actions
    assert "create_issue_comment" in mutating_actions

    # All mutating actions must require approval
    for action in wf.get_mutating_actions():
        assert action.requires_approval is True
        assert "github:write" in action.required_permissions

    gen_actions = [a.action_id for a in wf.get_generative_actions()]
    assert "summarize_pull_requests" in gen_actions
    assert "summarize_issue_concerns" in gen_actions
    assert "generate_repository_activity_report" in gen_actions


def test_github_tool_adapter_validation() -> None:
    """GitHubToolAdapter rejects invalid repository identifiers."""
    adapter = GitHubToolAdapter()
    with pytest.raises(ValueError, match="Invalid or missing 'repo' parameter"):
        adapter.execute("count_pull_requests", {"repo": "invalidrepo"})


def test_github_tool_adapter_mocked_calls() -> None:
    """GitHubToolAdapter formats API responses into clean structured payloads."""
    adapter = GitHubToolAdapter()

    # Mock list_open_pull_requests
    mock_prs = [
        {"number": 42, "title": "Fix bug", "user": {"login": "alice"}, "created_at": "2026-01-01T00:00:00Z", "html_url": "https://github.com/foo/bar/pull/42"}
    ]
    with patch.object(adapter, "_make_request", return_value=mock_prs):
        res = adapter.execute("list_open_pull_requests", {"repo": "foo/bar", "limit": 5})
        assert res["count"] == 1
        assert res["pull_requests"][0]["number"] == 42
        assert res["pull_requests"][0]["user"] == "alice"

    # Mock count_pull_requests
    with patch.object(adapter, "_make_request", return_value=[{"id": 1}, {"id": 2}]):
        res = adapter.execute("count_pull_requests", {"repo": "foo/bar", "state": "open"})
        assert res["count"] == 2
        assert res["state"] == "open"

    # Mock create_issue_comment
    with patch.object(adapter, "_make_request", return_value={"id": 999}):
        res = adapter.execute("create_issue_comment", {"repo": "foo/bar", "issue_number": 10, "body": "LGTM!"})
        assert res["comment_id"] == 999
        assert res["status"] == "created"


def test_github_tool_executor_live_public_repo() -> None:
    """Live read-only test against public repository octocat/Hello-World."""
    wf = create_github_workflow()
    adapter = GitHubToolAdapter()
    executor = ToolExecutor(adapters=[adapter])

    # Count issues on public octocat/Hello-World repo
    res = executor.execute(
        workflow=wf,
        action_id="count_issues",
        params={"repo": "octocat/Hello-World"},
        caller_permissions=["github:read"],
    )

    assert res.execution_state == ExecutionState.SUCCEEDED
    assert res.success is True
    assert res.output["repo"] == "octocat/Hello-World"
    assert "count" in res.output
    assert isinstance(res.output["count"], int)
