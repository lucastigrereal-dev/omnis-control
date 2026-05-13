"""P16 Observability Local — deterministic data models."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class MetricType(str, Enum):
    GAUGE = "gauge"
    COUNTER = "counter"
    HISTOGRAM = "histogram"


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class RunLogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class TraceEvent:
    """Deterministic trace event — no real OpenTelemetry."""
    name: str
    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    span_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    parent_span_id: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = "ok"
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricPoint:
    """Deterministic metric point — no real metrics backend."""
    name: str
    value: float
    unit: str = "count"
    metric_type: MetricType = MetricType.GAUGE
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    labels: dict[str, str] = field(default_factory=dict)


@dataclass
class RunLogEntry:
    """Deterministic run log entry — no real logging to files/services."""
    run_id: str
    message: str
    level: RunLogLevel = RunLogLevel.INFO
    module: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthSignal:
    """Deterministic health check signal — no real probes."""
    component: str
    status: HealthStatus = HealthStatus.HEALTHY
    message: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    checks: dict[str, bool] = field(default_factory=dict)


@dataclass
class ObservabilitySnapshot:
    """Aggregate snapshot of all observability signals — deterministic only."""
    traces: list[TraceEvent] = field(default_factory=list)
    metrics: list[MetricPoint] = field(default_factory=list)
    logs: list[RunLogEntry] = field(default_factory=list)
    health_signals: list[HealthSignal] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class AlertPlan:
    """Alert as a plan only — no real alerts fired."""
    alert_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    title: str = ""
    description: str = ""
    severity: AlertSeverity = AlertSeverity.INFO
    condition: str = ""
    suggested_action: str = ""
    source: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
