"""Tests for P13 Analytics/BI service layer."""

from __future__ import annotations

import pytest

from src.analytics.models import (
    AnalyticsDataset,
    MetricDefinition,
    MetricEvent,
)
from src.analytics.service import (
    AnalyticsPlanner,
    MetricSummary,
    ValidationResult,
)


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════

def _metric(**kw) -> MetricDefinition:
    return MetricDefinition.new(
        name=kw.pop("name", "Test Metric"),
        description=kw.pop("description", "Test"),
        category=kw.pop("category", "engagement"),
        aggregation=kw.pop("aggregation", "avg"),
        unit=kw.pop("unit", "percentage"),
        **kw,
    )


def _event(metric_id="met_abc", value=10.0, **kw) -> MetricEvent:
    return MetricEvent.new(metric_id=metric_id, value=value, **kw)


# ═══════════════════════════════════════════════════════════════
# ValidationResult
# ═══════════════════════════════════════════════════════════════

class TestValidationResult:
    def test_success_ok(self):
        vr = ValidationResult.success()
        assert vr.valid is True
        assert vr.ok is True

    def test_success_with_warnings(self):
        vr = ValidationResult.success(warnings=["low data"])
        assert vr.ok is True
        assert vr.warnings == ["low data"]

    def test_failure_not_ok(self):
        vr = ValidationResult.failure(["bad schema"])
        assert vr.valid is False
        assert vr.ok is False

    def test_failure_stores_issues(self):
        vr = ValidationResult.failure(["issue1", "issue2"])
        assert vr.issues == ["issue1", "issue2"]


# ═══════════════════════════════════════════════════════════════
# MetricSummary
# ═══════════════════════════════════════════════════════════════

class TestMetricSummary:
    def test_compute_empty_returns_zero_count(self):
        s = MetricSummary.compute("met_x", [])
        assert s.count == 0
        assert s.avg == 0.0

    def test_compute_single_value(self):
        s = MetricSummary.compute("met_x", [5.0])
        assert s.count == 1
        assert s.sum == 5.0
        assert s.avg == 5.0
        assert s.min == 5.0
        assert s.max == 5.0
        assert s.median == 5.0
        assert s.std_dev == 0.0

    def test_compute_multiple_values(self):
        s = MetricSummary.compute("met_x", [2.0, 4.0, 6.0, 8.0, 10.0])
        assert s.count == 5
        assert s.sum == 30.0
        assert s.avg == 6.0
        assert s.min == 2.0
        assert s.max == 10.0
        assert s.median == 6.0
        assert round(s.std_dev, 4) == 3.1623

    def test_to_dict(self):
        s = MetricSummary.compute("met_x", [1.0, 3.0])
        d = s.to_dict()
        assert d["metric_id"] == "met_x"
        assert d["count"] == 2
        assert "avg" in d


# ═══════════════════════════════════════════════════════════════
# AnalyticsPlanner
# ═══════════════════════════════════════════════════════════════

