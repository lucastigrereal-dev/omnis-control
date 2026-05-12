"""P13 Analytics/BI — deterministic models (dataclasses, zero Pydantic)."""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ═══════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════

VALID_AGGREGATIONS = frozenset({"sum", "avg", "count", "max", "min", "p50", "p95", "p99"})
VALID_CATEGORIES = frozenset({
    "engagement", "revenue", "growth", "content",
    "audience", "conversion", "retention",
})
VALID_UNITS = frozenset({
    "count", "percentage", "currency_brl", "seconds",
    "minutes", "hours", "views", "interactions",
})
VALID_LAYOUTS = frozenset({"grid", "single_column", "two_columns", "tabbed", "freeform"})
VALID_REPORT_FORMATS = frozenset({"markdown", "html", "pdf"})
VALID_WIDGET_TYPES = frozenset({
    "kpi_card", "line_chart", "bar_chart", "pie_chart",
    "table", "heatmap", "funnel", "gauge",
})


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _short_id(prefix: str) -> str:
    return f"{prefix}{uuid.uuid4().hex[:8]}"


# ═══════════════════════════════════════════════════════════════
# Models
# ═══════════════════════════════════════════════════════════════

@dataclass
class MetricDefinition:
    """Defines a metric: what to track and how to aggregate it."""

    id: str
    name: str
    description: str
    category: str
    aggregation: str
    unit: str
    dimensions: list[str] = field(default_factory=list)
    filters: dict[str, str] = field(default_factory=dict)
    target: float | None = None
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        name: str,
        description: str,
        category: str,
        aggregation: str,
        unit: str,
        dimensions: list[str] | None = None,
        filters: dict[str, str] | None = None,
        target: float | None = None,
    ) -> MetricDefinition:
        if category not in VALID_CATEGORIES:
            raise ValueError(
                f"Invalid category '{category}'. Valid: {sorted(VALID_CATEGORIES)}"
            )
        if aggregation not in VALID_AGGREGATIONS:
            raise ValueError(
                f"Invalid aggregation '{aggregation}'. Valid: {sorted(VALID_AGGREGATIONS)}"
            )
        if unit not in VALID_UNITS:
            raise ValueError(
                f"Invalid unit '{unit}'. Valid: {sorted(VALID_UNITS)}"
            )
        return cls(
            id=_short_id("met_"),
            name=name,
            description=description,
            category=category,
            aggregation=aggregation,
            unit=unit,
            dimensions=dimensions or [],
            filters=filters or {},
            target=target,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "aggregation": self.aggregation,
            "unit": self.unit,
            "dimensions": self.dimensions,
            "filters": self.filters,
            "target": self.target,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MetricDefinition:
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            category=data["category"],
            aggregation=data["aggregation"],
            unit=data["unit"],
            dimensions=data.get("dimensions", []),
            filters=data.get("filters", {}),
            target=data.get("target"),
            created_at=data.get("created_at", _now_iso()),
        )

    def to_json(self, path: str | Path) -> Path:
        p = Path(path)
        p.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        return p

    @classmethod
    def from_json(cls, path: str | Path) -> MetricDefinition:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_dict(data)


