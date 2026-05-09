"""Tests for Graph Replay / Resume — P8.2."""
from __future__ import annotations

import json
import pytest

from src.execution_graph.models import (
    ExecutionGraph,
    StepNode,
    StepStatus,
    StepRun,
    _make_run_id,
)
from src.execution_graph.runner import run_graph_dry
from src.execution_graph.replay import resume_graph_run, replay_graph_run
from src.execution_graph.store import (
    write_manifest,
    read_manifest,
    DEFAULT_STORE_ROOT,
)
from src.squad_composer.composer import compose_squad
from src.task_decomposer.decomposer import decompose_squad
from src.execution_graph.builder import build_graph


# ── Helpers ───────────────────────────────────────────────────────

def _make_run_with_snapshot(request="criar post de viagem em natal"):
    squad = compose_squad(request)
    task_plan = decompose_squad(squad)
    graph = build_graph(squad, task_plan)
    step_run = run_graph_dry(graph, include_snapshot=True)
    run_dir = DEFAULT_STORE_ROOT / step_run.graph_run_id
    write_manifest(run_dir, step_run.to_dict())
    return step_run


# ── Unit: from_dict round-trip ────────────────────────────────────

def test_step_node_from_dict_roundtrip():
    original = StepNode(
        step_id="s1", task_id="t1", role_id="copywriter",
        title="Write", description="Desc", expected_output="out",
        depends_on=["s0"], status=StepStatus.RUNNING,
        estimated_duration="10min", assigned_role="copywriter",
    )
    restored = StepNode.from_dict(original.to_dict())
    assert restored.step_id == original.step_id
    assert restored.status == StepStatus.RUNNING
    assert restored.depends_on == original.depends_on


def test_execution_graph_from_dict_roundtrip():
    squad = compose_squad("criar post de viagem")
    task_plan = decompose_squad(squad)
    graph = build_graph(squad, task_plan)

    d = graph.to_dict()
    restored = ExecutionGraph.from_dict(d)

    assert restored.graph_id == graph.graph_id
    assert len(restored.nodes) == len(graph.nodes)
    assert restored.edges == graph.edges
    assert restored.topological_order == graph.topological_order


def test_graph_snapshot_in_manifest():
    step_run = _make_run_with_snapshot()
    run_dir = DEFAULT_STORE_ROOT / step_run.graph_run_id
    manifest = read_manifest(run_dir)
    assert manifest is not None
    assert manifest.get("graph_snapshot") is not None
    assert "nodes" in manifest["graph_snapshot"]
    assert "edges" in manifest["graph_snapshot"]


# ── Resume ────────────────────────────────────────────────────────

def test_resume_all_done_produces_same_result():
    step_run = _make_run_with_snapshot()
    # All steps are done, resume should skip everything
    resumed = resume_graph_run(step_run.graph_run_id)
    assert resumed is not None
    assert resumed.status == "done"
    assert all(s == "done" for s in resumed.step_states.values())


def test_resume_preserves_done_steps():
    # Create a run with failure, then resume
    squad = compose_squad("criar campanha de marketing para Resort Villa do Sol")
    task_plan = decompose_squad(squad)
    graph = build_graph(squad, task_plan)

    # First run: fail at step 0
    fail_step = graph.topological_order[0]
    step_run = run_graph_dry(graph, fail_at=fail_step, include_snapshot=True)
    run_dir = DEFAULT_STORE_ROOT / step_run.graph_run_id
    write_manifest(run_dir, step_run.to_dict())

    # Resume
    resumed = resume_graph_run(step_run.graph_run_id)
    assert resumed is not None
    # The first step was failed, not done — so it should be re-run and succeed now
    assert resumed.step_states[fail_step] == "done"


def test_resume_with_nonexistent_run_returns_none():
    assert resume_graph_run("grun_nonexistent") is None


def test_resume_without_snapshot_returns_none():
    # Create a run without graph_snapshot
    squad = compose_squad("test")
    task_plan = decompose_squad(squad)
    graph = build_graph(squad, task_plan)
    step_run = run_graph_dry(graph)  # no include_snapshot
    run_dir = DEFAULT_STORE_ROOT / step_run.graph_run_id
    write_manifest(run_dir, step_run.to_dict())

    # Resume should fail because no snapshot
    result = resume_graph_run(step_run.graph_run_id)
    assert result is None


