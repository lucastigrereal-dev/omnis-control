"""Tests for P16 Observability Local service."""

import json
import pytest
from src.observability_local.models import (
    AlertPlan,
    AlertSeverity,
    HealthStatus,
    MetricType,
    ObservabilitySnapshot,
    RunLogLevel,
    TraceEvent,
)
from src.observability_local.service import (
    ObservabilityPlanner,
    build_snapshot_from_planner,
)


class TestRecordTraceEventPlan:
    def test_basic_trace_event(self):
        event = ObservabilityPlanner.record_trace_event_plan("my.span")
        assert isinstance(event, TraceEvent)
        assert event.name == "my.span"
        assert len(event.trace_id) == 32
        assert len(event.span_id) == 16
        assert event.parent_span_id is None
        assert event.attributes == {}

    def test_with_attributes_sanitized(self):
        event = ObservabilityPlanner.record_trace_event_plan(
            "auth.span",
            attributes={"user": "lucas", "token": "secret123"},
        )
        assert event.attributes["user"] == "lucas"
        assert event.attributes["token"] == "[REDACTED]"

    def test_explicit_ids_preserved(self):
        event = ObservabilityPlanner.record_trace_event_plan(
            "custom", span_id="span1", parent_span_id="parent1", trace_id="trace1"
        )
        assert event.span_id == "span1"
        assert event.parent_span_id == "parent1"
        assert event.trace_id == "trace1"


class TestBuildMetricPoint:
    def test_basic_metric(self):
        mp = ObservabilityPlanner.build_metric_point("latency", 12.3, unit="ms")
        assert mp.name == "latency"
        assert mp.value == 12.3
        assert mp.unit == "ms"
        assert mp.metric_type == MetricType.GAUGE

    def test_labels_sanitized(self):
        mp = ObservabilityPlanner.build_metric_point(
            "auth_ops", 1.0, labels={"api_key": "abc123", "env": "prod"}
        )
        assert mp.labels["api_key"] == "[REDACTED]"
        assert mp.labels["env"] == "prod"


class TestBuildRunLogEntry:
    def test_basic_entry(self):
        entry = ObservabilityPlanner.build_run_log_entry(
            "run-1", "task started", module="pipeline"
        )
        assert entry.run_id == "run-1"
        assert entry.message == "task started"
        assert entry.module == "pipeline"
        assert entry.level == RunLogLevel.INFO

    def test_metadata_sanitized(self):
        entry = ObservabilityPlanner.build_run_log_entry(
            "run-2", "auth failed", metadata={"password": "pwd", "user": "lucas"}
        )
        assert entry.metadata["password"] == "[REDACTED]"
        assert entry.metadata["user"] == "lucas"


class TestBuildHealthSnapshot:
    def test_empty(self):
        snap = ObservabilityPlanner.build_health_snapshot()
        assert isinstance(snap, ObservabilitySnapshot)
        assert snap.health_signals == []

    def test_with_components(self):
        components = [
            {"component": "db", "status": "healthy", "checks": {"ping": True}},
            {"component": "cache", "status": "degraded", "message": "slow"},
        ]
        snap = ObservabilityPlanner.build_health_snapshot(components)
        assert len(snap.health_signals) == 2
        assert snap.health_signals[0].status == HealthStatus.HEALTHY
        assert snap.health_signals[1].status == HealthStatus.DEGRADED


class TestPlanAlerts:
    def test_no_alerts_healthy(self):
        snap = ObservabilityPlanner.build_health_snapshot([
            {"component": "db", "status": "healthy"},
        ])
        plans = ObservabilityPlanner.plan_alerts(snap)
        assert plans == []

    def test_unhealthy_triggers_critical(self):
        snap = ObservabilityPlanner.build_health_snapshot([
            {"component": "cache", "status": "unhealthy", "message": "down"},
        ])
        plans = ObservabilityPlanner.plan_alerts(snap)
        assert len(plans) == 1
        assert plans[0].severity == AlertSeverity.CRITICAL
        assert "cache" in plans[0].title

    def test_degraded_triggers_warning(self):
        snap = ObservabilityPlanner.build_health_snapshot([
            {"component": "queue", "status": "degraded"},
        ])
        plans = ObservabilityPlanner.plan_alerts(snap)
        assert len(plans) == 1
        assert plans[0].severity == AlertSeverity.WARNING

    def test_metric_threshold_breach(self):
        from src.observability_local.models import MetricPoint
        snap = ObservabilitySnapshot(
            metrics=[MetricPoint(name="error_rate", value=15.0)]
        )
        plans = ObservabilityPlanner.plan_alerts(snap, thresholds={"error_rate": 5.0})
        assert len(plans) == 1
        assert plans[0].severity == AlertSeverity.WARNING
        assert "error_rate" in plans[0].title

    def test_metric_below_threshold_no_alert(self):
        from src.observability_local.models import MetricPoint
        snap = ObservabilitySnapshot(
            metrics=[MetricPoint(name="error_rate", value=3.0)]
        )
        plans = ObservabilityPlanner.plan_alerts(snap, thresholds={"error_rate": 5.0})
        assert plans == []

    def test_mixed_signals(self):
        snap = ObservabilityPlanner.build_health_snapshot([
            {"component": "db", "status": "healthy"},
            {"component": "cache", "status": "unhealthy", "message": "down"},
            {"component": "queue", "status": "degraded"},
        ])
        plans = ObservabilityPlanner.plan_alerts(snap)
        assert len(plans) == 2


