"""Core data schemas for SlothSwitch routing decisions and requests.

All structured types live here so that adapters and policy code share
a single source of truth for field names and validation.
"""

from __future__ import annotations

import time
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Route categories
# ---------------------------------------------------------------------------

class RouteCategory(str, Enum):
    """The candidate processing paths available to the router."""

    FAST_PATH = "FAST_PATH"
    SMALL_LLM = "SMALL_LLM"
    LARGE_LLM = "LARGE_LLM"
    CLARIFY = "CLARIFY"
    FALLBACK = "FALLBACK"
    HUMAN_REVIEW = "HUMAN_REVIEW"


# ---------------------------------------------------------------------------
# Incoming request
# ---------------------------------------------------------------------------

class RoutingRequest(BaseModel):
    """An incoming request to be routed."""

    request_id: str = Field(..., description="Unique identifier for this request")
    content: str = Field(..., description="The text content of the request")
    content_type: str = Field(default="text/plain", description="MIME type of the content")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Extra metadata")
    timestamp: float = Field(default_factory=time.time)

    # Optional explicit constraints from the caller
    allowed_routes: Optional[list[RouteCategory]] = Field(
        default=None,
        description="If set, only these routes may be selected",
    )
    max_cost_tier: Optional[int] = Field(
        default=None,
        description="If set, routes above this cost tier are excluded",
    )


# ---------------------------------------------------------------------------
# Route decision (output of the decision model / router)
# ---------------------------------------------------------------------------

class RouteDecision(BaseModel):
    """The result of the routing decision pipeline."""

    request_id: str
    chosen_route: RouteCategory
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Decision-model confidence (NOT a calibrated probability unless validated)",
    )
    reasoning: str = Field(
        default="",
        description="Short explanation of why this route was chosen",
    )
    accepted: bool = Field(
        default=True,
        description="Whether the route passed the policy acceptance gate",
    )
    fallback_reason: Optional[str] = Field(
        default=None,
        description="If a fallback was triggered, why",
    )
    decision_model: Optional[str] = Field(
        default=None,
        description="Identifier of the decision model/checkpoint used",
    )
    latency_ms: Optional[float] = Field(
        default=None,
        description="Time taken for the routing decision in milliseconds",
    )


# ---------------------------------------------------------------------------
# Task execution result
# ---------------------------------------------------------------------------

class TaskResult(BaseModel):
    """The result of executing the routed task."""

    request_id: str
    route_used: RouteCategory
    output: str = Field(default="", description="The generated response or structured result")
    success: bool = Field(default=True)
    error: Optional[str] = Field(default=None)
    model_used: Optional[str] = Field(default=None, description="Model identifier used for task")
    latency_ms: Optional[float] = Field(default=None)
    token_usage: Optional[dict[str, int]] = Field(
        default=None,
        description="Token counts (prompt_tokens, completion_tokens, total_tokens)",
    )
    estimated_cost_usd: Optional[float] = Field(
        default=None,
        description="Estimated cost; labeled simulated unless from provider billing API",
    )


# ---------------------------------------------------------------------------
# Telemetry record
# ---------------------------------------------------------------------------

class RoutingRecord(BaseModel):
    """A combined record of a routing decision and its task outcome, for evaluation."""

    request_id: str
    route_decision: RouteDecision
    task_result: Optional[TaskResult] = None
    timestamp: float = Field(default_factory=time.time)
    config_version: Optional[str] = None
