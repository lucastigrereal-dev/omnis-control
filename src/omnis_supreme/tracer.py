"""P20 OMNIS Supreme Activation — Observability tracer (thin P16 wrapper)."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

from src.observability_local.models import TraceEvent, ObservabilitySnapshot


@dataclass
class Span:
    event: TraceEvent
    _start: float = field(default_factory=time.monotonic)

    def ok(self, result: dict) -> None:
        self.event.status = "ok"
        self.event.attributes["result"] = result
        self.event.attributes["duration_ms"] = (time.monotonic() - self._start) * 1000

    def fail(self, error: Exception) -> None:
        self.event.status = "error"
        self.event.attributes["error"] = str(error)
        self.event.attributes["error_type"] = type(error).__name__
        self.event.attributes["duration_ms"] = (time.monotonic() - self._start) * 1000


class ObservabilityTracer:
    def __init__(self, mission_id: str):
        self.mission_id = mission_id
        self._spans: dict[str, Span] = {}
        self._snapshot = ObservabilitySnapshot()

    def start_span(self, step_id: str, operation: str) -> Span:
        event = TraceEvent(name=f"supreme.{operation}", span_id=step_id)
        span = Span(event=event)
        self._spans[step_id] = span
        return span

    def flush(self) -> dict:
        self._snapshot.traces = [s.event for s in self._spans.values()]
        return {
            "mission_id": self.mission_id,
            "trace_count": len(self._snapshot.traces),
            "ok_count": sum(1 for t in self._snapshot.traces if t.status == "ok"),
            "error_count": sum(1 for t in self._snapshot.traces if t.status == "error"),
            "traces": [{"span_id": t.span_id, "name": t.name, "status": t.status, "attributes": t.attributes} for t in self._snapshot.traces],
        }
