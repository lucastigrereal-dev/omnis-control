"""W185 — Tests for MissionOrchestrator (E2E)."""
import pytest
from src.first_missions.executor import MissionExecutor
from src.first_missions.models import Mission, MissionPriority, MissionStatus, MissionType
from src.first_missions.orchestrator import MissionOrchestrator, OrchestratorResult


def _orch(dry_run: bool = True) -> MissionOrchestrator:
    return MissionOrchestrator(dry_run=dry_run)


# ---------------------------------------------------------------------------
# OrchestratorResult
# ---------------------------------------------------------------------------

def test_orchestrator_result_empty():
    r = OrchestratorResult.empty()
    assert r.ok is True
    assert r.missions_executed == 0
    assert r.successful == 0
    assert r.failed == 0


def test_orchestrator_result_to_dict():
    r = OrchestratorResult(missions_executed=5, successful=4, failed=1)
    d = r.to_dict()
    assert d["missions_executed"] == 5
    assert d["successful"] == 4
    assert d["failed"] == 1
    assert d["ok"] is False


# ---------------------------------------------------------------------------
# Submit
# ---------------------------------------------------------------------------

def test_submit_registers_and_schedules():
    orch = _orch()
    m = Mission(name="e2e-test")
    orch.submit(m)
    assert orch.registry.get(m.mission_id) is m
    assert len(orch.scheduler.pending()) == 1


def test_submit_with_future_run_at():
    orch = _orch()
    m = Mission()
    orch.submit(m, run_at="2099-01-01T00:00:00+00:00")
    assert len(orch.scheduler.pending()) == 1
    assert orch.scheduler.ready() == []


def test_submit_many():
    orch = _orch()
    missions = [Mission() for _ in range(3)]
    orch.submit_many(missions)
    assert orch.registry.stats()["total"] == 3
    assert len(orch.scheduler.pending()) == 3


# ---------------------------------------------------------------------------
# Run one
# ---------------------------------------------------------------------------

def test_run_one_executes_and_stores():
    orch = _orch(dry_run=True)
    m = Mission.content_generation("lucastigrereal", "beach")
    stored = orch.run_one(m)
    assert stored.mission_id == m.mission_id
    assert stored.dry_run is True
    assert orch.result_store.get(stored.result_id) is stored
    # Mission should be completed
    assert m.status == MissionStatus.COMPLETED


def test_run_one_real():
    orch = _orch(dry_run=False)
    m = Mission.content_generation("oinatalrn", "sunset")
    stored = orch.run_one(m)
    assert stored.status == "COMPLETED"
    assert "caption" in stored.result


# ---------------------------------------------------------------------------
# Run pending
# ---------------------------------------------------------------------------

def test_run_pending_executes_all_ready():
    orch = _orch(dry_run=True)
    orch.submit_many([Mission() for _ in range(5)])
    result = orch.run_pending()
    assert result.missions_executed == 5
    assert result.successful == 5
    assert result.ok is True
    assert len(result.results) == 5


def test_run_pending_no_ready_returns_empty():
    orch = _orch()
    result = orch.run_pending()
    assert result.missions_executed == 0


def test_run_pending_mixed_priorities():
    orch = _orch(dry_run=True)
    orch.submit(Mission(priority=MissionPriority.HIGH))
    orch.submit(Mission(priority=MissionPriority.LOW))
    result = orch.run_pending()
    assert result.missions_executed == 2
    assert result.successful == 2


def test_run_pending_skips_future():
    orch = _orch(dry_run=True)
    orch.submit(Mission(), run_at="2099-01-01T00:00:00+00:00")
    orch.submit(Mission())  # immediate
    result = orch.run_pending()
    assert result.missions_executed == 1


def test_run_pending_handles_failure():
    orch = _orch(dry_run=False)
    orch.executor.register_handler(MissionType.CUSTOM, lambda m: (_ for _ in ()).throw(RuntimeError("boom")))
    m = Mission(mission_type=MissionType.CUSTOM)
    orch.submit(m)
    result = orch.run_pending()
    assert result.missions_executed == 1
    assert result.failed == 1
    assert result.ok is False
    assert "boom" in result.errors[0]


# ---------------------------------------------------------------------------
# E2E full pipeline
# ---------------------------------------------------------------------------

def test_e2e_full_pipeline_dry():
    orch = _orch(dry_run=True)
    orch.submit(Mission.content_generation("lucastigrereal", "travel"))
    orch.submit(Mission.metric_report("followers", "daily"))
    orch.submit(Mission.health_snapshot())
    orch.submit(Mission(name="custom", mission_type=MissionType.CAMPAIGN_AUDIT))

    result = orch.run_pending()
    assert result.missions_executed == 4
    assert result.successful == 4
    assert orch.registry.stats()["total"] == 4
    assert orch.result_store.stats()["total"] == 4


def test_e2e_full_pipeline_real():
    orch = _orch(dry_run=False)
    orch.submit(Mission.content_generation("afamiliatigrereal", "kids"))
    orch.submit(Mission.metric_report("reach", "weekly"))
    orch.submit(Mission.health_snapshot())

    result = orch.run_pending()
    assert result.missions_executed == 3
    assert result.successful == 3

    # Verify stored results
    stored = orch.result_store.query()
    assert len(stored) == 3
    types = {r.mission_type for r in stored}
    assert "CONTENT_GENERATION" in types
    assert "METRIC_REPORT" in types
    assert "HEALTH_SNAPSHOT" in types


# ---------------------------------------------------------------------------
# Status + summary
# ---------------------------------------------------------------------------

def test_status_aggregates_all_modules():
    orch = _orch(dry_run=True)
    orch.submit(Mission())
    s = orch.status()
    assert "registry" in s
    assert "scheduler" in s
    assert "executor" in s
    assert "result_store" in s
    assert s["dry_run"] is True
    assert s["registry"]["total"] == 1


def test_summary_string():
    orch = _orch(dry_run=True)
    orch.submit(Mission())
    orch.run_pending()
    text = orch.summary()
    assert "MissionOrchestrator" in text
    assert "(dry-run)" in text
    assert "1 stored" in text


# ---------------------------------------------------------------------------
# JSONL persistence E2E
# ---------------------------------------------------------------------------

def test_e2e_with_jsonl_persistence(tmp_path):
    path = tmp_path / "missions.jsonl"
    orch = MissionOrchestrator(dry_run=False, result_path=path)
    orch.submit(Mission.content_generation("test", "topic"))
    orch.submit(Mission.metric_report("impressions"))
    orch.run_pending()

    # Reload
    orch2 = MissionOrchestrator(dry_run=False, result_path=path)
    assert orch2.result_store.stats()["total"] == 2