def test_resume_skips_steps_that_were_done_before_failure():
    squad = compose_squad("criar post de viagem em natal")
    task_plan = decompose_squad(squad)
    graph = build_graph(squad, task_plan)

    # First run: fail at step 1, so step 0 is done, step 1 failed
    if len(graph.topological_order) >= 2:
        fail_step = graph.topological_order[1]
        first_step = graph.topological_order[0]
        step_run = run_graph_dry(graph, fail_at=fail_step, include_snapshot=True)
        run_dir = DEFAULT_STORE_ROOT / step_run.graph_run_id
        write_manifest(run_dir, step_run.to_dict())

        assert step_run.step_states[first_step] == "done"
        assert step_run.step_states[fail_step] == "failed"

        # Resume: step 0 is done (skipped), step 1 re-runs (succeeds now)
        resumed = resume_graph_run(step_run.graph_run_id)
        assert resumed is not None
        assert resumed.step_states[first_step] == "done"


# ── Replay ────────────────────────────────────────────────────────

def test_replay_runs_all_steps_fresh():
    step_run = _make_run_with_snapshot()
    replayed = replay_graph_run(step_run.graph_run_id)
    assert replayed is not None
    assert replayed.status == "done"
    assert replayed.graph_run_id != step_run.graph_run_id  # new run
    assert all(s == "done" for s in replayed.step_states.values())


def test_replay_after_failure_succeeds():
    squad = compose_squad("criar campanha de marketing para Resort Villa do Sol")
    task_plan = decompose_squad(squad)
    graph = build_graph(squad, task_plan)

    fail_step = graph.topological_order[0]
    step_run = run_graph_dry(graph, fail_at=fail_step, include_snapshot=True)
    run_dir = DEFAULT_STORE_ROOT / step_run.graph_run_id
    write_manifest(run_dir, step_run.to_dict())

    # Replay: everything fresh, no failure
    replayed = replay_graph_run(step_run.graph_run_id)
    assert replayed is not None
    assert replayed.status == "done"
    assert "failed" not in replayed.step_states.values()
    assert "skipped" not in replayed.step_states.values()


def test_replay_with_nonexistent_run_returns_none():
    assert replay_graph_run("grun_fake123") is None


def test_replay_without_snapshot_returns_none():
    squad = compose_squad("test")
    task_plan = decompose_squad(squad)
    graph = build_graph(squad, task_plan)
    step_run = run_graph_dry(graph)  # no snapshot
    run_dir = DEFAULT_STORE_ROOT / step_run.graph_run_id
    write_manifest(run_dir, step_run.to_dict())

    result = replay_graph_run(step_run.graph_run_id)
    assert result is None


# ── CLI smoke ─────────────────────────────────────────────────────

def test_cli_graph_run_resume():
    import subprocess, sys, os
    # Create a run first
    r1 = subprocess.run(
        [sys.executable, "jarvis.py", "graph", "run", "test resume", "--json"],
        capture_output=True, text=True, timeout=30,
        cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    )
    data = json.loads(r1.stdout)
    run_id = data["graph_run_id"]

    # Resume it
    r2 = subprocess.run(
        [sys.executable, "jarvis.py", "graph", "run-resume", run_id],
        capture_output=True, text=True, timeout=30,
        cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    )
    assert r2.returncode == 0
    assert "Resumed" in r2.stdout


def test_cli_graph_run_replay():
    import subprocess, sys, os
    # Create a run first
    r1 = subprocess.run(
        [sys.executable, "jarvis.py", "graph", "run", "test replay", "--json"],
        capture_output=True, text=True, timeout=30,
        cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    )
    data = json.loads(r1.stdout)
    run_id = data["graph_run_id"]

    # Replay it
    r2 = subprocess.run(
        [sys.executable, "jarvis.py", "graph", "run-replay", run_id],
        capture_output=True, text=True, timeout=30,
        cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    )
    assert r2.returncode == 0
    assert "Replayed" in r2.stdout


def test_graph_snapshot_survives_roundtrip():
    """Build a graph, serialize+deserialize, verify identical structure."""
    squad = compose_squad("fazer post de viagem em natal")
    task_plan = decompose_squad(squad)
    graph = build_graph(squad, task_plan)

    d = graph.to_dict()
    restored = ExecutionGraph.from_dict(d)

    # Run both through the runner, they should produce equivalent results
    r1 = run_graph_dry(graph)
    r2 = run_graph_dry(restored)
    assert r1.status == r2.status
    assert len(r1.step_states) == len(r2.step_states)
