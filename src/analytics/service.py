"""P13 Analytics/BI — deterministic services (zero LLM, zero network, zero DB)."""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import Any

from src.analytics.errors import (
    DatasetEmptyError,
    DatasetSchemaMismatchError,
    InvalidMetricError,
)
from src.analytics.models import (
    AnalyticsDataset,
    DashboardSpec,
    MetricDefinition,
    MetricEvent,
    ReportSpec,
    VALID_AGGREGATIONS,
    _now_iso,
)


# ═══════════════════════════════════════════════════════════════
# ValidationResult
# ═══════════════════════════════════════════════════════════════

@dataclass
class ValidationResult:
    """Composite result for validation operations."""
    valid: bool
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.valid and len(self.issues) == 0

    @classmethod
    def success(cls, warnings: list[str] | None = None) -> ValidationResult:
        return cls(valid=True, warnings=warnings or [])

    @classmethod
    def failure(cls, issues: list[str]) -> ValidationResult:
        return cls(valid=False, issues=issues)


# ═══════════════════════════════════════════════════════════════
# MetricSummary
# ═══════════════════════════════════════════════════════════════

@dataclass
class MetricSummary:
    """Summary statistics for a collection of metric events."""
    metric_id: str
    count: int
    sum: float = 0.0
    avg: float = 0.0
    min: float = 0.0
    max: float = 0.0
    median: float = 0.0
    std_dev: float = 0.0

    @classmethod
    def compute(cls, metric_id: str, values: list[float]) -> MetricSummary:
        if not values:
            return cls(metric_id=metric_id, count=0)
        return cls(
            metric_id=metric_id,
            count=len(values),
            sum=sum(values),
            avg=statistics.mean(values),
            min=min(values),
            max=max(values),
            median=statistics.median(values),
            std_dev=statistics.stdev(values) if len(values) >= 2 else 0.0,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_id": self.metric_id,
            "count": self.count,
            "sum": self.sum,
            "avg": self.avg,
            "min": self.min,
            "max": self.max,
            "median": self.median,
            "std_dev": self.std_dev,
        }


# ═══════════════════════════════════════════════════════════════
# AnalyticsPlanner
# ═══════════════════════════════════════════════════════════════

class AnalyticsPlanner:
    """Deterministic analytics planner — dry-run by default.

    Plans metrics, builds dashboard/report specs, summarizes data.
    Zero LLM. Zero network. Zero database.
    """

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self._planned_metrics: list[MetricDefinition] = []

    # ── Metric planning ──────────────────────────────────────

    def plan_metric(
        self,
        name: str,
        description: str,
        category: str,
        aggregation: str,
        unit: str,
        dimensions: list[str] | None = None,
        filters: dict[str, str] | None = None,
        target: float | None = None,
    ) -> MetricDefinition:
        metric = MetricDefinition.new(
            name=name,
            description=description,
            category=category,
            aggregation=aggregation,
            unit=unit,
            dimensions=dimensions,
            filters=filters,
            target=target,
        )
        self._planned_metrics.append(metric)
        return metric

    # ── Dashboard building ───────────────────────────────────

    def build_dashboard_spec(
        self,
        title: str,
        description: str,
        metrics: list[MetricDefinition] | None = None,
        layout: str = "grid",
        refresh_interval_minutes: int = 60,
    ) -> DashboardSpec:
        widgets: list[dict[str, Any]] = []
        for i, metric in enumerate(metrics or []):
            pos = i  # 0-indexed position in grid
            widgets.append({
                "type": "kpi_card",
                "title": metric.name,
                "metric_id": metric.id,
                "position": {"row": pos // 3, "col": pos % 3},
                "config": {
                    "aggregation": metric.aggregation,
                    "unit": metric.unit,
                    "target": metric.target,
                    "show_trend": True,
                },
            })
        return DashboardSpec.new(
            title=title,
            description=description,
            layout=layout,
            widgets=widgets,
            refresh_interval_minutes=refresh_interval_minutes,
        )

    # ── Metric summarization ─────────────────────────────────

    def summarize_metrics(
        self,
        events: list[MetricEvent],
        metrics_by_id: dict[str, MetricDefinition] | None = None,
    ) -> list[MetricSummary]:
        by_metric: dict[str, list[float]] = {}
        for evt in events:
            by_metric.setdefault(evt.metric_id, []).append(evt.value)
        return [MetricSummary.compute(mid, vals) for mid, vals in by_metric.items()]

    def summarize_single(
        self,
        metric_id: str,
        events: list[MetricEvent],
    ) -> MetricSummary:
        values = [e.value for e in events if e.metric_id == metric_id]
        return MetricSummary.compute(metric_id, values)

    # ── Dataset validation ───────────────────────────────────

    def validate_dataset(self, dataset: AnalyticsDataset) -> ValidationResult:
        issues: list[str] = []
        warnings: list[str] = []

        if not dataset.metrics:
            issues.append("Dataset has no metric definitions.")

        if not dataset.events:
            warnings.append("Dataset has no events (empty dataset).")

        # Check all event metric_ids reference known metrics
        known_ids = {m.id for m in dataset.metrics}
        for evt in dataset.events:
            if evt.metric_id not in known_ids:
                issues.append(
                    f"Event {evt.id} references unknown metric_id '{evt.metric_id}'."
                )

        if issues:
            return ValidationResult.failure(issues)

        if warnings and not issues:
            return ValidationResult.success(warnings)

        return ValidationResult.success()

    # ── Report planning ──────────────────────────────────────

    def plan_report(
        self,
        title: str,
        description: str,
        sections: list[dict[str, Any]] | None = None,
        format: str = "markdown",
    ) -> ReportSpec:
        return ReportSpec.new(
            title=title,
            description=description,
            sections=sections,
            format=format,
        )

    # ── Inventory ────────────────────────────────────────────

    def list_metrics(self) -> list[MetricDefinition]:
        return list(self._planned_metrics)

    @property
    def metric_count(self) -> int:
        return len(self._planned_metrics)
