"""W040 — Observability E2E dry-run test. Exercises full observability pipeline."""
import json
import os
import tempfile

from src.observability.stage_events import StageEvent, StageStatus
from src.observability.error_taxonomy import ErrorClassifier, ErrorCategory
from src.observability.audit import AuditTrail, AuditEntryType
from src.observability_local.models import (
    TraceEvent,
    MetricPoint,
    MetricType,
    RunLogEntry,
    RunLogLevel,
    HealthSignal,
    HealthStatus,
    ObservabilitySnapshot,
    AlertPlan,
    AlertSeverity,
)
from src.observability_local.service import ObservabilityPlanner, build_snapshot_from_planner


class TestObservabilityE2EDryRun:
    """Full pipeline: mission emits stage events → tracer records → metrics register → audit logs."""

    def test_full_pipeline_mission_observability(self, tmp_path):
        """Simulate a mission lifecycle with full observability instrumentation."""
        run_id = "run-e2e-001"
        mission_id = "mission-e2e-001"
        trace_id = "trace-e2e-001"

        # 1. Stage lifecycle events
        stages: list[StageEvent] = []
        for name, status in [
            ("validate_contract", StageStatus.COMPLETED),
            ("build_context", StageStatus.COMPLETED),
            ("generate_content", StageStatus.COMPLETED),
            ("approval_gate", StageStatus.COMPLETED),
            ("export_package", StageStatus.COMPLETED),
        ]:
            evt = StageEvent.for_stage(name, phase="execution", mission_id=mission_id, run_id=run_id)
            evt.trace_id = trace_id
            evt.status = status
            stages.append(evt)

        assert len(stages) == 5
        assert all(s.trace_id == trace_id for s in stages)
        assert all(s.status == StageStatus.COMPLETED for s in stages)

        # 2. Trace events via ObservabilityPlanner
        planner_traces = []
        for s in stages:
            t = ObservabilityPlanner.record_trace_event_plan(
                name=s.stage_name,
                attributes={"stage_id": s.stage_id, "status": s.status.value},
                trace_id=trace_id,
            )
            planner_traces.append(t)

        assert len(planner_traces) == 5
        assert all(t.trace_id == trace_id for t in planner_traces)

        # 3. Metric points
        metrics = [
            ObservabilityPlanner.build_metric_point("stages_completed", 5, unit="count"),
            ObservabilityPlanner.build_metric_point("duration_total_ms", 1250.0, unit="ms"),
            ObservabilityPlanner.build_metric_point("artifacts_produced", 4, unit="count"),
        ]
        assert metrics[0].value == 5

        # 4. Run log entries
        logs = [
            ObservabilityPlanner.build_run_log_entry(
                run_id, "mission started", level=RunLogLevel.INFO, module="runtime"
            ),
            ObservabilityPlanner.build_run_log_entry(
                run_id, "all stages completed", level=RunLogLevel.INFO, module="runtime"
            ),
        ]
        assert len(logs) == 2

        # 5. Health signals
        snapshot = ObservabilityPlanner.build_health_snapshot(
            components=[
                {"component": "memory", "status": "healthy", "checks": {"file_backed": True}},
                {"component": "mission_os", "status": "healthy", "checks": {"state_machine": True}},
                {"component": "observability", "status": "healthy", "checks": {"tracer": True, "metrics": True}},
            ]
        )
        assert len(snapshot.health_signals) == 3
        assert all(s.status == HealthStatus.HEALTHY for s in snapshot.health_signals)

        # 6. Build full snapshot from dicts
        full = build_snapshot_from_planner(
            traces=[{"name": "e2e_test", "trace_id": trace_id}],
            metrics=[{"name": "e2e_metric", "value": 42.0}],
            logs=[{"run_id": run_id, "message": "e2e complete"}],
            health=[{"component": "all", "status": "healthy"}],
        )
        assert len(full.traces) == 1
        assert len(full.metrics) == 1
        assert len(full.logs) == 1

        # 7. Alert planning from snapshot (all healthy = no alerts)
        alerts = ObservabilityPlanner.plan_alerts(snapshot)
        assert len(alerts) == 0

        # 8. Audit trail
        audit = AuditTrail()
        audit.record("mission_start", "ok", source="e2e", entry_type=AuditEntryType.EXECUTION)
        audit.record("stages_done", "ok", source="e2e", entry_type=AuditEntryType.EXECUTION)
        audit.record("approval_gate", "APPROVED", source="e2e", entry_type=AuditEntryType.APPROVAL)
        assert audit.entry_count == 3
        assert audit.last_entry.action == "approval_gate"

    def test_error_classification_in_pipeline(self):
        """Error taxonomy integrates with stage events during failure."""
        evt = StageEvent.for_stage("fetch_context", phase="execution", mission_id="m1", run_id="r1")
        evt.status = StageStatus.FAILED
        evt.error = "connection timed out after 30s"

        result = ErrorClassifier.classify(evt.error, exception_type="TimeoutError")
        assert result.category == ErrorCategory.TIMEOUT
        assert result.severity.value == "warning"
        assert ErrorClassifier.is_retryable(result.category) is True

    def test_degraded_component_generates_alerts(self):
        """Degraded health → alert generation."""
        snapshot = ObservabilityPlanner.build_health_snapshot(
            components=[
                {"component": "memory", "status": "degraded", "message": "high latency"},
            ]
        )
        alerts = ObservabilityPlanner.plan_alerts(snapshot)
        assert len(alerts) == 1
        assert alerts[0].severity == AlertSeverity.WARNING
        assert "memory" in alerts[0].title.lower()

    def test_unhealthy_component_generates_critical_alert(self):
        """Unhealthy health → critical alert."""
        snapshot = ObservabilityPlanner.build_health_snapshot(
            components=[
                {"component": "db", "status": "unhealthy", "message": "connection refused"},
            ]
        )
        alerts = ObservabilityPlanner.plan_alerts(snapshot)
        assert len(alerts) == 1
        assert alerts[0].severity == AlertSeverity.CRITICAL
        assert "db" in alerts[0].title.lower()

    def test_sanitization_redacts_secrets(self):
        """ObservabilityPlanner sanitizes sensitive data in payloads."""
        payload = {"api_key": "sk-12345", "user": "lucas", "nested": {"token": "abc"}}
        result = ObservabilityPlanner.sanitize_observability_payload(payload)
        assert result["api_key"] == "[REDACTED]"
        assert result["user"] == "lucas"
        assert result["nested"]["token"] == "[REDACTED]"

    def test_full_e2e_with_failure_and_recovery(self, tmp_path):
        """Full pipeline with one failing stage that gets retried and recovered."""
        run_id = "run-e2e-recovery"
        mission_id = "mission-e2e-recovery"

        # Stage 1: OK
        s1 = StageEvent.for_stage("validate", mission_id=mission_id, run_id=run_id)
        s1.status = StageStatus.COMPLETED

        # Stage 2: FAILED (timeout)
        s2 = StageEvent.for_stage("fetch_data", mission_id=mission_id, run_id=run_id)
        s2.status = StageStatus.FAILED
        s2.error = "connection timed out"

        # Stage 2 retry: OK
        s2_retry = StageEvent.for_stage("fetch_data", mission_id=mission_id, run_id=run_id)
        s2_retry.status = StageStatus.COMPLETED
        s2_retry.metadata["retry"] = True

        # Stage 3: OK
        s3 = StageEvent.for_stage("export", mission_id=mission_id, run_id=run_id)
        s3.status = StageStatus.COMPLETED

        # Classify the error
        classification = ErrorClassifier.classify(s2.error)
        assert classification.category == ErrorCategory.TIMEOUT
        assert ErrorClassifier.is_retryable(classification.category) is True

        # Audit the failure + recovery
        audit = AuditTrail()
        audit.record("fetch_data", "FAILED", source="stage", entry_type=AuditEntryType.ERROR,
                      detail={"error": s2.error, "category": classification.category.value})
        audit.record("fetch_data_retry", "SUCCESS", source="stage", entry_type=AuditEntryType.EXECUTION)

        assert audit.entry_count == 2
        assert audit.query(entry_type="ERROR")[0].detail["category"] == "timeout"

        # Verify full sequence
        all_stages = [s1, s2, s2_retry, s3]
        completed = [s for s in all_stages if s.status == StageStatus.COMPLETED]
        failed = [s for s in all_stages if s.status == StageStatus.FAILED]
        assert len(completed) == 3
        assert len(failed) == 1
        assert failed[0].stage_name == "fetch_data"
