"""W192 — Tests for MissionLogger."""
import io
import pytest
from src.first_missions.logger import MissionLogger, MissionLogEntry
from src.first_missions.models import Mission, MissionStatus


# ---------------------------------------------------------------------------
# MissionLogEntry
# ---------------------------------------------------------------------------

def test_log_entry_to_dict():
    e = MissionLogEntry(
        mission_id="mss_abc", event="start", status="RUNNING",
        mission_name="test", mission_type="CUSTOM",
    )
    d = e.to_dict()
    assert d["mission_id"] == "mss_abc"
    assert d["event"] == "start"
    assert d["status"] == "RUNNING"


def test_log_entry_format_line():
    e = MissionLogEntry(
        mission_id="mss_abc123", event="complete", status="COMPLETED",
        mission_name="test_mission", mission_type="CUSTOM",
        duration_ms=42.0, dry_run=True,
    )
    line = e.format_line()
    assert "[DRY]" in line
    assert "[COMPLETE]" in line
    assert "mss_abc123" in line
    assert "test_mission" in line
    assert "42ms" in line


def test_log_entry_format_with_error():
    e = MissionLogEntry(
        mission_id="mss_x", event="fail", status="FAILED",
        error="something broke",
    )
    line = e.format_line()
    assert "[FAIL]" in line
    assert "something broke" in line


# ---------------------------------------------------------------------------
# MissionLogger
# ---------------------------------------------------------------------------

def test_logger_log_start():
    log = MissionLogger(dry_run=True)
    m = Mission(name="m1")
    log.log_start(m)
    assert len(log.entries()) == 1
    assert log.entries()[0].event == "start"


def test_logger_log_complete():
    log = MissionLogger(dry_run=True)
    m = Mission(name="m1")
    m.status = MissionStatus.COMPLETED
    log.log_complete(m, duration_ms=50.0)
    e = log.entries()[0]
    assert e.event == "complete"
    assert e.duration_ms == 50.0


def test_logger_log_fail():
    log = MissionLogger(dry_run=True)
    m = Mission(name="fail", error="boom")
    m.status = MissionStatus.FAILED
    log.log_fail(m, duration_ms=10.0)
    e = log.entries()[0]
    assert e.event == "fail"
    assert e.error == "boom"


def test_logger_stats():
    log = MissionLogger(dry_run=True)
    m = Mission(name="m1")
    log.log_start(m)
    m.status = MissionStatus.COMPLETED
    log.log_complete(m)
    m2 = Mission(name="m2")
    log.log_start(m2)
    s = log.stats()
    assert s["total"] == 3
    assert s["by_event"]["start"] == 2
    assert s["by_event"]["complete"] == 1


def test_logger_clear():
    log = MissionLogger(dry_run=True)
    log.log_start(Mission(name="x"))
    log.clear()
    assert len(log.entries()) == 0


# ---------------------------------------------------------------------------
# Stream output
# ---------------------------------------------------------------------------

def test_logger_stream_output():
    buf = io.StringIO()
    log = MissionLogger(dry_run=False, stream=buf)
    m = Mission(name="stream_test")
    log.log_start(m)
    m.status = MissionStatus.COMPLETED
    log.log_complete(m, duration_ms=25.0)
    output = buf.getvalue()
    lines = output.strip().split("\n")
    assert len(lines) == 2
    assert "stream_test" in lines[0]


def test_logger_dry_run_does_not_write_stream():
    buf = io.StringIO()
    log = MissionLogger(dry_run=True, stream=buf)
    log.log_start(Mission(name="dry"))
    assert buf.getvalue() == ""


# ---------------------------------------------------------------------------
# Integration with orchestrator
# ---------------------------------------------------------------------------

def test_orchestrator_logs_on_execution():
    from src.first_missions.orchestrator import MissionOrchestrator
    orch = MissionOrchestrator(dry_run=True)
    m = Mission.content_generation("test", "beach")
    orch.run_one(m)
    entries = orch.log.entries()
    assert len(entries) >= 2  # start + complete
    events = [e.event for e in entries]
    assert "start" in events