class TestAnalyticsPlanner:
    def test_default_dry_run_true(self):
        planner = AnalyticsPlanner()
        assert planner.dry_run is True

    def test_can_set_dry_run_false(self):
        planner = AnalyticsPlanner(dry_run=False)
        assert planner.dry_run is False

    # ── plan_metric ──────────────────────────────────────────

    def test_plan_metric_returns_metric_definition(self):
        planner = AnalyticsPlanner()
        m = planner.plan_metric("Views", "Total views", "growth", "sum", "views")
        assert isinstance(m, MetricDefinition)
        assert m.name == "Views"
        assert m.id.startswith("met_")

    def test_plan_metric_tracks_in_inventory(self):
        planner = AnalyticsPlanner()
        planner.plan_metric("A", "a", "growth", "sum", "count")
        planner.plan_metric("B", "b", "revenue", "avg", "currency_brl")
        assert planner.metric_count == 2
        assert len(planner.list_metrics()) == 2

    # ── build_dashboard_spec ─────────────────────────────────

    def test_build_dashboard_spec_no_metrics(self):
        planner = AnalyticsPlanner()
        spec = planner.build_dashboard_spec("Empty Dash", "No metrics yet.")
        assert spec.title == "Empty Dash"
        assert spec.widgets == []

    def test_build_dashboard_spec_generates_widgets(self):
        planner = AnalyticsPlanner()
        m1 = planner.plan_metric("Views", "v", "growth", "sum", "views")
        m2 = planner.plan_metric("Clicks", "c", "engagement", "count", "count")
        spec = planner.build_dashboard_spec("Dash", "Two widgets", metrics=[m1, m2])
        assert len(spec.widgets) == 2
        assert spec.widgets[0]["type"] == "kpi_card"
        assert spec.widgets[0]["metric_id"] == m1.id
        assert spec.widgets[1]["metric_id"] == m2.id

    def test_build_dashboard_spec_respects_layout(self):
        planner = AnalyticsPlanner()
        spec = planner.build_dashboard_spec("T", "D", layout="single_column")
        assert spec.layout == "single_column"

    # ── summarize_metrics ────────────────────────────────────

    def test_summarize_metrics_empty(self):
        planner = AnalyticsPlanner()
        summaries = planner.summarize_metrics([])
        assert summaries == []

    def test_summarize_metrics_groups_by_metric_id(self):
        planner = AnalyticsPlanner()
        events = [
            _event(metric_id="met_a", value=1.0),
            _event(metric_id="met_a", value=3.0),
            _event(metric_id="met_b", value=10.0),
        ]
        summaries = planner.summarize_metrics(events)
        assert len(summaries) == 2
        by_id = {s.metric_id: s for s in summaries}
        assert by_id["met_a"].count == 2
        assert by_id["met_a"].avg == 2.0
        assert by_id["met_b"].count == 1
        assert by_id["met_b"].avg == 10.0

    def test_summarize_single(self):
        planner = AnalyticsPlanner()
        events = [_event(metric_id="met_x", value=5.0), _event(metric_id="met_x", value=15.0)]
        s = planner.summarize_single("met_x", events)
        assert s.count == 2
        assert s.min == 5.0
        assert s.max == 15.0

    # ── validate_dataset ────────────────────────────────────

    def test_validate_empty_dataset(self):
        planner = AnalyticsPlanner()
        ds = AnalyticsDataset.new("Empty", "No metrics or events.")
        vr = planner.validate_dataset(ds)
        assert vr.valid is False
        assert any("no metric definitions" in i.lower() for i in vr.issues)

    def test_validate_warns_on_empty_events(self):
        planner = AnalyticsPlanner()
        m = _metric()
        ds = AnalyticsDataset.new("D", "desc", metrics=[m], events=[])
        vr = planner.validate_dataset(ds)
        assert vr.ok is True
        assert len(vr.warnings) >= 1

    def test_validate_detects_orphan_events(self):
        planner = AnalyticsPlanner()
        m = _metric()
        orphan = _event(metric_id="met_unknown", value=1.0)
        ds = AnalyticsDataset.new("D", "desc", metrics=[m], events=[orphan])
        vr = planner.validate_dataset(ds)
        assert vr.valid is False
        assert any("unknown metric_id" in i.lower() for i in vr.issues)

    def test_validate_valid_dataset_passes(self):
        planner = AnalyticsPlanner()
        m = _metric()
        e = _event(metric_id=m.id, value=5.0)
        ds = AnalyticsDataset.new("D", "desc", metrics=[m], events=[e])
        vr = planner.validate_dataset(ds)
        assert vr.ok is True
        assert vr.issues == []

    # ── plan_report ──────────────────────────────────────────

    def test_plan_report_returns_report_spec(self):
        planner = AnalyticsPlanner()
        r = planner.plan_report("Weekly", "Weekly performance report.")
        assert r.title == "Weekly"
        assert r.format == "markdown"
        assert r.id.startswith("rpt_")

    def test_plan_report_with_sections(self):
        planner = AnalyticsPlanner()
        sections = [{"title": "Summary", "type": "text", "content": "All good."}]
        r = planner.plan_report("Q1", "Quarterly", sections=sections)
        assert len(r.sections) == 1

    # ── inventory ────────────────────────────────────────────

    def test_list_metrics_returns_copy(self):
        planner = AnalyticsPlanner()
        planner.plan_metric("X", "x", "growth", "sum", "count")
        copy1 = planner.list_metrics()
        copy1.clear()
        assert planner.metric_count == 1  # original unaffected
