"""Testes para SchedulerService + BatchSchedule + ScheduleRun."""
import json
import time
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from src.agentic.batch_runner import BatchReport, BatchRunner, BatchVerdict, BatchItemResult
from src.agentic.scheduler import (
    BatchRunnerFactory,
    BatchSchedule,
    ScheduleRepository,
    ScheduleRun,
    ScheduleRunRepository,
    SchedulerService,
    _add_hours,
    _now_iso,
    _parse_iso,
)
from src.content_queue.models import QueueStatus


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_svc(tmp_path, factory=None) -> SchedulerService:
    sched_repo = ScheduleRepository(path=str(tmp_path / "schedules.jsonl"))
    run_repo = ScheduleRunRepository(path=str(tmp_path / "schedule_runs.jsonl"))
    return SchedulerService(schedule_repo=sched_repo, run_repo=run_repo,
                            batch_runner_factory=factory)


class _NullBatchRunner:
    """BatchRunner que retorna relatório vazio sem tocar na fila."""
    def run(self, limit=5, account_filter=None, status_filter=None) -> BatchReport:
        return BatchReport(
            batch_id="null-batch", dry_run=True, account_filter=account_filter,
            limit=limit, total_candidates=0, total_processed=0,
        )


class _NullFactory:
    def make(self, schedule: BatchSchedule) -> _NullBatchRunner:
        return _NullBatchRunner()


# ── BatchSchedule ─────────────────────────────────────────────────────────────

def test_schedule_is_due_past():
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    s = BatchSchedule(schedule_id="s1", account_filter=None, limit=5, dry_run=True,
                      interval_hours=6, next_run_at=past)
    assert s.is_due is True


