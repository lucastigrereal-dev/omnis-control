"""Tests for Step Runner Dry-Run — P8.1."""
from __future__ import annotations

import json
import pytest
from pathlib import Path

from src.execution_graph.models import (
    StepStatus,
    StepNode,
    ExecutionGraph,
    StepRun,
    StepRunLog,
    RUN_STATUS_RUNNING,
    RUN_STATUS_DONE,
    RUN_STATUS_FAILED,
    _make_run_id,
)
from src.execution_graph.runner import run_graph_dry
from src.execution_graph.store import (
    append_event,
    read_events,
    get_step_state,
    write_manifest,
    read_manifest,
    DEFAULT_STORE_ROOT,
)
from src.execution_graph.errors import ExecutionGraphError
from src.squad_composer.composer import compose_squad
from src.task_decomposer.decomposer import decompose_squad
from src.execution_graph.builder import build_graph


# ── Unit: StepRunLog / StepRun serialization ──────────────────────

def test_step_run_log_to_dict():
    log = StepRunLog(
        step_id="s1", role_id="copywriter",
        status="running", message="Started", timestamp="2026-01-01T00:00:00",
    )
    d = log.to_dict()
    assert d["step_id"] == "s1"
    assert d["status"] == "running"


def test_step_run_to_dict():
    log = StepRunLog("s1", "qa", "done", "ok", "t1")
    run = StepRun(
        graph_run_id="grun_abc",
        graph_id="graph_xyz",
        request="test",
        status="done",
        step_states={"s1": "done"},
        logs=[log],
        started_at="t0",
        finished_at="t1",
    )
    d = run.to_dict()
    assert d["graph_run_id"] == "grun_abc"
    assert d["step_states"]["s1"] == "done"
    assert len(d["logs"]) == 1


def test_make_run_id():
    rid = _make_run_id()
    assert rid.startswith("grun_")


# ── Runner: success path ──────────────────────────────────────────

def test_run_graph_dry_marketing():
    squad = compose_squad("criar campanha de marketing para Resort Villa do Sol")
    task_plan = decompose_squad(squad)
    graph = build_graph(squad, task_plan)
    step_run = run_graph_dry(graph)

    assert step_run.status == RUN_STATUS_DONE
    assert len(step_run.step_states) == len(graph.nodes)
    assert all(s == "done" for s in step_run.step_states.values())
    assert len(step_run.logs) == len(graph.nodes) * 2


def test_run_graph_dry_all_steps_executed():
    squad = compose_squad("fazer um post de viagem")
    task_plan = decompose_squad(squad)
    graph = build_graph(squad, task_plan)
    step_run = run_graph_dry(graph)

    executed = set(step_run.step_states.keys())
    expected = {n.step_id for n in graph.nodes}
    assert executed == expected


def test_run_graph_dry_logs_ordered():
    squad = compose_squad("post de viagem em natal")
    task_plan = decompose_squad(squad)
    graph = build_graph(squad, task_plan)
    step_run = run_graph_dry(graph)

    timestamps = [l.timestamp for l in step_run.logs]
    assert timestamps == sorted(timestamps)


def test_run_graph_dry_running_then_done_per_step():
    squad = compose_squad("criar post simples")
    task_plan = decompose_squad(squad)
    graph = build_graph(squad, task_plan)
    step_run = run_graph_dry(graph)

    running_logs = [l for l in step_run.logs if l.status == "running"]
    done_logs = [l for l in step_run.logs if l.status == "done"]
    assert len(running_logs) == len(graph.nodes)
    assert len(done_logs) == len(graph.nodes)


# ── Runner: failure injection ─────────────────────────────────────

def test_run_graph_dry_failure_injection():
    squad = compose_squad("criar campanha de marketing para Resort Villa do Sol")
    task_plan = decompose_squad(squad)
    graph = build_graph(squad, task_plan)

    # Pick the second step to fail
    fail_step = graph.topological_order[1]
    step_run = run_graph_dry(graph, fail_at=fail_step)

    assert step_run.status == RUN_STATUS_FAILED
    assert step_run.step_states[fail_step] == "failed"


def test_run_graph_dry_failure_skips_downstream():
    squad = compose_squad("criar campanha de marketing para Resort Villa do Sol")
    task_plan = decompose_squad(squad)
    graph = build_graph(squad, task_plan)

    fail_step = graph.topological_order[0]
    step_run = run_graph_dry(graph, fail_at=fail_step)

    skipped = [sid for sid, s in step_run.step_states.items() if s == "skipped"]
    assert len(skipped) >= 1
    assert step_run.step_states[fail_step] == "failed"


