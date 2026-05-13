"""Tests for P16 Observability Local models."""

import pytest
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


class TestTraceEvent:
    def test_default_factory_generates_ids(self):
        event = TraceEvent(name="test.span")
        assert event.name == "test.span"
        assert len(event.trace_id) == 32
        assert len(event.span_id) == 16
        assert event.parent_span_id is None
        assert event.status == "ok"
        assert event.attributes == {}

    def test_explicit_ids_respected(self):
        event = TraceEvent(
            name="explicit",
            trace_id="aaa",
            span_id="bbb",
            parent_span_id="ccc",
        )
        assert event.trace_id == "aaa"
        assert event.span_id == "bbb"
        assert event.parent_span_id == "ccc"

    def test_attributes_stored(self):
        event = TraceEvent(name="with.attrs", attributes={"key": "val"})
        assert event.attributes == {"key": "val"}


class TestMetricPoint:
    def test_defaults(self):
        mp = MetricPoint(name="cpu_usage", value=42.5)
        assert mp.name == "cpu_usage"
        assert mp.value == 42.5
        assert mp.unit == "count"
        assert mp.metric_type == MetricType.GAUGE
        assert mp.labels == {}

    def test_with_labels_and_type(self):
        mp = MetricPoint(
            name="requests",
            value=100.0,
            unit="rps",
            metric_type=MetricType.COUNTER,
            labels={"host": "srv1"},
        )
        assert mp.metric_type == MetricType.COUNTER
        assert mp.labels == {"host": "srv1"}


class TestRunLogEntry:
    def test_defaults(self):
        entry = RunLogEntry(run_id="run-1", message="hello")
        assert entry.run_id == "run-1"
        assert entry.message == "hello"
        assert entry.level == RunLogLevel.INFO
        assert entry.module == ""
        assert entry.metadata == {}

    def test_with_metadata(self):
        entry = RunLogEntry(
            run_id="run-2",
            message="error msg",
            level=RunLogLevel.ERROR,
            module="test.module",
            metadata={"code": 500},
        )
        assert entry.level == RunLogLevel.ERROR
        assert entry.module == "test.module"
        assert entry.metadata == {"code": 500}


class TestHealthSignal:
    def test_defaults(self):
        sig = HealthSignal(component="db")
        assert sig.component == "db"
        assert sig.status == HealthStatus.HEALTHY
        assert sig.message == ""
        assert sig.checks == {}

    def test_unhealthy(self):
        sig = HealthSignal(
            component="cache",
            status=HealthStatus.UNHEALTHY,
            message="connection refused",
            checks={"ping": False},
        )
        assert sig.status == HealthStatus.UNHEALTHY
        assert sig.checks == {"ping": False}


class TestObservabilitySnapshot:
    def test_empty_snapshot(self):
        snap = ObservabilitySnapshot()
        assert snap.traces == []
        assert snap.metrics == []
        assert snap.logs == []
        assert snap.health_signals == []

    def test_snapshot_with_signals(self):
        snap = ObservabilitySnapshot(
            traces=[TraceEvent(name="s")],
            metrics=[MetricPoint(name="m", value=1.0)],
            logs=[RunLogEntry(run_id="r", message="x")],
            health_signals=[HealthSignal(component="c")],
        )
        assert len(snap.traces) == 1
        assert len(snap.metrics) == 1
        assert len(snap.logs) == 1
        assert len(snap.health_signals) == 1


class TestAlertPlan:
    def test_defaults(self):
        plan = AlertPlan()
        assert len(plan.alert_id) == 12
        assert plan.severity == AlertSeverity.INFO
        assert plan.title == ""

    def test_full_plan(self):
        plan = AlertPlan(
            title="Disk full",
            description="Disk at 95%",
            severity=AlertSeverity.CRITICAL,
            condition="disk_usage > 90",
            suggested_action="Free disk space",
            source="metric",
        )
        assert plan.severity == AlertSeverity.CRITICAL
        assert plan.source == "metric"


class TestEnums:
    def test_metric_type_values(self):
        assert MetricType.GAUGE == "gauge"
        assert MetricType.COUNTER == "counter"
        assert MetricType.HISTOGRAM == "histogram"

    def test_health_status_values(self):
        assert HealthStatus.HEALTHY == "healthy"
        assert HealthStatus.DEGRADED == "degraded"
        assert HealthStatus.UNHEALTHY == "unhealthy"

    def test_alert_severity_values(self):
        assert AlertSeverity.INFO == "info"
        assert AlertSeverity.WARNING == "warning"
        assert AlertSeverity.CRITICAL == "critical"

    def test_run_log_level_values(self):
        assert RunLogLevel.DEBUG == "debug"
        assert RunLogLevel.INFO == "info"
        assert RunLogLevel.WARNING == "warning"
        assert RunLogLevel.ERROR == "error"