class TestSanitizeObservabilityPayload:
    def test_redacts_token(self):
        result = ObservabilityPlanner.sanitize_observability_payload(
            {"token": "abc123", "user": "lucas"}
        )
        assert result["token"] == "[REDACTED]"
        assert result["user"] == "lucas"

    def test_redacts_secret(self):
        result = ObservabilityPlanner.sanitize_observability_payload(
            {"client_secret": "xyz"}
        )
        assert result["client_secret"] == "[REDACTED]"

    def test_redacts_password(self):
        result = ObservabilityPlanner.sanitize_observability_payload(
            {"password": "12345"}
        )
        assert result["password"] == "[REDACTED]"

    def test_redacts_api_key(self):
        result = ObservabilityPlanner.sanitize_observability_payload(
            {"api_key": "key123"}
        )
        assert result["api_key"] == "[REDACTED]"

    def test_redacts_bearer(self):
        result = ObservabilityPlanner.sanitize_observability_payload(
            {"Authorization": "Bearer token123"}
        )
        assert result["Authorization"] == "[REDACTED]"

    def test_redacts_access_key(self):
        result = ObservabilityPlanner.sanitize_observability_payload(
            {"aws_access_key": "AKIAxxx"}
        )
        assert result["aws_access_key"] == "[REDACTED]"

    def test_redacts_private_key(self):
        result = ObservabilityPlanner.sanitize_observability_payload(
            {"private_key": "-----BEGIN RSA-----"}
        )
        assert result["private_key"] == "[REDACTED]"

    def test_nested_dict_sanitized(self):
        result = ObservabilityPlanner.sanitize_observability_payload({
            "metadata": {"token": "secret", "safe": "ok"}
        })
        assert result["metadata"]["token"] == "[REDACTED]"
        assert result["metadata"]["safe"] == "ok"

    def test_list_of_dicts(self):
        result = ObservabilityPlanner.sanitize_observability_payload({
            "items": [{"name": "a", "token": "x"}, {"name": "b", "token": "y"}]
        })
        assert result["items"][0]["token"] == "[REDACTED]"
        assert result["items"][1]["token"] == "[REDACTED]"
        assert result["items"][0]["name"] == "a"

    def test_case_insensitive(self):
        result = ObservabilityPlanner.sanitize_observability_payload(
            {"TOKEN": "abc", "Bearer": "tok"}
        )
        assert result["TOKEN"] == "[REDACTED]"
        assert result["Bearer"] == "[REDACTED]"

    def test_safe_values_preserved(self):
        result = ObservabilityPlanner.sanitize_observability_payload(
            {"name": "lucas", "env": "prod", "count": 42}
        )
        assert result == {"name": "lucas", "env": "prod", "count": 42}

    def test_non_dict_returns_as_is(self):
        assert ObservabilityPlanner.sanitize_observability_payload("string") == "string"
        assert ObservabilityPlanner.sanitize_observability_payload(42) == 42

    def test_json_roundtrip_safe(self):
        payload = {"user": "lucas", "token": "abc"}
        sanitized = ObservabilityPlanner.sanitize_observability_payload(payload)
        json_str = json.dumps(sanitized)
        back = json.loads(json_str)
        assert back == sanitized


class TestBuildSnapshotFromPlanner:
    def test_empty_returns_empty_snapshot(self):
        snap = build_snapshot_from_planner()
        assert snap.traces == []
        assert snap.metrics == []
        assert snap.logs == []
        assert snap.health_signals == []

    def test_full_build(self):
        snap = build_snapshot_from_planner(
            traces=[{"name": "span1", "attributes": {"token": "x"}}],
            metrics=[{"name": "cpu", "value": 50.0, "labels": {"api_key": "k"}}],
            logs=[{"run_id": "r1", "message": "start", "metadata": {"secret": "s"}}],
            health=[{"component": "db", "status": "healthy"}],
        )
        assert len(snap.traces) == 1
        assert snap.traces[0].attributes["token"] == "[REDACTED]"
        assert len(snap.metrics) == 1
        assert snap.metrics[0].labels["api_key"] == "[REDACTED]"
        assert len(snap.logs) == 1
        assert snap.logs[0].metadata["secret"] == "[REDACTED]"
        assert len(snap.health_signals) == 1
        assert snap.health_signals[0].component == "db"


class TestAlertPlanProperties:
    def test_alert_plan_is_plan_only(self):
        plans = ObservabilityPlanner.plan_alerts(
            ObservabilityPlanner.build_health_snapshot([
                {"component": "s3", "status": "unhealthy", "message": "timeout"}
            ])
        )
        for plan in plans:
            assert isinstance(plan, AlertPlan)
            assert plan.alert_id is not None
            assert plan.timestamp is not None
            assert plan.source == "health_signal"
