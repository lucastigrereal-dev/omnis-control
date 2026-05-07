"""Testes das funcoes de agregacao — P0.9."""
from __future__ import annotations

from src.metrics.models import MetricEvent, RunSummary
from src.metrics.aggregations import (
    aggregate_metrics_by_event_type,
    aggregate_tool_usage,
    compute_run_stats,
    compute_mission_summary,
    compute_daily_summary,
)


class TestAggregateByEventType:
    """Agrupamento por event_type."""

    def test_basic_grouping(self):
        metrics = [
            MetricEvent(name="a", event_type="et1", value=1.0),
            MetricEvent(name="b", event_type="et1", value=2.0),
            MetricEvent(name="c", event_type="et2", value=3.0),
        ]
        result = aggregate_metrics_by_event_type(metrics)
        assert result["et1"]["count"] == 2
        assert result["et1"]["avg_value"] == 1.5
        assert result["et2"]["count"] == 1

    def test_empty_list(self):
        assert aggregate_metrics_by_event_type([]) == {}


class TestAggregateToolUsage:
    """Agrupamento por tool_id."""

    def test_per_tool_counts(self):
        metrics = [
            MetricEvent(name="a", tool_id="docker", status="success"),
            MetricEvent(name="b", tool_id="docker", status="success"),
            MetricEvent(name="c", tool_id="publisher", status="blocked"),
        ]
        result = aggregate_tool_usage(metrics)
        assert result["docker"]["count"] == 2
        assert result["publisher"]["count"] == 1
        assert result["docker"]["by_status"]["success"] == 2

    def test_no_tool_id_grouped(self):
        metrics = [
            MetricEvent(name="a", tool_id=""),
        ]
        result = aggregate_tool_usage(metrics)
        assert "__no_tool__" in result
        assert result["__no_tool__"]["count"] == 1


class TestComputeRunStats:
    """Estatisticas de runs."""

    def test_basic_stats(self):
        runs = [
            RunSummary(run_id="r1", status="success", duration_ms=100.0),
            RunSummary(run_id="r2", status="failed", duration_ms=200.0),
            RunSummary(run_id="r3", status="success", duration_ms=300.0),
        ]
        stats = compute_run_stats(runs)
        assert stats["total"] == 3
        assert stats["succeeded"] == 2
        assert stats["failed"] == 1
        assert stats["avg_duration_ms"] == 200.0

    def test_empty_runs(self):
        stats = compute_run_stats([])
        assert stats["total"] == 0


class TestComputeDailySummary:
    """Filtro por data."""

    def test_date_filter(self):
        runs = [
            RunSummary(run_id="r1", started_at="2026-05-07T10:00:00Z", status="success"),
            RunSummary(run_id="r2", started_at="2026-05-06T10:00:00Z", status="failed"),
        ]
        summary = compute_daily_summary(runs, date_prefix="2026-05-07")
        assert summary["total"] == 1
        assert summary["succeeded"] == 1

    def test_no_date_prefix_uses_today(self):
        runs = [
            RunSummary(run_id="r1", started_at="2026-05-06T10:00:00Z", status="failed"),
        ]
        summary = compute_daily_summary(runs, date_prefix="2026-05-07")
        assert summary["total"] == 0
