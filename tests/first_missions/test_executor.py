"""W182 — Tests for MissionExecutor."""
import pytest
from src.first_missions.executor import ExecutionResult, MissionExecutor
from src.first_missions.models import Mission, MissionPriority, MissionStatus, MissionType


def _executor(dry_run: bool = True) -> MissionExecutor:
    return MissionExecutor(dry_run=dry_run)


# ---------------------------------------------------------------------------
# ExecutionResult
# ---------------------------------------------------------------------------

def test_execution_result_to_dict():
    r = ExecutionResult(mission_id="mss_abc", ok=True, result={"x": 1})
    d = r.to_dict()
    assert d["mission_id"] == "mss_abc"
    assert d["ok"] is True
    assert d["result"] == {"x": 1}


# ---------------------------------------------------------------------------
# Dry-run execution
# ---------------------------------------------------------------------------

def test_dry_run_marks_completed():
    exe = _executor(dry_run=True)
    m = Mission.content_generation("lucastigrereal", "travel")
    result = exe.execute(m)
    assert result.ok
    assert result.dry_run is True
    assert m.status == MissionStatus.COMPLETED


def test_dry_run_result_has_simulated_flag():
    exe = _executor(dry_run=True)
    m = Mission()
    result = exe.execute(m)
    assert result.result.get("simulated") is True


def test_dry_run_sets_started_at():
    exe = _executor(dry_run=True)
    m = Mission()
    exe.execute(m)
    assert m.started_at != ""


def test_dry_run_sets_completed_at():
    exe = _executor(dry_run=True)
    m = Mission()
    exe.execute(m)
    assert m.completed_at != ""


# ---------------------------------------------------------------------------
# Real execution (non-dry-run)
# ---------------------------------------------------------------------------

def test_real_content_generation():
    exe = _executor(dry_run=False)
    m = Mission.content_generation("oinatalrn", "beach")
    result = exe.execute(m)
    assert result.ok
    assert "caption" in result.result
    assert "oinatalrn" in result.result["caption"]


def test_real_metric_report():
    exe = _executor(dry_run=False)
    m = Mission.metric_report("followers", "weekly")
    result = exe.execute(m)
    assert result.ok
    assert result.result["metric"] == "followers"


def test_real_health_snapshot():
    exe = _executor(dry_run=False)
    m = Mission.health_snapshot()
    result = exe.execute(m)
    assert result.ok
    assert "modules" in result.result


def test_real_generic_mission():
    exe = _executor(dry_run=False)
    m = Mission(mission_type=MissionType.CUSTOM)
    result = exe.execute(m)
    assert result.ok
    assert result.result["executed"] is True


# ---------------------------------------------------------------------------
# Terminal state guard
# ---------------------------------------------------------------------------

def test_cannot_execute_completed_mission():
    exe = _executor()
    m = Mission(status=MissionStatus.COMPLETED)
    result = exe.execute(m)
    assert not result.ok
    assert "terminal" in result.error


def test_cannot_execute_failed_mission():
    exe = _executor()
    m = Mission(status=MissionStatus.FAILED)
    result = exe.execute(m)
    assert not result.ok


def test_cannot_execute_cancelled_mission():
    exe = _executor()
    m = Mission(status=MissionStatus.CANCELLED)
    result = exe.execute(m)
    assert not result.ok


# ---------------------------------------------------------------------------
# Custom handler
# ---------------------------------------------------------------------------

def test_register_custom_handler():
    exe = _executor(dry_run=False)
    exe.register_handler(MissionType.CAMPAIGN_AUDIT, lambda m: {"audited": True, "score": 99})
    m = Mission(mission_type=MissionType.CAMPAIGN_AUDIT)
    result = exe.execute(m)
    assert result.ok
    assert result.result["score"] == 99


def test_handler_exception_marks_failed():
    exe = _executor(dry_run=False)
    exe.register_handler(MissionType.CUSTOM, lambda m: (_ for _ in ()).throw(RuntimeError("boom")))
    m = Mission(mission_type=MissionType.CUSTOM)
    result = exe.execute(m)
    assert not result.ok
    assert "boom" in result.error
    assert m.status == MissionStatus.FAILED


# ---------------------------------------------------------------------------
# execute_many + stats
# ---------------------------------------------------------------------------

def test_execute_many():
    exe = _executor()
    missions = [Mission() for _ in range(3)]
    results = exe.execute_many(missions)
    assert len(results) == 3
    assert all(r.ok for r in results)


def test_stats():
    exe = _executor(dry_run=False)
    exe.execute(Mission.content_generation("a", "b"))
    exe.register_handler(MissionType.CUSTOM, lambda m: (_ for _ in ()).throw(RuntimeError()))
    exe.execute(Mission(mission_type=MissionType.CUSTOM))
    s = exe.stats()
    assert s["total_executions"] == 2
    assert s["successful"] == 1
    assert s["failed"] == 1


def test_history():
    exe = _executor()
    exe.execute(Mission())
    exe.execute(Mission())
    assert len(exe.history()) == 2
