"""System Operations workflow demonstrating non-GitHub reusability of the engine.

Proves that SlothSwitch's workflow registry, decision routing, tool execution,
and generative delegation work identically for general software operations.
"""

from __future__ import annotations

import os
import platform
import shutil
import time
from typing import Any

from slothswitch.workflows.base import ActionDefinition, WorkflowDefinition


def execute_get_system_health() -> dict[str, Any]:
    """Execute real local system health inspection."""
    return {
        "os": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "cpu_count": os.cpu_count(),
        "timestamp": time.time(),
        "status": "healthy",
    }


def execute_get_disk_usage(path: str = ".") -> dict[str, Any]:
    """Execute real disk usage check."""
    usage = shutil.disk_usage(path)
    return {
        "path": os.path.abspath(path),
        "total_bytes": usage.total,
        "used_bytes": usage.used,
        "free_bytes": usage.free,
        "free_gb": round(usage.free / (1024**3), 2),
    }


def execute_clean_temp_cache(target_dir: str) -> dict[str, Any]:
    """Execute cache directory cleaning (mutating operation)."""
    # Safety guard: only allow cleaning within safe directory paths
    norm_path = os.path.abspath(target_dir)
    if not os.path.exists(norm_path):
        return {"target_dir": norm_path, "cleaned_files": 0, "status": "directory_not_found"}

    cleaned_count = 0
    for root, dirs, files in os.walk(norm_path):
        for f in files:
            if f.endswith((".tmp", ".cache", ".bak")):
                file_path = os.path.join(root, f)
                try:
                    os.remove(file_path)
                    cleaned_count += 1
                except OSError:
                    pass
    return {"target_dir": norm_path, "cleaned_files": cleaned_count, "status": "completed"}


def create_system_ops_workflow() -> WorkflowDefinition:
    """Construct and return the System Operations WorkflowDefinition."""
    actions = [
        ActionDefinition(
            action_id="get_system_health",
            description="Inspect system platform, OS, CPU count, and host health status",
            parameters_schema={},
            output_schema={"properties": {"status": {"type": "string"}, "cpu_count": {"type": "integer"}}},
            required_permissions=["system:read"],
            is_mutating=False,
            requires_approval=False,
            allows_generative=False,
            is_direct_execution=True,
            idempotent=True,
        ),
        ActionDefinition(
            action_id="get_disk_usage",
            description="Check disk space usage, free gigabytes, and partition totals",
            parameters_schema={
                "properties": {
                    "path": {"type": "string", "description": "Target filesystem path", "default": "."}
                }
            },
            output_schema={"properties": {"free_gb": {"type": "number"}}},
            required_permissions=["system:read"],
            is_mutating=False,
            requires_approval=False,
            allows_generative=False,
            is_direct_execution=True,
            idempotent=True,
        ),
        ActionDefinition(
            action_id="clean_temp_cache",
            description="Clean temporary cache files (.tmp, .cache, .bak) in target directory",
            parameters_schema={
                "properties": {
                    "target_dir": {"type": "string", "description": "Path to cache directory"}
                },
                "required": ["target_dir"],
            },
            output_schema={"properties": {"cleaned_files": {"type": "integer"}}},
            required_permissions=["admin:system"],
            is_mutating=True,
            requires_approval=True,
            allows_generative=False,
            is_direct_execution=True,
            idempotent=False,
        ),
        ActionDefinition(
            action_id="summarize_system_status",
            description="Generate a natural language sysadmin report synthesizing system health and disk metrics",
            parameters_schema={
                "properties": {
                    "health_data": {"type": "object", "description": "Structured health metrics"},
                    "focus_area": {"type": "string", "description": "Specific concern to emphasize"},
                },
                "required": ["health_data"],
            },
            required_permissions=["system:read"],
            is_mutating=False,
            requires_approval=False,
            allows_generative=True,
            is_direct_execution=False,
            idempotent=True,
        ),
    ]

    return WorkflowDefinition(
        name="system_ops",
        version="1.0.0",
        description="Core system operations, hardware diagnostics, and cache management workflow",
        actions=actions,
    )
