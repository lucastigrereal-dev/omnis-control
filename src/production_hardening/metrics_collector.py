"""W176 — Metrics Collector: lightweight in-memory metrics for OMNIS modules."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from src.remote_control.models import _new_id, _now_iso


class MetricType(str, Enum):
    COUNTER = "COUNTER"
    GAUGE = "GAUGE"
    HISTOGRAM = "HISTOGRAM"


# ---------------------------------------------------------------------------
# Metric
# ---------------------------------------------------------------------------

@dataclass
class MetricPoint:
    name: str
    value: float
    metric_type: MetricType = MetricType.GAUGE
    module: str = ""
    tags: dict = field(default_factory=dict)
    recorded_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "value": self.value,
            "metric_type": self.metric_type.value,
            "module": self.module,
            "tags": self.tags,
            "recorded_at": self.recorded_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "MetricPoint":
        return cls(
            name=d.get("name", ""),
            value=d.get("value", 0.0),
            metric_type=MetricType(d.get("metric_type", "GAUGE")),
            module=d.get("module", ""),
            tags=d.get("tags", {}),
            recorded_at=d.get("recorded_at", _now_iso()),
        )


# ---------------------------------------------------------------------------
# Aggregated metric
# ---------------------------------------------------------------------------

@dataclass
class MetricSummary:
    name: str
    count: int = 0
    total: float = 0.0
    min_val: float = float("inf")
    max_val: float = float("-inf")
    last_val: float = 0.0

    @property
    def avg(self) -> float:
        return round(self.total / self.count, 4) if self.count else 0.0

    def update(self, value: float) -> None:
        self.count += 1
        self.total += value
        self.last_val = value
        if value < self.min_val:
            self.min_val = value
        if value > self.max_val:
            self.max_val = value

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "count": self.count,
            "total": round(self.total, 4),
            "min": round(self.min_val, 4) if self.count else 0.0,
            "max": round(self.max_val, 4) if self.count else 0.0,
            "avg": self.avg,
            "last": round(self.last_val, 4),
        }


# ---------------------------------------------------------------------------
# Collector
# ---------------------------------------------------------------------------

class MetricsCollector:
    """Collects and aggregates module metrics in memory."""

    def __init__(self, module: str = "omnis") -> None:
        self.module = module
        self._points: list[MetricPoint] = []
        self._summaries: dict[str, MetricSummary] = {}
        self._counters: dict[str, float] = {}

    # ------------------------------------------------------------------
    def record(self, name: str, value: float, metric_type: MetricType = MetricType.GAUGE,
               tags: Optional[dict] = None) -> MetricPoint:
        point = MetricPoint(name=name, value=value, metric_type=metric_type,
                            module=self.module, tags=tags or {})
        self._points.append(point)
        self._summaries.setdefault(name, MetricSummary(name=name)).update(value)
        return point

    def increment(self, name: str, by: float = 1.0) -> float:
        self._counters[name] = self._counters.get(name, 0.0) + by
        self.record(name, self._counters[name], MetricType.COUNTER)
        return self._counters[name]

    def gauge(self, name: str, value: float, tags: Optional[dict] = None) -> MetricPoint:
        return self.record(name, value, MetricType.GAUGE, tags)

    def histogram(self, name: str, value: float, tags: Optional[dict] = None) -> MetricPoint:
        return self.record(name, value, MetricType.HISTOGRAM, tags)

    def time_ms(self, name: str, duration_ms: float) -> MetricPoint:
        return self.histogram(f"{name}.duration_ms", duration_ms)

    # ------------------------------------------------------------------
    def summary(self, name: str) -> Optional[MetricSummary]:
        return self._summaries.get(name)

    def all_summaries(self) -> dict[str, dict]:
        return {name: s.to_dict() for name, s in self._summaries.items()}

    def counter_value(self, name: str) -> float:
        return self._counters.get(name, 0.0)

    def points(self, name: Optional[str] = None) -> list[MetricPoint]:
        if name is None:
            return list(self._points)
        return [p for p in self._points if p.name == name]

    def reset(self) -> None:
        self._points.clear()
        self._summaries.clear()
        self._counters.clear()

    def snapshot(self) -> dict:
        return {
            "module": self.module,
            "total_points": len(self._points),
            "metrics": list(self._summaries.keys()),
            "summaries": self.all_summaries(),
            "counters": dict(self._counters),
        }
