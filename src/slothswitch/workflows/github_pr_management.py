"""GitHub Issue and Pull Request Management workflow.

Implements read-only operations, approval-gated mutating actions, and
bounded generative tasks (summarization, reporting).
"""

from __future__ import annotations

from slothswitch.workflows.base import ActionDefinition, WorkflowDefinition


def create_github_workflow() -> WorkflowDefinition:
    """Construct and return the GitHub Issue and PR Management WorkflowDefinition."""
    actions = [
        # --- Read-only actions ---
        ActionDefinition(
            action_id="list_open_pull_requests",
            description="List open pull requests or PRs for a repository with title and author",
            parameters_schema={
                "properties": {
                    "repo": {"type": "string", "description": "Repository in 'owner/repo' format"},
                    "limit": {"type": "integer", "description": "Maximum PRs to return", "default": 10},
                },
                "required": ["repo"],
            },
            required_permissions=["github:read"],
            is_mutating=False,
            requires_approval=False,
            allows_generative=False,
            is_direct_execution=True,
            idempotent=True,
        ),
        ActionDefinition(
            action_id="count_pull_requests",
            description="Count pull requests or PRs in a repository",
            parameters_schema={
                "properties": {
                    "repo": {"type": "string", "description": "Repository in 'owner/repo' format"},
                    "state": {"type": "string", "description": "PR state: open, closed, or all", "default": "open"},
                },
                "required": ["repo"],
            },
            required_permissions=["github:read"],
            is_mutating=False,
            requires_approval=False,
            allows_generative=False,
            is_direct_execution=True,
            idempotent=True,
        ),
        ActionDefinition(
            action_id="get_pull_request_details",
            description="Fetch pull request details, body, description, and status for a PR number",
            parameters_schema={
                "properties": {
                    "repo": {"type": "string", "description": "Repository in 'owner/repo' format"},
                    "pull_number": {"type": "integer", "description": "Pull request number"},
                },
                "required": ["repo", "pull_number"],
            },
            required_permissions=["github:read"],
            is_mutating=False,
            requires_approval=False,
            allows_generative=False,
            is_direct_execution=True,
            idempotent=True,
        ),
        ActionDefinition(
            action_id="list_open_issues",
            description="List open issues or bug reports for a repository",
            parameters_schema={
                "properties": {
                    "repo": {"type": "string", "description": "Repository in 'owner/repo' format"},
                    "limit": {"type": "integer", "description": "Maximum issues to return", "default": 10},
                },
                "required": ["repo"],
            },
            required_permissions=["github:read"],
            is_mutating=False,
            requires_approval=False,
            allows_generative=False,
            is_direct_execution=True,
            idempotent=True,
        ),
        ActionDefinition(
            action_id="count_issues",
            description="Count issues or bug reports in a repository",
            parameters_schema={
                "properties": {
                    "repo": {"type": "string", "description": "Repository in 'owner/repo' format"},
                    "state": {"type": "string", "description": "Issue state", "default": "open"},
                },
                "required": ["repo"],
            },
            required_permissions=["github:read"],
            is_mutating=False,
            requires_approval=False,
            allows_generative=False,
            is_direct_execution=True,
            idempotent=True,
        ),
        ActionDefinition(
            action_id="get_issue_details",
            description="Fetch issue details, body, description, and labels for an issue number",
            parameters_schema={
                "properties": {
                    "repo": {"type": "string", "description": "Repository in 'owner/repo' format"},
                    "issue_number": {"type": "integer", "description": "Issue number"},
                },
                "required": ["repo", "issue_number"],
            },
            required_permissions=["github:read"],
            is_mutating=False,
            requires_approval=False,
            allows_generative=False,
            is_direct_execution=True,
            idempotent=True,
        ),
        ActionDefinition(
            action_id="get_pull_request_checks",
            description="Fetch pull request CI/CD check runs, test results, and status for a PR number",
            parameters_schema={
                "properties": {
                    "repo": {"type": "string", "description": "Repository in 'owner/repo' format"},
                    "pull_number": {"type": "integer", "description": "Pull request number"},
                },
                "required": ["repo", "pull_number"],
            },
            required_permissions=["github:read"],
            is_mutating=False,
            requires_approval=False,
            allows_generative=False,
            is_direct_execution=True,
            idempotent=True,
        ),
        ActionDefinition(
            action_id="list_repository_labels",
            description="List all issue and pull request labels configured in a repository",
            parameters_schema={
                "properties": {
                    "repo": {"type": "string", "description": "Repository in 'owner/repo' format"},
                },
                "required": ["repo"],
            },
            required_permissions=["github:read"],
            is_mutating=False,
            requires_approval=False,
            allows_generative=False,
            is_direct_execution=True,
            idempotent=True,
        ),
        # --- Mutating actions (approval-gated) ---
        ActionDefinition(
            action_id="add_issue_label",
            description="Add one or more labels to an issue",
            parameters_schema={
                "properties": {
                    "repo": {"type": "string", "description": "Repository in 'owner/repo' format"},
                    "issue_number": {"type": "integer", "description": "Issue number"},
                    "labels": {"type": "array", "description": "List of label strings"},
                },
                "required": ["repo", "issue_number", "labels"],
            },
            required_permissions=["github:write"],
            is_mutating=True,
            requires_approval=True,
            allows_generative=False,
            is_direct_execution=True,
            idempotent=False,
        ),
        ActionDefinition(
            action_id="add_pull_request_label",
            description="Add one or more labels to a pull request",
            parameters_schema={
                "properties": {
                    "repo": {"type": "string", "description": "Repository in 'owner/repo' format"},
                    "pull_number": {"type": "integer", "description": "Pull request number"},
                    "labels": {"type": "array", "description": "List of label strings"},
                },
                "required": ["repo", "pull_number", "labels"],
            },
            required_permissions=["github:write"],
            is_mutating=True,
            requires_approval=True,
            allows_generative=False,
            is_direct_execution=True,
            idempotent=False,
        ),
        ActionDefinition(
            action_id="create_issue_comment",
            description="Post a comment on an issue or pull request",
            parameters_schema={
                "properties": {
                    "repo": {"type": "string", "description": "Repository in 'owner/repo' format"},
                    "issue_number": {"type": "integer", "description": "Issue or PR number"},
                    "body": {"type": "string", "description": "Comment markdown text"},
                },
                "required": ["repo", "issue_number", "body"],
            },
            required_permissions=["github:write"],
            is_mutating=True,
            requires_approval=True,
            allows_generative=False,
            is_direct_execution=True,
            idempotent=False,
        ),
        # --- Generative actions ---
        ActionDefinition(
            action_id="summarize_pull_requests",
            description="Summarize themes, architecture changes, and potential risks across PR descriptions",
            parameters_schema={
                "properties": {
                    "repo": {"type": "string", "description": "Repository name"},
                    "pull_requests_data": {"type": "array", "description": "Bounded pull request metadata"},
                },
                "required": ["repo"],
            },
            required_permissions=["github:read"],
            is_mutating=False,
            requires_approval=False,
            allows_generative=True,
            is_direct_execution=False,
            idempotent=True,
        ),
        ActionDefinition(
            action_id="summarize_issue_concerns",
            description="Synthesize key user complaints, bug reports, and technical concerns from issue bodies",
            parameters_schema={
                "properties": {
                    "repo": {"type": "string", "description": "Repository name"},
                    "issues_data": {"type": "array", "description": "Bounded issue metadata"},
                },
                "required": ["repo"],
            },
            required_permissions=["github:read"],
            is_mutating=False,
            requires_approval=False,
            allows_generative=True,
            is_direct_execution=False,
            idempotent=True,
        ),
        ActionDefinition(
            action_id="generate_repository_activity_report",
            description="Produce a concise repository activity report summarizing open PRs, issues, and CI health",
            parameters_schema={
                "properties": {
                    "repo": {"type": "string", "description": "Repository name"},
                    "activity_summary": {"type": "object", "description": "Aggregated metrics"},
                },
                "required": ["repo"],
            },
            required_permissions=["github:read"],
            is_mutating=False,
            requires_approval=False,
            allows_generative=True,
            is_direct_execution=False,
            idempotent=True,
        ),
    ]

    return WorkflowDefinition(
        name="github_pr_management",
        version="1.0.0",
        description="Workflow for managing GitHub issues, pull requests, CI checks, and generating activity summaries",
        actions=actions,
    )