def test_schedule_not_due_future():
    future = (datetime.now(timezone.utc) + timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%SZ")
    s = BatchSchedule(schedule_id="s1", account_filter=None, limit=5, dry_run=True,
                      interval_hours=6, next_run_at=future)
    assert s.is_due is False


def test_schedule_disabled_not_due():
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    s = BatchSchedule(schedule_id="s1", account_filter=None, limit=5, dry_run=True,
                      interval_hours=6, next_run_at=past, enabled=False)
    assert s.is_due is False


def test_schedule_advance():
    s = BatchSchedule(schedule_id="s1", account_filter=None, limit=5, dry_run=True,
                      interval_hours=6)
    s.advance()
    assert s.last_run_at is not None
    assert s.run_count == 1
    next_dt = _parse_iso(s.next_run_at)
    last_dt = _parse_iso(s.last_run_at)
    assert abs((next_dt - last_dt).total_seconds() - 6 * 3600) < 5


def test_schedule_roundtrip():
    s = BatchSchedule(schedule_id="s1", account_filter="@x", limit=3, dry_run=False,
                      interval_hours=12)
    restored = BatchSchedule.from_dict(s.to_dict())
    assert restored.schedule_id == "s1"
    assert restored.interval_hours == 12
    assert restored.dry_run is False


# ── ScheduleRepository ────────────────────────────────────────────────────────

def test_repo_save_and_list(tmp_path):
    repo = ScheduleRepository(path=str(tmp_path / "s.jsonl"))
    s = BatchSchedule(schedule_id="s1", account_filter=None, limit=5,
                      dry_run=True, interval_hours=6)
    repo.save(s)
    assert len(repo.list_all()) == 1


def test_repo_update_in_place(tmp_path):
    repo = ScheduleRepository(path=str(tmp_path / "s.jsonl"))
    s = BatchSchedule(schedule_id="s1", account_filter=None, limit=5,
                      dry_run=True, interval_hours=6)
    repo.save(s)
    s.run_count = 3
    repo.save(s)
    all_s = repo.list_all()
    assert len(all_s) == 1
    assert all_s[0].run_count == 3


def test_repo_remove(tmp_path):
    repo = ScheduleRepository(path=str(tmp_path / "s.jsonl"))
    s = BatchSchedule(schedule_id="s1", account_filter=None, limit=5,
                      dry_run=True, interval_hours=6)
    repo.save(s)
    assert repo.remove("s1") is True
    assert repo.list_all() == []


def test_repo_remove_missing(tmp_path):
    repo = ScheduleRepository(path=str(tmp_path / "s.jsonl"))
    assert repo.remove("nonexistent") is False


# ── SchedulerService ──────────────────────────────────────────────────────────

def test_service_add(tmp_path):
    svc = _make_svc(tmp_path, _NullFactory())
    s = svc.add(interval_hours=6, account_filter="@x", limit=3, dry_run=True)
    assert s.schedule_id is not None
    assert len(svc.list_schedules()) == 1


def test_service_add_run_now_is_due(tmp_path):
    svc = _make_svc(tmp_path, _NullFactory())
    s = svc.add(interval_hours=6, run_now=True)
    assert s.is_due is True


def test_service_add_not_run_now_not_due(tmp_path):
    svc = _make_svc(tmp_path, _NullFactory())
    s = svc.add(interval_hours=6, run_now=False)
    assert s.is_due is False


def test_service_remove(tmp_path):
    svc = _make_svc(tmp_path, _NullFactory())
    s = svc.add(interval_hours=6)
    assert svc.remove(s.schedule_id) is True
    assert svc.list_schedules() == []


def test_service_remove_missing(tmp_path):
    svc = _make_svc(tmp_path, _NullFactory())
    assert svc.remove("nonexistent") is False


def test_service_run_due_none_due(tmp_path):
    svc = _make_svc(tmp_path, _NullFactory())
    svc.add(interval_hours=6, run_now=False)
    executed = svc.run_due()
    assert executed == []


def test_service_run_due_executes(tmp_path):
    svc = _make_svc(tmp_path, _NullFactory())
    svc.add(interval_hours=6, run_now=True)
    executed = svc.run_due()
    assert len(executed) == 1


def test_service_run_due_advances_schedule(tmp_path):
    svc = _make_svc(tmp_path, _NullFactory())
    s = svc.add(interval_hours=6, run_now=True)
    svc.run_due()
    updated = svc.list_schedules()[0]
    assert updated.run_count == 1
    assert updated.last_run_at is not None
    assert updated.is_due is False


def test_service_run_due_records_history(tmp_path):
    svc = _make_svc(tmp_path, _NullFactory())
    svc.add(interval_hours=6, run_now=True)
    svc.run_due()
    history = svc.history()
    assert len(history) == 1


def test_service_history_filtered(tmp_path):
    svc = _make_svc(tmp_path, _NullFactory())
    s1 = svc.add(interval_hours=1, run_now=True)
    s2 = svc.add(interval_hours=2, run_now=True)
    svc.run_due()
    assert len(svc.history(s1.schedule_id)) == 1
    assert len(svc.history(s2.schedule_id)) == 1


def test_service_multiple_due(tmp_path):
    svc = _make_svc(tmp_path, _NullFactory())
    for _ in range(3):
        svc.add(interval_hours=1, run_now=True)
    executed = svc.run_due()
    assert len(executed) == 3


def test_service_runs_multiple_schedules_with_same_next_run_at(tmp_path):
    sched_repo = ScheduleRepository(path=str(tmp_path / "schedules.jsonl"))
    run_repo = ScheduleRunRepository(path=str(tmp_path / "schedule_runs.jsonl"))
    svc = SchedulerService(
        schedule_repo=sched_repo,
        run_repo=run_repo,
        batch_runner_factory=_NullFactory(),
    )
    same_due_at = (datetime.now(timezone.utc) - timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    for idx in range(2):
        sched_repo.save(
            BatchSchedule(
                schedule_id=f"s{idx}",
                account_filter=None,
                limit=5,
                dry_run=True,
                interval_hours=1,
                next_run_at=same_due_at,
            )
        )

    executed = svc.run_due()

    assert [run.schedule_id for run in executed] == ["s0", "s1"]
    assert len(svc.history()) == 2


def test_service_schedule_can_advance_past_one_run_count(tmp_path):
    svc = _make_svc(tmp_path, _NullFactory())
    schedule = svc.add(interval_hours=1, run_now=True)
    svc.run_due()
    updated = svc.list_schedules()[0]
    updated.next_run_at = (datetime.now(timezone.utc) - timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    svc._schedules.save(updated)

    svc.run_due()

    assert svc.list_schedules()[0].run_count == 2
    assert len(svc.history(schedule.schedule_id)) == 2


def test_schedule_run_to_dict():
    r = ScheduleRun(
        run_id="r1", schedule_id="s1", account_filter="@x",
        limit=5, dry_run=True, approved=2, needs_review=1, failed=0,
        total_processed=3, batch_id="b1",
    )
    d = r.to_dict()
    assert d["approved"] == 2
    json.dumps(d)


def test_schedule_run_from_dict_roundtrip():
    original = ScheduleRun(
        run_id="r1", schedule_id="s1", account_filter="@x",
        limit=5, dry_run=True, approved=2, needs_review=1, failed=0,
        total_processed=3, batch_id="b1",
    )

    restored = ScheduleRun.from_dict(original.to_dict())

    assert restored.run_id == original.run_id
    assert restored.schedule_id == original.schedule_id
    assert restored.account_filter == original.account_filter
    assert restored.total_processed == original.total_processed
