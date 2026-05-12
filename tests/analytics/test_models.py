"""Tests for P13 Analytics/BI models."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from src.analytics.models import (
    VALID_AGGREGATIONS,
    VALID_CATEGORIES,
    VALID_LAYOUTS,
    VALID_REPORT_FORMATS,
    VALID_UNITS,
    VALID_WIDGET_TYPES,
    AnalyticsDataset,
    DashboardSpec,
    MetricDefinition,
    MetricEvent,
    ReportSpec,
)


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════

def _make_metric(**kw) -> MetricDefinition:
    return MetricDefinition.new(
        name=kw.pop("name", "Engagement Rate"),
        description=kw.pop("description", "Percent of followers who engaged."),
        category=kw.pop("category", "engagement"),
        aggregation=kw.pop("aggregation", "avg"),
        unit=kw.pop("unit", "percentage"),
        **kw,
    )


def _make_event(**kw) -> MetricEvent:
    return MetricEvent.new(
        metric_id=kw.pop("metric_id", "met_test1234"),
        value=kw.pop("value", 5.5),
        **kw,
    )


def _make_dataset(**kw) -> AnalyticsDataset:
    return AnalyticsDataset.new(
        name=kw.pop("name", "Daily Engagement"),
        description=kw.pop("description", "Engagement metrics for today."),
        **kw,
    )


def _make_dashboard(**kw) -> DashboardSpec:
    return DashboardSpec.new(
        title=kw.pop("title", "Content Performance"),
        description=kw.pop("description", "Overview of content metrics."),
        **kw,
    )


def _make_report(**kw) -> ReportSpec:
    return ReportSpec.new(
        title=kw.pop("title", "Weekly Analytics Report"),
        description=kw.pop("description", "Summary of the week's performance."),
        **kw,
    )


# ═══════════════════════════════════════════════════════════════
# MetricDefinition
# ═══════════════════════════════════════════════════════════════

class TestMetricDefinition:
    def test_new_creates_metric_with_id_prefix(self):
        m = _make_metric()
        assert m.id.startswith("met_")
        assert len(m.id) == 12  # "met_" + 8 hex

    def test_new_creates_unique_ids(self):
        a = _make_metric()
        b = _make_metric()
        assert a.id != b.id

    def test_new_has_iso_timestamp(self):
        m = _make_metric()
        assert "T" in m.created_at
        assert m.created_at.endswith("Z")

    def test_new_rejects_invalid_category(self):
        with pytest.raises(ValueError, match="Invalid category"):
            _make_metric(category="bogus")

    def test_new_rejects_invalid_aggregation(self):
        with pytest.raises(ValueError, match="Invalid aggregation"):
            _make_metric(aggregation="quantum")

    def test_new_rejects_invalid_unit(self):
        with pytest.raises(ValueError, match="Invalid unit"):
            _make_metric(unit="parsecs")

    def test_new_accepts_all_valid_categories(self):
        for cat in VALID_CATEGORIES:
            m = _make_metric(category=cat)
            assert m.category == cat

    def test_new_accepts_all_valid_aggregations(self):
        for agg in VALID_AGGREGATIONS:
            m = _make_metric(aggregation=agg)
            assert m.aggregation == agg

    def test_new_accepts_all_valid_units(self):
        for unit in VALID_UNITS:
            m = _make_metric(unit=unit)
            assert m.unit == unit

    def test_dimensions_defaults_to_empty_list(self):
        m = _make_metric()
        assert m.dimensions == []

    def test_filters_defaults_to_empty_dict(self):
        m = _make_metric()
        assert m.filters == {}

    def test_target_is_none_by_default(self):
        m = _make_metric()
        assert m.target is None

    def test_to_dict_from_dict_round_trip(self):
        m = _make_metric(dimensions=["profile"], target=3.5)
        d = m.to_dict()
        restored = MetricDefinition.from_dict(d)
        assert restored.id == m.id
        assert restored.name == m.name
        assert restored.dimensions == ["profile"]
        assert restored.target == 3.5

    def test_to_json_from_json_round_trip(self):
        m = _make_metric(dimensions=["profile"])
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "metric.json"
            m.to_json(p)
            restored = MetricDefinition.from_json(p)
            assert restored.id == m.id
            assert restored.name == m.name

    def test_from_dict_populates_defaults(self):
        d = {"id": "met_abc", "name": "T", "description": "D", "category": "growth", "aggregation": "sum", "unit": "count"}
        m = MetricDefinition.from_dict(d)
        assert m.dimensions == []
        assert m.filters == {}
        assert m.target is None


# ═══════════════════════════════════════════════════════════════
# MetricEvent
# ═══════════════════════════════════════════════════════════════

class TestMetricEvent:
    def test_new_creates_event_with_id_prefix(self):
        e = _make_event()
        assert e.id.startswith("evt_")

    def test_new_unique_ids(self):
        a = _make_event()
        b = _make_event()
        assert a.id != b.id

    def test_dry_run_true_by_default(self):
        e = _make_event()
        assert e.dry_run is True

    def test_can_set_dry_run_false(self):
        e = _make_event(dry_run=False)
        assert e.dry_run is False

    def test_dimensions_and_metadata_default_empty(self):
        e = _make_event()
        assert e.dimensions == {}
        assert e.metadata == {}

    def test_to_dict_from_dict_round_trip(self):
        e = _make_event(value=12.3, dimensions={"profile": "@test"}, metadata={"source": "api"})
        d = e.to_dict()
        restored = MetricEvent.from_dict(d)
        assert restored.id == e.id
        assert restored.value == 12.3
        assert restored.dimensions == {"profile": "@test"}
        assert restored.metadata == {"source": "api"}

    def test_from_dict_defaults(self):
        d = {"id": "evt_abc", "metric_id": "met_xyz", "value": 1.0}
        e = MetricEvent.from_dict(d)
        assert e.dimensions == {}
        assert e.metadata == {}
        assert e.dry_run is True


# ═══════════════════════════════════════════════════════════════
# AnalyticsDataset
# ═══════════════════════════════════════════════════════════════

class TestAnalyticsDataset:
    def test_new_creates_dataset_with_id_prefix(self):
        ds = _make_dataset()
        assert ds.id.startswith("ds_")

    def test_row_count_matches_events(self):
        m = _make_metric()
        ds = _make_dataset(
            metrics=[m],
            events=[_make_event(), _make_event(), _make_event()],
        )
        assert ds.row_count == 3

    def test_row_count_zero_for_empty(self):
        ds = _make_dataset()
        assert ds.row_count == 0

    def test_to_dict_includes_row_count(self):
        ds = _make_dataset(events=[_make_event()])
        d = ds.to_dict()
        assert d["row_count"] == 1

    def test_to_dict_from_dict_round_trip(self):
        m = _make_metric()
        e = _make_event()
        ds = _make_dataset(metrics=[m], events=[e], period_start="2026-05-01", period_end="2026-05-12")
        d = ds.to_dict()
        restored = AnalyticsDataset.from_dict(d)
        assert restored.id == ds.id
        assert restored.name == ds.name
        assert restored.row_count == 1
        assert len(restored.metrics) == 1
        assert isinstance(restored.metrics[0], MetricDefinition)
        assert len(restored.events) == 1
        assert isinstance(restored.events[0], MetricEvent)
        assert restored.period_start == "2026-05-01"
        assert restored.period_end == "2026-05-12"


# ═══════════════════════════════════════════════════════════════
# DashboardSpec
# ═══════════════════════════════════════════════════════════════

class TestDashboardSpec:
    def test_new_creates_with_id_prefix(self):
        d = _make_dashboard()
        assert d.id.startswith("dash_")

    def test_default_layout_is_grid(self):
        d = _make_dashboard()
        assert d.layout == "grid"

    def test_default_refresh_60_minutes(self):
        d = _make_dashboard()
        assert d.refresh_interval_minutes == 60

    def test_rejects_invalid_layout(self):
        with pytest.raises(ValueError, match="Invalid layout"):
            _make_dashboard(layout="circular")

    def test_rejects_invalid_widget_type(self):
        with pytest.raises(ValueError, match="Invalid widget type"):
            _make_dashboard(widgets=[{"type": "rocket_launcher"}])

    def test_accepts_all_valid_layouts(self):
        for layout in VALID_LAYOUTS:
            d = _make_dashboard(layout=layout)
            assert d.layout == layout

    def test_accepts_all_valid_widget_types(self):
        for wtype in VALID_WIDGET_TYPES:
            d = _make_dashboard(widgets=[{"type": wtype, "title": "Test"}])
            assert d.widgets[0]["type"] == wtype

    def test_to_dict_from_dict_round_trip(self):
        widgets = [{"type": "kpi_card", "title": "Engagement", "metric_id": "met_abc"}]
        d = _make_dashboard(layout="two_columns", widgets=widgets, refresh_interval_minutes=30)
        data = d.to_dict()
        restored = DashboardSpec.from_dict(data)
        assert restored.id == d.id
        assert restored.layout == "two_columns"
        assert restored.widgets == widgets
        assert restored.refresh_interval_minutes == 30


# ═══════════════════════════════════════════════════════════════
# ReportSpec
# ═══════════════════════════════════════════════════════════════

class TestReportSpec:
    def test_new_creates_with_id_prefix(self):
        r = _make_report()
        assert r.id.startswith("rpt_")

    def test_default_format_is_markdown(self):
        r = _make_report()
        assert r.format == "markdown"

    def test_rejects_invalid_format(self):
        with pytest.raises(ValueError, match="Invalid format"):
            _make_report(format="latex")

    def test_accepts_all_valid_formats(self):
        for fmt in VALID_REPORT_FORMATS:
            r = _make_report(format=fmt)
            assert r.format == fmt

    def test_to_dict_from_dict_round_trip(self):
        sections = [
            {"title": "Overview", "type": "summary", "content": "High-level summary."},
            {"title": "Charts", "type": "charts", "content": [], "charts": [{"title": "Growth", "type": "line_chart", "metric_id": "met_abc"}]},
        ]
        r = _make_report(sections=sections)
        data = r.to_dict()
        restored = ReportSpec.from_dict(data)
        assert restored.id == r.id
        assert len(restored.sections) == 2
        assert restored.sections[0]["title"] == "Overview"


# ═══════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════

class TestConstants:
    def test_valid_aggregations_cardinality(self):
        assert len(VALID_AGGREGATIONS) == 8

    def test_valid_categories_cardinality(self):
        assert len(VALID_CATEGORIES) == 7

    def test_valid_units_cardinality(self):
        assert len(VALID_UNITS) == 8

    def test_valid_layouts_cardinality(self):
        assert len(VALID_LAYOUTS) == 5

    def test_valid_widget_types_cardinality(self):
        assert len(VALID_WIDGET_TYPES) == 8

    def test_valid_report_formats_cardinality(self):
        assert len(VALID_REPORT_FORMATS) == 3
