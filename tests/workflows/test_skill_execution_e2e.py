"""Tests — SkillExecutionWorkflow (Onda 29).

Cobertura:
  - run() com planos válidos
  - plans_count, total_entries, succeeded_entries
  - success_rate, unique_skills
  - PlanExecutionResult: total, succeeded, failed, needs_review
  - akasha event emitido
  - error: empty_plans
  - to_dict keys
  - dry_run passado via run()
"""
from __future__ import annotations

import pytest

from src.agentic.task_dispatcher import DispatchEntry, DispatchPlan
from src.akasha_event_sink.adapter import MockAkashaSink
from src.akasha_event_sink.models import SinkStatus
from src.workflows.skill_execution_workflow import SkillExecutionWorkflow


# ── helpers ───────────────────────────────────────────────────────────────────

def _entry(i: int, deliverable: str = "legenda", executor: str = "publisher") -> DispatchEntry:
    return DispatchEntry(
        task_id=f"T-{i:03d}",
        deliverable=deliverable,
        executor=executor,
        dry_run=True,
    )


def _plan(mission_id: str = "M-001", n: int = 2) -> DispatchPlan:
    plan = DispatchPlan(mission_id=mission_id, dry_run=True)
    plan.entries = [_entry(i) for i in range(n)]
    plan.total = n
    return plan


# ── basic run ────────────────────────────────────────────────────────────────

def test_run_succeeds():
    wf = SkillExecutionWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(plans=[_plan()])
    assert result.success is True


def test_run_plans_count():
    wf = SkillExecutionWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(plans=[_plan("M-001"), _plan("M-002")])
    assert result.plans_count == 2


def test_run_total_entries():
    wf = SkillExecutionWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(plans=[_plan(n=3), _plan(n=2)])
    assert result.total_entries == 5


def test_run_run_id_nonempty():
    wf = SkillExecutionWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(plans=[_plan()])
    assert result.run_id
    assert len(result.run_id) == 12


def test_run_dry_run_flag():
    wf = SkillExecutionWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(plans=[_plan()], dry_run=True)
    assert result.dry_run is True


# ── succeeded / failed entries ────────────────────────────────────────────────

def test_run_succeeded_entries_nonzero():
    wf = SkillExecutionWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(plans=[_plan(n=3)])
    # dry_run=True → all entries become "dry_run" status (counted as succeeded)
    assert result.succeeded_entries == 3


def test_run_failed_entries_zero_in_dry_run():
    wf = SkillExecutionWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(plans=[_plan(n=2)])
    assert result.failed_entries == 0


def test_run_success_rate_one_in_dry_run():
    wf = SkillExecutionWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(plans=[_plan(n=4)])
    assert result.success_rate == 1.0


# ── skills_used ───────────────────────────────────────────────────────────────

def test_run_skills_used_nonempty():
    wf = SkillExecutionWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(plans=[_plan(n=2)])
    assert len(result.skills_used) == 2


def test_run_unique_skills_positive():
    wf = SkillExecutionWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(plans=[_plan(n=3)])
    assert result.unique_skills >= 1


# ── plan_results ──────────────────────────────────────────────────────────────

def test_plan_results_count():
    wf = SkillExecutionWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(plans=[_plan("M-001"), _plan("M-002")])
    assert len(result.plan_results) == 2


def test_plan_result_mission_id():
    wf = SkillExecutionWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(plans=[_plan("M-XYZ")])
    assert result.plan_results[0].mission_id == "M-XYZ"


def test_plan_result_total():
    wf = SkillExecutionWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(plans=[_plan(n=3)])
    assert result.plan_results[0].total == 3


def test_plan_result_succeeded_in_dry_run():
    wf = SkillExecutionWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(plans=[_plan(n=2)])
    assert result.plan_results[0].succeeded == 2


# ── akasha event ──────────────────────────────────────────────────────────────

def test_run_emits_akasha_event():
    sink = MockAkashaSink()
    wf = SkillExecutionWorkflow(akasha_sink=sink)
    wf.run(plans=[_plan()])
    events = sink.query_events("skill_execution_completed")
    assert len(events) == 1


def test_run_event_source_is_run_id():
    sink = MockAkashaSink()
    wf = SkillExecutionWorkflow(akasha_sink=sink)
    result = wf.run(plans=[_plan()])
    events = sink.query_events("skill_execution_completed")
    assert events[0].source == result.run_id


def test_run_akasha_event_id_nonempty():
    wf = SkillExecutionWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(plans=[_plan()])
    assert result.akasha_event_id.startswith("ske_")


def test_run_event_status_written():
    sink = MockAkashaSink()
    wf = SkillExecutionWorkflow(akasha_sink=sink)
    wf.run(plans=[_plan()])
    events = sink.query_events("skill_execution_completed")
    assert events[0].status == SinkStatus.WRITTEN


# ── error: empty_plans ───────────────────────────────────────────────────────

def test_empty_plans_success_false():
    wf = SkillExecutionWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(plans=[])
    assert result.success is False


def test_empty_plans_error_field():
    wf = SkillExecutionWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(plans=[])
    assert result.error == "empty_plans"


def test_empty_plans_still_emits_event():
    sink = MockAkashaSink()
    wf = SkillExecutionWorkflow(akasha_sink=sink)
    wf.run(plans=[])
    events = sink.query_events("skill_execution_completed")
    assert len(events) == 1


# ── to_dict ───────────────────────────────────────────────────────────────────

def test_to_dict_has_required_keys():
    wf = SkillExecutionWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(plans=[_plan()])
    d = result.to_dict()
    for key in ["run_id", "success", "plans_count", "total_entries",
                "succeeded_entries", "unique_skills", "success_rate",
                "akasha_event_id", "dry_run", "cost_local_pct"]:
        assert key in d


def test_cost_local_pct_100():
    wf = SkillExecutionWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(plans=[_plan()])
    assert result.cost_local_pct == 100
