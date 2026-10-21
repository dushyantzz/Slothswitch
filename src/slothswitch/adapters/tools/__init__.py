"""Tool adapters package for SlothSwitch."""

from slothswitch.adapters.tools.base import ToolAdapter
from slothswitch.adapters.tools.github import GitHubToolAdapter
from slothswitch.adapters.tools.system_ops_tool import SystemOpsToolAdapter

__all__ = ["GitHubToolAdapter", "SystemOpsToolAdapter", "ToolAdapter"]
