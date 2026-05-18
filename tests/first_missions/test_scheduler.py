"""W183 — Tests for MissionScheduler."""
import pytest
from src.first_missions.models import Mission, MissionStatus
from src.first_missions.scheduler import MissionScheduler, ScheduleStatus


def _sched(dry_run: bool = True) -> MissionScheduler:
    return MissionScheduler(dry_run=dry_run)


# ---------------------------------------------------------------------------
# ScheduledMission
# ---------------------------------------------------------------------------

def test_schedule_now_ready():
    s = _sched()
    m = Mission()
    entry = s.schedule_now(m)
    assert entry.status == ScheduleStatus.READY
    assert entry.entry_id.startswith("sch_")


def test_schedule_future_waiting():
    s = _sched()
    entry = s.schedule(Mission(), run_at="2099-01-01T00:00:00+00:00")
    assert entry.status == ScheduleStatus.WAITING


def test_to_dict():
    s = _sched()
    entry = s.schedule_now(Mission())
    d = entry.to_dict()
    assert "entry_id" in d
    assert "mission_id" in d
    assert d["status"] == "READY"


# ---------------------------------------------------------------------------
# Ready / dispatch
# ---------------------------------------------------------------------------

def test_ready_returns_immediate():
    s = _sched()
    m = Mission()
    s.schedule_now(m)
    ready = s.ready()
    assert len(ready) == 1


def test_future_not_ready():
    s = _sched()
    s.schedule(Mission(), run_at="2099-01-01T00:00:00+00:00")
    assert s.ready() == []


def test_past_run_at_becomes_ready():
    s = _sched()
    s.schedule(Mission(), run_at="2000-01-01T00:00:00+00:00")
    ready = s.ready(_now="2026-01-01T00:00:00+00:00")
    assert len(ready) == 1


def test_dispatch_ready_returns_missions():
    s = _sched()
    m = Mission()
    s.schedule_now(m)
    dispatched = s.dispatch_ready()
    assert len(dispatched) == 1
    assert dispatched[0] is m


def test_dispatch_removes_from_queue():
    s = _sched()
    s.schedule_now(Mission())
    s.dispatch_ready()
    assert len(s.pending()) == 0


def test_dispatch_records_history():
    s = _sched()
    s.schedule_now(Mission())
    s.dispatch_ready()
    assert len(s.history()) == 1


# ---------------------------------------------------------------------------
# Cancel
# ---------------------------------------------------------------------------

def test_cancel_waiting():
    s = _sched()
    entry = s.schedule(Mission(), run_at="2099-01-01T00:00:00+00:00")
    assert s.cancel(entry.entry_id)
    assert entry.status == ScheduleStatus.CANCELLED


def test_cancel_dispatched_fails():
    s = _sched()
    entry = s.schedule_now(Mission())
    s.dispatch_ready()
    assert not s.cancel(entry.entry_id)


def test_cancel_unknown():
    s = _sched()
    assert not s.cancel("unknown_id")


# ---------------------------------------------------------------------------
# Stats + pending
# ---------------------------------------------------------------------------

def test_pending_count():
    s = _sched()
    s.schedule_now(Mission())
    s.schedule(Mission(), run_at="2099-01-01T00:00:00+00:00")
    assert len(s.pending()) == 2


def test_stats():
    s = _sched()
    s.schedule_now(Mission())
    s.dispatch_ready()
    stats = s.stats()
    assert stats["dispatched"] == 1
    assert stats["dry_run"] is True
