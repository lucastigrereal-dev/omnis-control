"""Testes para AgentRun + AgentStep."""
import os
import pytest

from src.agentic.agent_models import (
    AgentRun,
    AgentRunRepository,
    AgentRunStatus,
    AgentStep,
    StepStatus,
)


# ── AgentStep ────────────────────────────────────────────────────────────────

def test_step_complete():
    step = AgentStep(step_id="s1", run_id="r1", name="fetch")
    step.complete("got 5 items")
    assert step.status == StepStatus.OK
    assert step.output_summary == "got 5 items"
    assert step.finished_at is not None


def test_step_skip():
    step = AgentStep(step_id="s2", run_id="r1", name="query")
    step.skip("dry_run mode")
    assert step.status == StepStatus.SKIPPED
    assert step.finished_at is not None


def test_step_fail():
    step = AgentStep(step_id="s3", run_id="r1", name="write")
    step.fail("not found")
    assert step.status == StepStatus.ERROR
    assert step.error == "not found"


def test_step_roundtrip():
    step = AgentStep(step_id="s4", run_id="r1", name="test")
    step.complete("ok")
    d = step.to_dict()
    restored = AgentStep.from_dict(d)
    assert restored.step_id == "s4"
    assert restored.status == StepStatus.OK


# ── AgentRun ─────────────────────────────────────────────────────────────────

def test_run_add_step():
    run = AgentRun(run_id="r1", agent="test_agent", account_handle="@test", objective="alcance")
    step = run.add_step("fetch", input_summary="id=123")
    assert step.run_id == "r1"
    assert len(run.steps) == 1
    assert step.status == StepStatus.PENDING


def test_run_complete_dry():
    run = AgentRun(run_id="r2", agent="test_agent", account_handle="@test", objective="alcance", dry_run=True)
    run.complete(result={"draft_id": "abc"})
    assert run.status == AgentRunStatus.DRY_RUN
    assert run.result["draft_id"] == "abc"
    assert run.finished_at is not None


def test_run_complete_real():
    run = AgentRun(run_id="r3", agent="test_agent", account_handle="@test", objective="alcance", dry_run=False)
    run.complete()
    assert run.status == AgentRunStatus.COMPLETED


def test_run_fail():
    run = AgentRun(run_id="r4", agent="test_agent", account_handle="@test", objective="alcance")
    run.fail("item not found")
    assert run.status == AgentRunStatus.FAILED
    assert run.error == "item not found"


def test_run_roundtrip():
    run = AgentRun(run_id="r5", agent="caption_draft_agent", account_handle="@oinatalrn", objective="alcance")
    run.add_step("fetch").complete("item found")
    run.complete({"draft_id": "xyz123"})
    d = run.to_dict()
    restored = AgentRun.from_dict(d)
    assert restored.run_id == "r5"
    assert len(restored.steps) == 1
    assert restored.steps[0].status == StepStatus.OK
    assert restored.result["draft_id"] == "xyz123"


# ── AgentRunRepository ───────────────────────────────────────────────────────

def test_repo_save_and_list(tmp_path):
    path = str(tmp_path / "agent_runs.jsonl")
    repo = AgentRunRepository(path=path)

    run = AgentRun(run_id="r6", agent="test_agent", account_handle="@x", objective="alcance")
    run.complete()
    repo.save(run)

    runs = repo.list_all()
    assert len(runs) == 1
    assert runs[0].run_id == "r6"


def test_repo_get(tmp_path):
    path = str(tmp_path / "agent_runs.jsonl")
    repo = AgentRunRepository(path=path)

    for i in range(3):
        r = AgentRun(run_id=f"r{i}", agent="a", account_handle="@x", objective="o")
        r.complete()
        repo.save(r)

    found = repo.get("r1")
    assert found is not None
    assert found.run_id == "r1"

    missing = repo.get("r99")
    assert missing is None


def test_repo_empty(tmp_path):
    path = str(tmp_path / "empty.jsonl")
    repo = AgentRunRepository(path=path)
    assert repo.list_all() == []
