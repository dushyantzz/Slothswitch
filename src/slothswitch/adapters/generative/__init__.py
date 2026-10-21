"""Generative adapters package for SlothSwitch."""

from slothswitch.adapters.generative.base import GenerativeTaskAdapter
from slothswitch.adapters.generative.gemma_local import (
    LocalGemmaAdapter,
    MockGenerativeAdapter,
    sanitize_untrusted_content,
)

__all__ = [
    "GenerativeTaskAdapter",
    "LocalGemmaAdapter",
    "MockGenerativeAdapter",
    "sanitize_untrusted_content",
]
