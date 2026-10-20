"""Input preprocessing and feature extraction for routing decisions.

This module handles:
- Input validation (size, content type)
- Privacy-aware redaction of sensitive information
- Routing feature extraction (without retaining raw content)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from slothswitch.schemas import RoutingRequest

# ---------------------------------------------------------------------------
# Redaction patterns
# ---------------------------------------------------------------------------

_REDACTION_PATTERNS: list[tuple[str, str]] = [
    # Email addresses
    (r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "[REDACTED_EMAIL]"),
    # Phone numbers (simple patterns)
    (r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "[REDACTED_PHONE]"),
    # Credit card–like sequences
    (r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "[REDACTED_CARD]"),
    # API key–like strings (long hex/base64)
    (r"\b(?:sk-|pk-|api[-_]?key[-_:]?\s*)[a-zA-Z0-9]{20,}\b", "[REDACTED_KEY]"),
]


def redact_sensitive(text: str) -> str:
    """Replace common sensitive patterns with placeholders."""
    for pattern, replacement in _REDACTION_PATTERNS:
        text = re.sub(pattern, replacement, text)
    return text


# ---------------------------------------------------------------------------
# Routing features
# ---------------------------------------------------------------------------

@dataclass
class RoutingFeatures:
    """Extracted features used by the decision model for routing.

    These are derived from the request without retaining the full raw content,
    unless explicitly enabled via configuration.
    """

    request_id: str
    char_count: int = 0
    word_count: int = 0
    has_question_mark: bool = False
    has_code_block: bool = False
    is_deep_technical: bool = False
    missing_required_identifier: bool = False
    is_malformed_noise: bool = False
    category_hints: list[str] = field(default_factory=list)
    language_hint: str = "en"
    redacted_summary: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class ValidationError(Exception):
    """Raised when a request fails input validation."""


def validate_request(
    request: RoutingRequest,
    max_length: int = 10_000,
    supported_content_types: list[str] | None = None,
) -> None:
    """Validate an incoming request against configured constraints.

    Raises ValidationError if the request is invalid.
    """
    if supported_content_types is None:
        supported_content_types = ["text/plain"]

    if not request.content or not request.content.strip():
        raise ValidationError("Request content is empty")

    if len(request.content) > max_length:
        raise ValidationError(
            f"Request content length {len(request.content)} exceeds maximum {max_length}"
        )

    if request.content_type not in supported_content_types:
        raise ValidationError(
            f"Unsupported content type '{request.content_type}'; "
            f"supported: {supported_content_types}"
        )


# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------

def extract_features(
    request: RoutingRequest,
    include_redacted_summary: bool = False,
    summary_max_length: int = 200,
) -> RoutingFeatures:
    """Extract routing features from a validated request.

    By default the raw content is NOT retained. When `include_redacted_summary`
    is True, a truncated/redacted summary is stored for the decision model.
    """
    content = request.content

    features = RoutingFeatures(
        request_id=request.request_id,
        char_count=len(content),
        word_count=len(content.split()),
        has_question_mark="?" in content,
        has_code_block="```" in content or "    " in content,
    )

    # Check metadata for category hints
    if "category" in request.metadata and isinstance(request.metadata["category"], str):
        features.category_hints.append(request.metadata["category"])
    elif "categories" in request.metadata and isinstance(request.metadata["categories"], list):
        features.category_hints.extend(request.metadata["categories"])

    # Simple category hints from keywords
    lower = content.lower()
    keyword_categories = {
        "billing": ["invoice", "charge", "refund", "payment", "billing", "subscription"],
        "technical": ["error", "bug", "crash", "not working", "broken", "exception", "traceback"],
        "account": ["password", "login", "account", "profile", "sign in", "sign up"],
        "general": ["hello", "hi", "help", "question", "how do i"],
        "legal": ["legal", "lawsuit", "gdpr", "compliance", "dpa", "contract", "counsel"],
        "security": ["security", "vulnerability", "cve", "breach", "hack", "exploit", "secops"],
        "financial": ["dispute", "chargeback", "fraud", "sla breach", "financial claim"],
    }
    for category, keywords in keyword_categories.items():
        if any(kw in lower for kw in keywords) and category not in features.category_hints:
            features.category_hints.append(category)

    # Extract deep technical reasoning signals
    deep_tech_keywords = [
        "kubernetes", "ingress", "microservices", "dynamodb", "eventbridge",
        "postgres", "concurrency", "lock-free", "circular buffer", "zero-downtime",
        "pg_partman", "rails", "grpc", "traceback", "deadlock", "race condition",
        "profiling", "memory leak", "multi-threaded", "cache-line", "distributed",
        "502 bad gateway", "envoy", "idempotent", "schema migration", "buffer",
        "single-table design", "mutex", "coroutine", "thread pool", "asyncio",
    ]
    features.is_deep_technical = (
        any(kw in lower for kw in deep_tech_keywords)
        or features.has_code_block
        or "traceback (" in lower
    )

    # Missing parameters for action requests (clarification triggers)
    has_specific_id = bool(
        re.search(r"#\d+|\b[A-Z0-9]{6,}\b|\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b", content)
    )
    action_clarify_triggers = [
        "reissue the invoice", "reissue invoice", "reset my two-factor", "reset 2fa",
        "cancel my subscription", "cancel subscription", "webhook is not receiving",
        "not receiving payloads", "can you clarify", "what do you mean",
    ]
    features.missing_required_identifier = (
        any(act in lower for act in action_clarify_triggers) and not has_specific_id
    )

    # Malformed noise
    punct_count = sum(1 for c in content if not c.isalnum() and not c.isspace())
    punct_ratio = punct_count / max(1, len(content))
    alphanumeric_words = [w for w in re.findall(r"[a-zA-Z0-9]+", lower) if len(w) > 1]
    features.is_malformed_noise = (
        punct_ratio > 0.35
        or (len(alphanumeric_words) > 0 and all(len(w) > 12 and not any(v in w for v in "aeiou") for w in alphanumeric_words))
        or (len(content) > 15 and punct_ratio > 0.25 and len(alphanumeric_words) <= 2)
    )

    if include_redacted_summary:
        redacted = redact_sensitive(content)
        features.redacted_summary = redacted[:summary_max_length]

    return features
