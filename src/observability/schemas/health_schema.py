"""Health score schemas — composite health, anomaly detection, runtime scoring."""

from datetime import datetime, timezone
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class HealthComponent(BaseModel):
    """Individual health signal from a subsystem."""

    name: str = Field(..., description="e.g. event_bus, redis, postgres, docker")
    status: HealthStatus
    score: float = Field(..., ge=0.0, le=1.0, description="0=dead, 1=perfect")
    weight: float = Field(default=1.0, ge=0.0, le=1.0)
    message: str = ""
    last_checked: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    latency_ms: float | None = Field(default=None, ge=0.0)
    error_count: int = Field(default=0, ge=0)
    metadata: dict = Field(default_factory=dict)


class AnomalySignal(BaseModel):
    """Anomaly detected by the health scoring engine."""

    signal_name: str
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    current_value: float
    expected_range: tuple[float, float]
    deviation_pct: float = Field(..., description="How far from expected (0-100+)")
    severity: Literal["low", "medium", "high", "critical"] = "low"
    metric: str = ""
    context: dict = Field(default_factory=dict)


class HealthScore(BaseModel):
    """Composite health score for the entire OMNIS system.

    Computed as weighted average of component scores:
        total = sum(score_i * weight_i) / sum(weight_i)

    Thresholds:
        >= 0.90 → healthy
        >= 0.70 → degraded
        >= 0.40 → unhealthy
        < 0.40  → critical
    """

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    overall_score: float = Field(..., ge=0.0, le=1.0)
    status: HealthStatus
    components: list[HealthComponent] = Field(default_factory=list)
    anomalies: list[AnomalySignal] = Field(default_factory=list)

    # Trend
    previous_score: float | None = None
    trend: Literal["improving", "stable", "degrading", "unknown"] = "unknown"

    # Uptime
    uptime_pct_24h: float | None = Field(default=None, ge=0.0, le=100.0)
    uptime_pct_7d: float | None = Field(default=None, ge=0.0, le=100.0)

    # SLI/SLO
    slo_compliance_pct: float | None = Field(default=None, ge=0.0, le=100.0)

    @classmethod
    def compute(
        cls, components: list[HealthComponent], previous_score: float | None = None
    ) -> "HealthScore":
        if not components:
            return cls(overall_score=1.0, status=HealthStatus.UNKNOWN)

        total_weight = sum(c.weight for c in components)
        if total_weight == 0:
            return cls(overall_score=0.0, status=HealthStatus.CRITICAL)

        score = sum(c.score * c.weight for c in components) / total_weight

        if score >= 0.90:
            status = HealthStatus.HEALTHY
        elif score >= 0.70:
            status = HealthStatus.DEGRADED
        elif score >= 0.40:
            status = HealthStatus.UNHEALTHY
        else:
            status = HealthStatus.CRITICAL

        trend = "unknown"
        if previous_score is not None:
            delta = score - previous_score
            if delta > 0.02:
                trend = "improving"
            elif delta < -0.02:
                trend = "degrading"
            else:
                trend = "stable"

        return cls(
            overall_score=round(score, 4),
            status=status,
            components=components,
            previous_score=previous_score,
            trend=trend,
        )
