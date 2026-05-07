"""Testes do MetricsRecorder — P0.9."""
from __future__ import annotations

import pytest

from src.metrics.recorder import MetricsRecorder
from src.metrics.store import MetricsStore


@pytest.fixture
def tmp_recorder(tmp_path):
    return MetricsRecorder(base_dir=str(tmp_path / "metrics_spine"))


class TestStartFinishRun:
    """start_run + finish_run."""

    def test_start_run_creates_summary(self, tmp_recorder):
        summary = tmp_recorder.start_run(mission_id="m001", run_id="r001")
        assert summary.run_id == "r001"
        assert summary.status == "running"

    def test_start_run_emits_metric(self, tmp_recorder):
        tmp_recorder.start_run(mission_id="m001", run_id="r001")
        metrics = tmp_recorder.store.get_metrics(event_type="run_started")
        assert len(metrics) == 1
        assert metrics[0].mission_id == "m001"

    def test_finish_run_updates_status(self, tmp_recorder):
        tmp_recorder.start_run(mission_id="m001", run_id="r001")
        updated = tmp_recorder.finish_run("r001", "success", warnings_count=3)
        assert updated is not None
        assert updated.status == "success"
        assert updated.warnings_count == 3

    def test_finish_run_emits_metric(self, tmp_recorder):
        tmp_recorder.start_run(mission_id="m001", run_id="r001")
        tmp_recorder.finish_run("r001", "success")
        metrics = tmp_recorder.store.get_metrics(event_type="run_completed")
        assert len(metrics) == 1
        assert metrics[0].status == "success"

    def test_finish_nonexistent_run(self, tmp_recorder):
        assert tmp_recorder.finish_run("ghost", "success") is None


class TestRecordToolUse:
    """record_tool_use."""

    def test_record_tool_use_creates_metric(self, tmp_recorder):
        event = tmp_recorder.record_tool_use("docker", mission_id="m001")
        assert event.tool_id == "docker"
        assert event.event_type == "tool_use"
        assert event.mission_id == "m001"


class TestRecordMissionEvent:
    """record_mission_event."""

    def test_record_mission_event(self, tmp_recorder):
        event = tmp_recorder.record_mission_event("m001", "checkpoint_created")
        assert event.mission_id == "m001"
        assert event.event_type == "checkpoint_created"


class TestSummarize:
    """summarize_mission + summarize_tools + summarize_today."""

    def test_summarize_today_empty(self, tmp_recorder):
        summary = tmp_recorder.summarize_today()
        assert summary["total"] == 0

    def test_summarize_today_with_runs(self, tmp_recorder):
        from datetime import datetime, timezone
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Create runs with today's date
        r1 = tmp_recorder.start_run(mission_id="m1", run_id="r1")
        tmp_recorder.store.update_run("r1", started_at=f"{today}T10:00:00Z", status="success")
        r2 = tmp_recorder.start_run(mission_id="m2", run_id="r2")
        tmp_recorder.store.update_run("r2", started_at=f"{today}T11:00:00Z", status="failed")

        summary = tmp_recorder.summarize_today()
        assert summary["total"] == 2
        assert summary["succeeded"] == 1
        assert summary["failed"] == 1

    def test_summarize_mission(self, tmp_recorder):
        tmp_recorder.record_mission_event("m001", "mission_started")
        tmp_recorder.record_mission_event("m001", "checkpoint_created")
        tmp_recorder.record_tool_use("docker", mission_id="m001", status="success")

        result = tmp_recorder.summarize_mission("m001")
        assert result["total_events"] == 3
        assert "mission_started" in result["by_event_type"]
        assert "checkpoint_created" in result["by_event_type"]

    def test_summarize_tools(self, tmp_recorder):
        tmp_recorder.record_tool_use("docker", status="success")
        tmp_recorder.record_tool_use("docker", status="success")
        tmp_recorder.record_tool_use("publisher", status="blocked")

        result = tmp_recorder.summarize_tools()
        assert result["unique_tools"] == 2
        by_tool = result["by_tool"]
        assert by_tool["docker"]["count"] == 2
        assert by_tool["publisher"]["count"] == 1
