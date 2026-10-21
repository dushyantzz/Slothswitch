"""Tool adapter executing system_ops workflow actions."""

from __future__ import annotations

from typing import Any

from slothswitch.adapters.tools.base import ToolAdapter
from slothswitch.workflows.system_ops import (
    execute_clean_temp_cache,
    execute_get_disk_usage,
    execute_get_system_health,
)


class SystemOpsToolAdapter(ToolAdapter):
    """Tool adapter for local system diagnostic and maintenance operations."""

    @property
    def name(self) -> str:
        return "system_ops_tool"

    def supports_action(self, action_id: str) -> bool:
        return action_id in ("get_system_health", "get_disk_usage", "clean_temp_cache")

    def execute(self, action_id: str, params: dict[str, Any]) -> dict[str, Any]:
        if action_id == "get_system_health":
            return execute_get_system_health()
        elif action_id == "get_disk_usage":
            path = params.get("path", ".")
            return execute_get_disk_usage(path=path)
        elif action_id == "clean_temp_cache":
            target_dir = params["target_dir"]
            return execute_clean_temp_cache(target_dir=target_dir)
        else:
            raise ValueError(f"Action '{action_id}' is not supported by {self.name}")
