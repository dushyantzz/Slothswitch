"""GitHub tool adapter for SlothSwitch.

Implements read-only and approval-gated mutating actions against the GitHub REST API v3.
Supports public repositories with zero credentials and authenticated usage via GITHUB_TOKEN.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from typing import Any

from slothswitch.adapters.tools.base import ToolAdapter

logger = logging.getLogger(__name__)


class GitHubToolAdapter(ToolAdapter):
    """Tool adapter interfacing with GitHub REST API v3."""

    def __init__(
        self,
        token: str | None = None,
        base_url: str = "https://api.github.com",
        timeout_seconds: float = 10.0,
    ) -> None:
        self._token = token or os.environ.get("GITHUB_TOKEN")
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    @property
    def name(self) -> str:
        return "github_tool_adapter"

    def supports_action(self, action_id: str) -> bool:
        return action_id in {
            "list_open_pull_requests",
            "count_pull_requests",
            "get_pull_request_details",
            "list_open_issues",
            "count_issues",
            "get_issue_details",
            "get_pull_request_checks",
            "list_repository_labels",
            "add_issue_label",
            "add_pull_request_label",
            "create_issue_comment",
        }

    def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        data: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self._base_url}/{endpoint.lstrip('/')}"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "SlothSwitch-Engine",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        body_bytes = json.dumps(data).encode("utf-8") if data is not None else None
        req = urllib.request.Request(url, data=body_bytes, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=self._timeout_seconds) as resp:
                status_code = resp.status
                raw = resp.read()
                if not raw:
                    return {"status_code": status_code, "data": None}
                return json.loads(raw.decode("utf-8"))
        except urllib.error.HTTPError as exc:
            msg = f"GitHub API error {exc.code} for endpoint '{endpoint}'"
            if exc.code == 404:
                msg = f"Resource not found on GitHub: '{endpoint}'"
            elif exc.code == 403:
                msg = f"GitHub API rate limit exceeded or access forbidden: '{endpoint}'"
            elif exc.code == 401:
                msg = "GitHub API unauthorized. Check GITHUB_TOKEN"
            logger.error(msg)
            raise RuntimeError(msg) from None
        except urllib.error.URLError as exc:
            logger.error("Network error reaching GitHub: %s", exc.reason)
            raise RuntimeError(f"Network error contacting GitHub: {exc.reason}") from None

    def execute(self, action_id: str, params: dict[str, Any]) -> dict[str, Any]:
        """Dispatch and execute supported GitHub actions."""
        repo = params.get("repo", "").strip()
        if not repo or "/" not in repo:
            raise ValueError(f"Invalid or missing 'repo' parameter: '{repo}'. Must be 'owner/repo'.")

        if action_id == "list_open_pull_requests":
            limit = int(params.get("limit", 10))
            data = self._make_request(f"repos/{repo}/pulls?state=open&per_page={limit}")
            prs = [
                {
                    "number": pr.get("number"),
                    "title": pr.get("title"),
                    "user": pr.get("user", {}).get("login"),
                    "created_at": pr.get("created_at"),
                    "html_url": pr.get("html_url"),
                }
                for pr in (data if isinstance(data, list) else [])
            ]
            return {"repo": repo, "count": len(prs), "pull_requests": prs}

        elif action_id == "count_pull_requests":
            state = params.get("state", "open")
            data = self._make_request(f"repos/{repo}/pulls?state={state}&per_page=100")
            count = len(data) if isinstance(data, list) else 0
            return {"repo": repo, "state": state, "count": count}

        elif action_id == "get_pull_request_details":
            pr_num = params.get("pull_number")
            if pr_num is None:
                raise ValueError("Missing 'pull_number' parameter")
            pr = self._make_request(f"repos/{repo}/pulls/{pr_num}")
            return {
                "repo": repo,
                "number": pr.get("number"),
                "title": pr.get("title"),
                "state": pr.get("state"),
                "body": pr.get("body", "") or "",
                "user": pr.get("user", {}).get("login"),
                "created_at": pr.get("created_at"),
                "mergeable": pr.get("mergeable"),
                "changed_files": pr.get("changed_files", 0),
            }

        elif action_id == "list_open_issues":
            limit = int(params.get("limit", 10))
            data = self._make_request(f"repos/{repo}/issues?state=open&per_page={limit}")
            # Note: GitHub issues API returns both issues and PRs unless filtered
            issues = [
                {
                    "number": item.get("number"),
                    "title": item.get("title"),
                    "user": item.get("user", {}).get("login"),
                    "created_at": item.get("created_at"),
                    "is_pull_request": "pull_request" in item,
                }
                for item in (data if isinstance(data, list) else [])
            ]
            return {"repo": repo, "count": len(issues), "issues": issues}

        elif action_id == "count_issues":
            state = params.get("state", "open")
            repo_info = self._make_request(f"repos/{repo}")
            open_count = repo_info.get("open_issues_count", 0)
            return {"repo": repo, "state": state, "count": open_count}

        elif action_id == "get_issue_details":
            issue_num = params.get("issue_number")
            if issue_num is None:
                raise ValueError("Missing 'issue_number' parameter")
            issue = self._make_request(f"repos/{repo}/issues/{issue_num}")
            return {
                "repo": repo,
                "number": issue.get("number"),
                "title": issue.get("title"),
                "state": issue.get("state"),
                "body": issue.get("body", "") or "",
                "user": issue.get("user", {}).get("login"),
                "created_at": issue.get("created_at"),
                "labels": [lbl.get("name") for lbl in issue.get("labels", [])],
            }

        elif action_id == "get_pull_request_checks":
            pr_num = params.get("pull_number")
            if pr_num is None:
                raise ValueError("Missing 'pull_number' parameter")
            pr = self._make_request(f"repos/{repo}/pulls/{pr_num}")
            head_sha = pr.get("head", {}).get("sha")
            if not head_sha:
                return {"repo": repo, "pull_number": pr_num, "checks": []}
            checks_data = self._make_request(f"repos/{repo}/commits/{head_sha}/check-runs")
            check_runs = checks_data.get("check_runs", [])
            return {
                "repo": repo,
                "pull_number": pr_num,
                "head_sha": head_sha,
                "total_checks": len(check_runs),
                "checks": [
                    {
                        "name": c.get("name"),
                        "status": c.get("status"),
                        "conclusion": c.get("conclusion"),
                    }
                    for c in check_runs
                ],
            }

        elif action_id == "list_repository_labels":
            data = self._make_request(f"repos/{repo}/labels?per_page=100")
            labels = [lbl.get("name") for lbl in (data if isinstance(data, list) else [])]
            return {"repo": repo, "count": len(labels), "labels": labels}

        # Mutating actions
        elif action_id in ("add_issue_label", "add_pull_request_label"):
            target_num = params.get("issue_number") or params.get("pull_number")
            labels = params.get("labels", [])
            if not target_num or not labels:
                raise ValueError("Requires target number and 'labels' list")
            data = self._make_request(
                f"repos/{repo}/issues/{target_num}/labels",
                method="POST",
                data={"labels": labels},
            )
            return {"repo": repo, "target_number": target_num, "applied_labels": labels, "status": "success"}

        elif action_id == "create_issue_comment":
            issue_num = params.get("issue_number")
            body = params.get("body", "").strip()
            if not issue_num or not body:
                raise ValueError("Requires 'issue_number' and non-empty 'body'")
            data = self._make_request(
                f"repos/{repo}/issues/{issue_num}/comments",
                method="POST",
                data={"body": body},
            )
            return {"repo": repo, "issue_number": issue_num, "comment_id": data.get("id"), "status": "created"}

        else:
            raise ValueError(f"Action '{action_id}' is not supported by {self.name}")
