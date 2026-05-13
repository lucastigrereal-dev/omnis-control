"""P16 Observability Local — deterministic planner service."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from src.observability_local.models import (
    AlertPlan,
    AlertSeverity,
    HealthSignal,
    HealthStatus,
    MetricPoint,
    MetricType,
    ObservabilitySnapshot,
    RunLogEntry,
    RunLogLevel,
    TraceEvent,
)

_SENSITIVE_KEYS = frozenset({"token", "secret", "password", "api_key", "bearer", "authorization", "access_key", "private_key"})
_SENSITIVE_SEGMENTS = frozenset({
    "token", "secret", "password", "api_key", "bearer",
    "authorization", "access_key", "private_key",
})


def _is_sensitive_key(key: str) -> bool:
    """Check if any sensitive segment appears within the key (case-insensitive, supports underscore/hyphen delimiters)."""
    lower = key.lower()
    for segment in _SENSITIVE_SEGMENTS:
        if segment in lower:
            return True
    return False


class ObservabilityPlanner:
    """Deterministic observability planner — no real side effects, no external services."""

    @staticmethod
    def record_trace_event_plan(
        name: str,
        attributes: dict[str, Any] | None = None,
        span_id: str | None = None,
        parent_span_id: str | None = None,
        trace_id: str | None = None,
    ) -> TraceEvent:
        """Build a dry-run TraceEvent plan. No real tracer called."""
        return TraceEvent(
            name=name,
            trace_id=trace_id or uuid.uuid4().hex,
            span_id=span_id or uuid.uuid4().hex[:16],
            parent_span_id=parent_span_id,
            attributes=ObservabilityPlanner.sanitize_observability_payload(
                attributes or {}
            ),
        )

    @staticmethod
    def build_metric_point(
        name: str,
        value: float,
        unit: str = "count",
        labels: dict[str, str] | None = None,
        metric_type: MetricType = MetricType.GAUGE,
    ) -> MetricPoint:
        """Build a dry-run MetricPoint. No real metrics backend called."""
        return MetricPoint(
            name=name,
            value=value,
            unit=unit,
            metric_type=metric_type,
            labels=ObservabilityPlanner.sanitize_observability_payload(
                labels or {}
            ),
        )

    @staticmethod
    def build_run_log_entry(
        run_id: str,
        message: str,
        level: RunLogLevel = RunLogLevel.INFO,
        module: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> RunLogEntry:
        """Build a dry-run RunLogEntry. No real log written to disk or service."""
        return RunLogEntry(
            run_id=run_id,
            message=message,
            level=level,
            module=module,
            metadata=ObservabilityPlanner.sanitize_observability_payload(
                metadata or {}
            ),
        )

    @staticmethod
    def build_health_snapshot(
        components: list[dict[str, Any]] | None = None,
    ) -> ObservabilitySnapshot:
        """Build a dry-run ObservabilitySnapshot with health signals."""
        signals: list[HealthSignal] = []
        for comp in (components or []):
            signals.append(
                HealthSignal(
                    component=comp.get("component", "unknown"),
                    status=HealthStatus(comp.get("status", "healthy")),
                    message=comp.get("message", ""),
                    checks=comp.get("checks", {}),
                )
            )
        return ObservabilitySnapshot(health_signals=signals)

    @staticmethod
    def plan_alerts(
        snapshot: ObservabilitySnapshot,
        thresholds: dict[str, Any] | None = None,
    ) -> list[AlertPlan]:
        """Generate alert plans from an ObservabilitySnapshot. No real alerts fired."""
        plans: list[AlertPlan] = []
        thresholds = thresholds or {}

        for sig in snapshot.health_signals:
            if sig.status == HealthStatus.UNHEALTHY:
                plans.append(
                    AlertPlan(
                        title=f"Unhealthy component: {sig.component}",
                        description=sig.message or f"{sig.component} is unhealthy",
                        severity=AlertSeverity.CRITICAL,
                        condition=f"health_status == unhealthy for {sig.component}",
                        suggested_action=f"Investigate {sig.component} immediately",
                        source="health_signal",
                    )
                )
            elif sig.status == HealthStatus.DEGRADED:
                plans.append(
                    AlertPlan(
                        title=f"Degraded component: {sig.component}",
                        description=sig.message or f"{sig.component} is degraded",
                        severity=AlertSeverity.WARNING,
                        condition=f"health_status == degraded for {sig.component}",
                        suggested_action=f"Monitor {sig.component} closely",
                        source="health_signal",
                    )
                )

        for metric in snapshot.metrics:
            threshold = thresholds.get(metric.name)
            if threshold is not None and metric.value > threshold:
                plans.append(
                    AlertPlan(
                        title=f"Metric threshold breached: {metric.name}",
                        description=f"{metric.name}={metric.value} > threshold={threshold}",
                        severity=AlertSeverity.WARNING,
                        condition=f"{metric.name} > {threshold}",
                        suggested_action=f"Investigate spike in {metric.name}",
                        source="metric",
                    )
                )

        return plans

    @staticmethod
    def sanitize_observability_payload(payload: dict[str, Any]) -> dict[str, Any]:
        """Redact sensitive keys from an observability payload."""
        if not isinstance(payload, dict):
            return payload

        sanitized: dict[str, Any] = {}
        for key, value in payload.items():
            if _is_sensitive_key(key):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, dict):
                sanitized[key] = ObservabilityPlanner.sanitize_observability_payload(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    ObservabilityPlanner.sanitize_observability_payload(v)
                    if isinstance(v, dict)
                    else "[REDACTED]" if isinstance(v, str) and _SENSITIVE_PATTERN.search(v)
                    else v
                    for v in value
                ]
            elif isinstance(value, str) and _is_sensitive_key(value):
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = value
        return sanitized


def build_snapshot_from_planner(
    traces: list[dict[str, Any]] | None = None,
    metrics: list[dict[str, Any]] | None = None,
    logs: list[dict[str, Any]] | None = None,
    health: list[dict[str, Any]] | None = None,
) -> ObservabilitySnapshot:
    """Convenience: build a full snapshot from raw dicts using the planner."""
    planner = ObservabilityPlanner
    snapshot = ObservabilitySnapshot()

    for t in (traces or []):
        snapshot.traces.append(
            planner.record_trace_event_plan(
                name=t.get("name", "unknown"),
                attributes=t.get("attributes"),
                span_id=t.get("span_id"),
                parent_span_id=t.get("parent_span_id"),
                trace_id=t.get("trace_id"),
            )
        )

    for m in (metrics or []):
        snapshot.metrics.append(
            planner.build_metric_point(
                name=m.get("name", "unknown"),
                value=m.get("value", 0.0),
                unit=m.get("unit", "count"),
                labels=m.get("labels"),
                metric_type=MetricType(m.get("metric_type", "gauge")),
            )
        )

    for l in (logs or []):
        snapshot.logs.append(
            planner.build_run_log_entry(
                run_id=l.get("run_id", ""),
                message=l.get("message", ""),
                level=RunLogLevel(l.get("level", "info")),
                module=l.get("module", ""),
                metadata=l.get("metadata"),
            )
        )

    for h in (health or []):
        snapshot.health_signals.append(
            HealthSignal(
                component=h.get("component", "unknown"),
                status=HealthStatus(h.get("status", "healthy")),
                message=h.get("message", ""),
                checks=h.get("checks", {}),
            )
        )

    return snapshot
