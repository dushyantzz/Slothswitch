"""Base interface for generative model adapters in SlothSwitch."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from slothswitch.schemas import TaskResult


class GenerativeTaskAdapter(ABC):
    """Abstract base class for generative language model adapters (e.g. Gemma)."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Identifier of this generative adapter and model."""
        ...

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        max_new_tokens: int = 256,
        temperature: float = 0.2,
    ) -> TaskResult:
        """Execute text generation on bounded input.

        Args:
            prompt: The text prompt.
            system_instruction: Optional system instruction or role guidance.
            max_new_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.

        Returns:
            TaskResult containing generated output, latency, and token usage.
        """
        ...

    @abstractmethod
    def health_check(self) -> bool:
        """Check if runtime and model weights are available."""
        ...

    @abstractmethod
    def summarize_pull_requests(
        self,
        repo: str,
        pull_requests: list[dict[str, Any]],
        max_tokens: int = 256,
    ) -> TaskResult:
        """Summarize pull requests with prompt injection guards."""
        ...

    @abstractmethod
    def summarize_issue_concerns(
        self,
        repo: str,
        issues: list[dict[str, Any]],
        max_tokens: int = 256,
    ) -> TaskResult:
        """Synthesize technical concerns and bug themes from issues."""
        ...

    @abstractmethod
    def generate_repository_report(
        self,
        repo: str,
        activity_data: dict[str, Any],
        max_tokens: int = 350,
    ) -> TaskResult:
        """Produce a structured activity summary report for a repository."""
        ...
