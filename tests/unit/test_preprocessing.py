"""Unit tests for preprocessing, validation, and feature extraction."""

import pytest

from slothswitch.preprocessing import (
    RoutingFeatures,
    ValidationError,
    extract_features,
    redact_sensitive,
    validate_request,
)
from slothswitch.schemas import RoutingRequest


def test_validate_request_valid():
    req = RoutingRequest(request_id="r1", content="Hello world")
    validate_request(req, max_length=100, supported_content_types=["text/plain"])


def test_validate_request_empty_content():
    req = RoutingRequest(request_id="r1", content="   ")
    with pytest.raises(ValidationError, match="empty"):
        validate_request(req)


def test_validate_request_length_exceeded():
    req = RoutingRequest(request_id="r1", content="a" * 105)
    with pytest.raises(ValidationError, match="exceeds maximum"):
        validate_request(req, max_length=100)


def test_validate_request_unsupported_content_type():
    req = RoutingRequest(request_id="r1", content="image data", content_type="image/png")
    with pytest.raises(ValidationError, match="Unsupported content type"):
        validate_request(req, supported_content_types=["text/plain"])


def test_redact_sensitive_email():
    text = "Please reach out to support@example.com for refund inquiries."
    redacted = redact_sensitive(text)
    assert "[REDACTED_EMAIL]" in redacted
    assert "support@example.com" not in redacted


def test_redact_sensitive_phone():
    text = "Call me at 555-123-4567 regarding my account."
    redacted = redact_sensitive(text)
    assert "[REDACTED_PHONE]" in redacted
    assert "555-123-4567" not in redacted


def test_redact_sensitive_card():
    text = "Payment card: 4111 2222 3333 4444."
    redacted = redact_sensitive(text)
    assert "[REDACTED_CARD]" in redacted
    assert "4111 2222 3333 4444" not in redacted


def test_redact_sensitive_api_key():
    text = "Key is sk-abcdef1234567890abcdef123456"
    redacted = redact_sensitive(text)
    assert "[REDACTED_KEY]" in redacted
    assert "abcdef1234567890" not in redacted


def test_extract_features_no_redacted_summary():
    req = RoutingRequest(
        request_id="r1",
        content="How do I reset my password? Here is the traceback ```error```",
    )
    features = extract_features(req, include_redacted_summary=False)
    assert isinstance(features, RoutingFeatures)
    assert features.char_count == len(req.content)
    assert features.word_count > 0
    assert features.has_question_mark is True
    assert features.has_code_block is True
    assert "account" in features.category_hints
    assert "technical" in features.category_hints
    assert features.redacted_summary == ""  # Raw/summary text not retained


def test_extract_features_with_redacted_summary():
    req = RoutingRequest(
        request_id="r2",
        content="Invoice question for customer user@test.com",
    )
    features = extract_features(req, include_redacted_summary=True, summary_max_length=50)
    assert "[REDACTED_EMAIL]" in features.redacted_summary
    assert "user@test.com" not in features.redacted_summary
    assert "billing" in features.category_hints
