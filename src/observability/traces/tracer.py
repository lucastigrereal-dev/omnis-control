"""Distributed tracing — span lifecycle, context propagation.

Ties together events from different processes/worktrees into a single trace.
Propagates W3C Trace Context across boundaries.
"""

import logging
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

from ..schemas.trace_schema import SpanContext, SpanEvent, SpanKind, TraceSpan

logger = logging.getLogger(__name__)

_current_span: ContextVar[SpanContext | None] = ContextVar("trace_span", default=None)


class Tracer:
    """Distributed tracer with span context propagation.

    Usage:
        tracer = Tracer()

        with tracer.start_span("mission_execution") as span:
            span.add_event("step_started", {"step": "decompose"})
            # ... do work ...
            span.set_ok()

        # Propagate to child process:
        headers = tracer.current_context.to_headers()
        subprocess.run(..., env={"TRACEPARENT": headers["traceparent"]})
    """

    def __init__(self):
        self._spans: dict[str, TraceSpan] = {}

    @property
    def current_context(self) -> SpanContext:
        ctx = _current_span.get()
        if ctx is None:
            ctx = SpanContext()
            _current_span.set(ctx)
        return ctx

    def start_span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        parent_context: SpanContext | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> "SpanHandle":
        parent = parent_context or self.current_context
        child_ctx = parent.child_span()
        _current_span.set(child_ctx)

        span = TraceSpan(
            trace_id=child_ctx.trace_id,
            span_id=child_ctx.span_id,
            parent_span_id=child_ctx.parent_span_id,
            name=name,
            kind=kind,
            attributes=attributes or {},
        )
        self._spans[child_ctx.span_id] = span
        return SpanHandle(span, self)

    def get_span(self, span_id: str) -> TraceSpan | None:
        return self._spans.get(span_id)

    def get_trace(self, trace_id: str) -> list[TraceSpan]:
        return [s for s in self._spans.values() if s.trace_id == trace_id]


class SpanHandle:
    """Context manager for a span."""

    def __init__(self, span: TraceSpan, tracer: Tracer):
        self.span = span
        self._tracer = tracer

    def __enter__(self) -> "SpanHandle":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.span.end_time = datetime.now(timezone.utc)
        if exc_type is not None:
            self.span.status = "error"
        elif self.span.status == "unset":
            self.span.status = "ok"

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        self.span.events.append(SpanEvent(name=name, attributes=attributes or {}))

    def set_attribute(self, key: str, value: Any) -> None:
        self.span.attributes[key] = value

    def set_ok(self) -> None:
        self.span.status = "ok"

    def set_error(self) -> None:
        self.span.status = "error"

    @property
    def trace_id(self) -> str:
        return self.span.trace_id

    @property
    def span_id(self) -> str:
        return self.span.span_id


_tracer: Tracer | None = None


def get_tracer() -> Tracer:
    global _tracer
    if _tracer is None:
        _tracer = Tracer()
    return _tracer