def test_run_graph_dry_no_failure_all_done():
    squad = compose_squad("criar post de viagem em natal")
    task_plan = decompose_squad(squad)
    graph = build_graph(squad, task_plan)

    step_run = run_graph_dry(graph)  # no fail_at
    assert step_run.status == RUN_STATUS_DONE
    assert "failed" not in step_run.step_states.values()
    assert "skipped" not in step_run.step_states.values()


def test_run_empty_graph_raises():
    graph = ExecutionGraph(
        graph_id="g1", request="r", squad_id="s1", task_plan_id="t1",
        nodes=[], edges=[], topological_order=[], created_at="2026",
    )
    with pytest.raises(ExecutionGraphError, match="empty"):
        run_graph_dry(graph)


# ── Store: JSONL persistence ──────────────────────────────────────

def test_append_and_read_events(tmp_path):
    run_dir = tmp_path / "test_run"
    append_event(run_dir, {"step_id": "s1", "status": "running", "msg": "start"})
    append_event(run_dir, {"step_id": "s1", "status": "done", "msg": "end"})

    events = read_events(run_dir)
    assert len(events) == 2
    assert events[0]["status"] == "running"
    assert events[1]["status"] == "done"


def test_read_events_empty_dir(tmp_path):
    events = read_events(tmp_path / "nonexistent")
    assert events == []


def test_get_step_state_from_events(tmp_path):
    run_dir = tmp_path / "run"
    append_event(run_dir, {"step_id": "s1", "status": "running"})
    append_event(run_dir, {"step_id": "s1", "status": "done"})
    append_event(run_dir, {"step_id": "s2", "status": "done"})

    state = get_step_state(run_dir)
    assert state["s1"] == "done"
    assert state["s2"] == "done"


def test_write_and_read_manifest(tmp_path):
    run_dir = tmp_path / "run"
    data = {"id": "grun_abc", "status": "done"}
    write_manifest(run_dir, data)

    loaded = read_manifest(run_dir)
    assert loaded["id"] == "grun_abc"
    assert loaded["status"] == "done"


def test_read_manifest_nonexistent(tmp_path):
    assert read_manifest(tmp_path / "no_dir") is None


# ── Integration: runner + store ───────────────────────────────────

def test_runner_persists_to_store(tmp_path):
    squad = compose_squad("criar post de viagem")
    task_plan = decompose_squad(squad)
    graph = build_graph(squad, task_plan)
    step_run = run_graph_dry(graph)

    run_dir = tmp_path / step_run.graph_run_id
    write_manifest(run_dir, step_run.to_dict())

    manifest = read_manifest(run_dir)
    assert manifest is not None
    assert manifest["status"] == RUN_STATUS_DONE
    assert manifest["graph_id"] == graph.graph_id


# ── CLI smoke ─────────────────────────────────────────────────────

def test_cli_graph_run():
    import subprocess, sys, os
    result = subprocess.run(
        [sys.executable, "jarvis.py", "graph", "run", "criar post de viagem em natal"],
        capture_output=True, text=True, timeout=30,
        cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    )
    assert result.returncode == 0
    assert "Graph Run" in result.stdout


def test_cli_graph_run_json():
    import subprocess, sys, os
    result = subprocess.run(
        [sys.executable, "jarvis.py", "graph", "run", "criar post de viagem", "--json"],
        capture_output=True, text=True, timeout=30,
        cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "graph_run_id" in data
    assert "step_states" in data
    assert "logs" in data


def test_cli_graph_run_show():
    import subprocess, sys, os
    # First run to create a record
    r1 = subprocess.run(
        [sys.executable, "jarvis.py", "graph", "run", "test show", "--json"],
        capture_output=True, text=True, timeout=30,
        cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    )
    data = json.loads(r1.stdout)
    run_id = data["graph_run_id"]

    # Then show it
    r2 = subprocess.run(
        [sys.executable, "jarvis.py", "graph", "run-show", run_id],
        capture_output=True, text=True, timeout=30,
        cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    )
    assert r2.returncode == 0
    assert run_id in r2.stdout


def test_cli_graph_run_list():
    import subprocess, sys, os
    result = subprocess.run(
        [sys.executable, "jarvis.py", "graph", "run-list"],
        capture_output=True, text=True, timeout=30,
        cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    )
    assert result.returncode == 0
    # Should have at least the runs created by other tests
    assert "grun_" in result.stdout or "No graph runs" in result.stdout
