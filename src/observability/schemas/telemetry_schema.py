"""Telemetry schemas — provider observability, token tracking, latency."""

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class TokenUsage(BaseModel):
    """Token consumption record for a single provider call."""

    model_config = {"frozen": True}

    provider: str = Field(..., description="e.g. anthropic, openai, gemini")
    model: str = Field(..., description="e.g. claude-opus-4-7, gpt-4o")
    input_tokens: int = Field(..., ge=0)
    output_tokens: int = Field(..., ge=0)
    cache_read_tokens: int = Field(default=0, ge=0)
    cache_write_tokens: int = Field(default=0, ge=0)
    reasoning_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int = Field(..., ge=0)
    cost_usd: float = Field(..., ge=0.0)


class LatencyRecord(BaseModel):
    """Latency measurement for a single operation."""

    model_config = {"frozen": True}

    operation: str
    duration_ms: float = Field(..., ge=0.0)
    ttfb_ms: float | None = Field(default=None, ge=0.0)
    phase: Literal["pre_process", "inference", "post_process", "total"] = "total"


class ProviderMetric(BaseModel):
    """Aggregated metric for a single provider call."""

    model_config = {"frozen": True}

    call_id: str = Field(default_factory=lambda: str(uuid4()))
    provider: str
    model: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    success: bool
    status_code: int | None = None
    error_type: str | None = None
    error_message: str | None = None
    retry_count: int = Field(default=0, ge=0)
    tokens: TokenUsage | None = None
    latency: LatencyRecord | None = None
    hallucination_score: float | None = Field(default=None, ge=0.0, le=1.0)
    mission_id: str | None = None
    trace_id: str | None = None


class TelemetryPayload(BaseModel):
    """Aggregated telemetry snapshot for a time window."""

    window_start: datetime
    window_end: datetime
    total_calls: int = 0
    success_count: int = 0
    failure_count: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    hallucination_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    provider_breakdown: dict[str, "ProviderMetric"] = Field(default_factory=dict)
    retry_rate: float = Field(default=0.0, ge=0.0, le=1.0)
