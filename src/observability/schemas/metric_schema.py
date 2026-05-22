"""Runtime metric schemas — SLO/SLI definitions, metric types."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class MetricType(str, Enum):
    GAUGE = "gauge"
    COUNTER = "counter"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class SLIDefinition(BaseModel):
    """Service Level Indicator definition."""

    name: str
    description: str
    metric_type: MetricType
    target_value: float
    unit: str = ""
    window_minutes: int = Field(default=5, ge=1)


class SLOStatus(BaseModel):
    """Current SLO compliance status for one indicator."""

    sli: SLIDefinition
    current_value: float
    compliant: bool
    budget_remaining_pct: float = Field(..., ge=0.0, le=100.0)
    burn_rate: float = Field(default=0.0, description="How fast we're burning error budget")


class RuntimeMetric(BaseModel):
    """A single runtime metric data point."""

    name: str
    type: MetricType
    value: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tags: dict[str, str] = Field(default_factory=dict)
    unit: str = ""
    mission_id: str | None = None
    trace_id: str | None = None


# Canonical SLO definitions for OMNIS
CANONICAL_SLOS: list[SLIDefinition] = [
    SLIDefinition(
        name="mission_success_rate",
        description="Percentage of missions that complete successfully",
        metric_type=MetricType.GAUGE,
        target_value=95.0,
        unit="%",
        window_minutes=60,
    ),
    SLIDefinition(
        name="task_success_rate",
        description="Percentage of tasks within a mission that complete",
        metric_type=MetricType.GAUGE,
        target_value=98.0,
        unit="%",
        window_minutes=15,
    ),
    SLIDefinition(
        name="provider_availability",
        description="Percentage of provider calls that succeed",
        metric_type=MetricType.GAUGE,
        target_value=99.5,
        unit="%",
        window_minutes=5,
    ),
    SLIDefinition(
        name="p95_latency_ms",
        description="95th percentile end-to-end latency",
        metric_type=MetricType.HISTOGRAM,
        target_value=5000.0,
        unit="ms",
        window_minutes=15,
    ),
    SLIDefinition(
        name="event_bus_latency_ms",
        description="Event bus publish-to-consume latency",
        metric_type=MetricType.HISTOGRAM,
        target_value=500.0,
        unit="ms",
        window_minutes=5,
    ),
    SLIDefinition(
        name="health_score",
        description="Composite health score",
        metric_type=MetricType.GAUGE,
        target_value=0.90,
        unit="",
        window_minutes=5,
    ),
    SLIDefinition(
        name="cost_per_mission_usd",
        description="Average cost per completed mission",
        metric_type=MetricType.SUMMARY,
        target_value=1.00,
        unit="USD",
        window_minutes=60,
    ),
    SLIDefinition(
        name="hallucination_rate",
        description="Rate of detected hallucinations per provider call",
        metric_type=MetricType.GAUGE,
        target_value=0.02,
        unit="%",
        window_minutes=30,
    ),
]
