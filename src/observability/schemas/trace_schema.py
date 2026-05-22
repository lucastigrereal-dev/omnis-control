"""Distributed tracing schemas — span context, trace propagation."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class SpanKind(str, Enum):
    """OpenTelemetry-compatible span kinds."""
    INTERNAL = "internal"
    CLIENT = "client"
    SERVER = "server"
    PRODUCER = "producer"
    CONSUMER = "consumer"


class SpanContext(BaseModel):
    """W3C Trace Context propagation header.

    Propagated across process boundaries (worktrees, agents, subprocesses)
    via environment variables or message headers.
    """

    trace_id: str = Field(default_factory=lambda: uuid4().hex)
    span_id: str = Field(default_factory=lambda: uuid4().hex[:16])
    parent_span_id: str | None = None
    trace_flags: int = Field(default=1, description="1 = sampled")
    tracestate: dict[str, str] = Field(default_factory=dict)

    def to_headers(self) -> dict[str, str]:
        return {
            "traceparent": f"00-{self.trace_id}-{self.span_id}-{self.trace_flags:02x}",
            "tracestate": ",".join(f"{k}={v}" for k, v in self.tracestate.items()),
        }

    @classmethod
    def from_headers(cls, headers: dict[str, str]) -> "SpanContext":
        tp = headers.get("traceparent", "00-0-0-00")
        parts = tp.split("-")
        ts_str = headers.get("tracestate", "")
        tracestate = {}
        if ts_str:
            for pair in ts_str.split(","):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    tracestate[k.strip()] = v.strip()
        return cls(
            trace_id=parts[1] if len(parts) > 1 else uuid4().hex,
            span_id=parts[2] if len(parts) > 2 else uuid4().hex[:16],
            trace_flags=int(parts[3], 16) if len(parts) > 3 else 1,
            tracestate=tracestate,
        )

    def child_span(self, span_id: str | None = None) -> "SpanContext":
        return SpanContext(
            trace_id=self.trace_id,
            span_id=span_id or uuid4().hex[:16],
            parent_span_id=self.span_id,
            trace_flags=self.trace_flags,
            tracestate=self.tracestate,
        )


class TraceSpan(BaseModel):
    """A single span in a distributed trace."""

    model_config = {"frozen": True}

    trace_id: str
    span_id: str
    parent_span_id: str | None = None
    name: str
    kind: SpanKind = SpanKind.INTERNAL
    start_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: datetime | None = None
    status: Literal["unset", "ok", "error"] = "unset"
    attributes: dict[str, Any] = Field(default_factory=dict)
    events: list["SpanEvent"] = Field(default_factory=list)
    resource: dict[str, str] = Field(default_factory=dict)

    @property
    def duration_ms(self) -> float | None:
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time).total_seconds() * 1000


class SpanEvent(BaseModel):
    """A timestamped event within a span."""

    name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    attributes: dict[str, Any] = Field(default_factory=dict)