@dataclass
class MetricEvent:
    """A single metric data point with value and dimensional context."""

    id: str
    metric_id: str
    value: float
    timestamp: str
    dimensions: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, str] = field(default_factory=dict)
    dry_run: bool = True

    @classmethod
    def new(
        cls,
        metric_id: str,
        value: float,
        timestamp: str | None = None,
        dimensions: dict[str, str] | None = None,
        metadata: dict[str, str] | None = None,
        dry_run: bool = True,
    ) -> MetricEvent:
        return cls(
            id=_short_id("evt_"),
            metric_id=metric_id,
            value=value,
            timestamp=timestamp or _now_iso(),
            dimensions=dimensions or {},
            metadata=metadata or {},
            dry_run=dry_run,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "metric_id": self.metric_id,
            "value": self.value,
            "timestamp": self.timestamp,
            "dimensions": self.dimensions,
            "metadata": self.metadata,
            "dry_run": self.dry_run,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MetricEvent:
        return cls(
            id=data["id"],
            metric_id=data["metric_id"],
            value=data["value"],
            timestamp=data.get("timestamp", _now_iso()),
            dimensions=data.get("dimensions", {}),
            metadata=data.get("metadata", {}),
            dry_run=data.get("dry_run", True),
        )


@dataclass
class AnalyticsDataset:
    """A named collection of metric definitions + events."""

    id: str
    name: str
    description: str
    metrics: list[MetricDefinition] = field(default_factory=list)
    events: list[MetricEvent] = field(default_factory=list)
    period_start: str | None = None
    period_end: str | None = None
    created_at: str = field(default_factory=_now_iso)

    @property
    def row_count(self) -> int:
        return len(self.events)

    @classmethod
    def new(
        cls,
        name: str,
        description: str,
        metrics: list[MetricDefinition] | None = None,
        events: list[MetricEvent] | None = None,
        period_start: str | None = None,
        period_end: str | None = None,
    ) -> AnalyticsDataset:
        return cls(
            id=_short_id("ds_"),
            name=name,
            description=description,
            metrics=metrics or [],
            events=events or [],
            period_start=period_start,
            period_end=period_end,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "metrics": [m.to_dict() for m in self.metrics],
            "events": [e.to_dict() for e in self.events],
            "period_start": self.period_start,
            "period_end": self.period_end,
            "row_count": self.row_count,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AnalyticsDataset:
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            metrics=[MetricDefinition.from_dict(m) for m in data.get("metrics", [])],
            events=[MetricEvent.from_dict(e) for e in data.get("events", [])],
            period_start=data.get("period_start"),
            period_end=data.get("period_end"),
            created_at=data.get("created_at", _now_iso()),
        )


@dataclass
class DashboardSpec:
    """Dashboard layout specification with widget placements."""

    id: str
    title: str
    description: str
    layout: str
    widgets: list[dict[str, Any]] = field(default_factory=list)
    refresh_interval_minutes: int = 60
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        title: str,
        description: str,
        layout: str = "grid",
        widgets: list[dict[str, Any]] | None = None,
        refresh_interval_minutes: int = 60,
    ) -> DashboardSpec:
        if layout not in VALID_LAYOUTS:
            raise ValueError(
                f"Invalid layout '{layout}'. Valid: {sorted(VALID_LAYOUTS)}"
            )
        validated = []
        for w in (widgets or []):
            if w.get("type") not in VALID_WIDGET_TYPES:
                raise ValueError(
                    f"Invalid widget type '{w.get('type')}'. Valid: {sorted(VALID_WIDGET_TYPES)}"
                )
            validated.append(w)
        return cls(
            id=_short_id("dash_"),
            title=title,
            description=description,
            layout=layout,
            widgets=validated,
            refresh_interval_minutes=refresh_interval_minutes,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "layout": self.layout,
            "widgets": self.widgets,
            "refresh_interval_minutes": self.refresh_interval_minutes,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DashboardSpec:
        return cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            layout=data.get("layout", "grid"),
            widgets=data.get("widgets", []),
            refresh_interval_minutes=data.get("refresh_interval_minutes", 60),
            created_at=data.get("created_at", _now_iso()),
        )


@dataclass
class ReportSpec:
    """Report template specification with sections and visualizations."""

    id: str
    title: str
    description: str
    sections: list[dict[str, Any]] = field(default_factory=list)
    format: str = "markdown"
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        title: str,
        description: str,
        sections: list[dict[str, Any]] | None = None,
        format: str = "markdown",
    ) -> ReportSpec:
        if format not in VALID_REPORT_FORMATS:
            raise ValueError(
                f"Invalid format '{format}'. Valid: {sorted(VALID_REPORT_FORMATS)}"
            )
        return cls(
            id=_short_id("rpt_"),
            title=title,
            description=description,
            sections=sections or [],
            format=format,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "sections": self.sections,
            "format": self.format,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ReportSpec:
        return cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            sections=data.get("sections", []),
            format=data.get("format", "markdown"),
            created_at=data.get("created_at", _now_iso()),
        )
