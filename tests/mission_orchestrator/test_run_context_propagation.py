"""Testes de propagação do RunContext (Onda 8 Passo 2).

Verifica que um run_id único flui por: OrchestratorRun → StepRun.
Uma missão multi-passo compartilha o mesmo run_id.
"""
from __future__ import annotations

import pytest

from src.utils.run_context import RunContext
from src.mission_orchestrator.models import OrchestratorRun


# ── OrchestratorRun.new() aceita run_id externo ───────────────────────────────

def test_orchestrator_run_new_uses_provided_run_id():
    ctx = RunContext.new()
    run = OrchestratorRun.new(
        request_text="test request",
        run_id=ctx.run_id,
    )
    assert run.run_id == ctx.run_id


def test_orchestrator_run_new_generates_id_when_none():
    run = OrchestratorRun.new(request_text="test request")
    assert run.run_id.startswith("run_")


def test_orchestrator_run_new_run_id_not_none():
    run = OrchestratorRun.new(request_text="test", run_id="custom-id-123")
    assert run.run_id == "custom-id-123"


# ── build_plan() propaga run_context ─────────────────────────────────────────

def test_build_plan_propagates_run_context(tmp_path):
    from src.mission_orchestrator.planner import build_plan

    ctx = RunContext.new()
    run = build_plan(
        request_text="criar carrossel para @oinatalrn",
        allow_unknown=True,
        run_context=ctx,
    )
    assert run.run_id == ctx.run_id


def test_build_plan_without_context_generates_own_id(tmp_path):
    from src.mission_orchestrator.planner import build_plan

    run = build_plan(
        request_text="criar carrossel",
        allow_unknown=True,
    )
    assert run.run_id.startswith("run_")


def test_build_plan_context_none_stays_none():
    from src.mission_orchestrator.planner import build_plan

    run_a = build_plan(request_text="test a", allow_unknown=True)
    run_b = build_plan(request_text="test b", allow_unknown=True)
    assert run_a.run_id != run_b.run_id


# ── service.run() propaga run_context ────────────────────────────────────────

def test_service_run_propagates_run_context(tmp_path):
    from src.mission_orchestrator import service

    ctx = RunContext.new()
    orch_run = service.run(
        request_text="criar post para @lucastigrereal",
        allow_unknown=True,
        runs_root=tmp_path / "runs",
        runs_log=tmp_path / "runs.jsonl",
        run_context=ctx,
    )
    assert orch_run.run_id == ctx.run_id


def test_service_run_two_separate_contexts_different_ids(tmp_path):
    from src.mission_orchestrator import service

    ctx_a = RunContext.new()
    ctx_b = RunContext.new()
    run_a = service.run(
        request_text="task A",
        allow_unknown=True,
        runs_root=tmp_path / "runs_a",
        runs_log=tmp_path / "runs_a.jsonl",
        run_context=ctx_a,
    )
    run_b = service.run(
        request_text="task B",
        allow_unknown=True,
        runs_root=tmp_path / "runs_b",
        runs_log=tmp_path / "runs_b.jsonl",
        run_context=ctx_b,
    )
    assert run_a.run_id == ctx_a.run_id
    assert run_b.run_id == ctx_b.run_id
    assert run_a.run_id != run_b.run_id


# ── run_graph_dry() aceita run_id externo (já suportado) ─────────────────────

def _make_test_graph():
    from src.execution_graph.builder import build_graph
    from src.squad_composer.composer import compose_squad
    from src.task_decomposer.decomposer import decompose_squad

    squad = compose_squad("criar carrossel de marketing")
    task_plan = decompose_squad(squad)
    return build_graph(squad, task_plan)


def test_run_graph_dry_uses_provided_run_id():
    from src.execution_graph.runner import run_graph_dry

    graph = _make_test_graph()
    ctx = RunContext.new()
    step_run = run_graph_dry(graph, run_id=ctx.run_id)
    assert step_run.graph_run_id == ctx.run_id


def test_run_graph_dry_generates_id_when_no_run_context():
    from src.execution_graph.runner import run_graph_dry

    graph = _make_test_graph()
    step_run = run_graph_dry(graph)
    assert step_run.graph_run_id.startswith("grun_")
