"""Validação Final Onda 8 — multi-agente coordenado end-to-end.

Verifica: um run_id único flui por toda a stack
(OrchestratorRun → ExecutionGraph → SkillRunnerBridge → Legos),
Legos coordenados, context_store propagado, max_steps guardando.
"""
from __future__ import annotations

import pytest

from src.utils.run_context import RunContext
from src.execution_graph.mission_bridge import run_full_pipeline
from src.execution_graph.runner import run_graph_dry, run_graph_real
from src.execution_graph.builder import build_graph
from src.squad_composer.composer import compose_squad
from src.task_decomposer.decomposer import decompose_squad
from src.legos.registry import default_registry
from src.agentic.skill_runner_bridge import SkillRunnerBridge


# ── run_id único flui por toda a stack ───────────────────────────────────────

def test_single_run_id_flows_full_pipeline(tmp_path):
    """Um run_id externo deve aparecer no orch_run, no graph_run_id."""
    ctx = RunContext.new()
    orch_run, step_run = run_full_pipeline(
        request_text="pesquisar hotéis em Natal e publicar post",
        allow_unknown=True,
        runs_root=tmp_path / "runs",
        runs_log=tmp_path / "runs.jsonl",
        run_context=ctx,
    )
    assert orch_run.run_id == ctx.run_id
    assert step_run is not None
    assert step_run.graph_run_id == ctx.run_id


def test_two_parallel_pipelines_have_distinct_ids(tmp_path):
    """Dois pipelines simultâneos com contextos distintos → run_ids distintos."""
    ctx_a = RunContext.new()
    ctx_b = RunContext.new()
    assert ctx_a.run_id != ctx_b.run_id

    orch_a, step_a = run_full_pipeline(
        request_text="criar carrossel turismo",
        allow_unknown=True,
        runs_root=tmp_path / "runs_a",
        runs_log=tmp_path / "runs_a.jsonl",
        run_context=ctx_a,
    )
    orch_b, step_b = run_full_pipeline(
        request_text="criar stories gastronomia",
        allow_unknown=True,
        runs_root=tmp_path / "runs_b",
        runs_log=tmp_path / "runs_b.jsonl",
        run_context=ctx_b,
    )

    assert orch_a.run_id == ctx_a.run_id
    assert orch_b.run_id == ctx_b.run_id
    assert orch_a.run_id != orch_b.run_id


# ── Legos coordenados via LegoRegistry ───────────────────────────────────────

def test_lego_registry_routes_research_lead():
    """research_lead executor deve rotear para lego:research_conductor."""
    from src.agentic.task_dispatcher import DispatchEntry

    reg = default_registry()
    bridge = SkillRunnerBridge(dry_run=True, lego_registry=reg)
    entry = DispatchEntry(
        task_id="e2e_t1",
        deliverable="research best hotels in Natal RN for luxury travelers",
        executor="research_lead",
        dry_run=True,
    )
    result = bridge.execute_entry(entry)
    assert result.skill_id == "lego:research_conductor"
    assert result.status == "dry_run"


def test_lego_registry_routes_channel_messenger():
    """channel_messenger executor deve rotear para lego:channel_messenger."""
    from src.agentic.task_dispatcher import DispatchEntry

    reg = default_registry()
    bridge = SkillRunnerBridge(dry_run=True, lego_registry=reg)
    entry = DispatchEntry(
        task_id="e2e_t2",
        deliverable="send notification: new hotel article published",
        executor="channel_messenger",
        dry_run=True,
    )
    result = bridge.execute_entry(entry)
    assert result.skill_id == "lego:channel_messenger"
    assert result.status == "dry_run"


def test_lego_context_flow_research_to_publish():
    """Context propagado: research output aparece como upstream_context no segundo step."""
    from src.agentic.task_dispatcher import DispatchEntry
    from src.execution_graph.runner import _collect_upstream_context
    from src.execution_graph.models import StepNode

    # Simulate: step 1 (research) completes, output stored
    context_store = {"s_research": "Top 5 hotels Natal: Serhs, Iate, Beach Park, Maracajau, Rifoles"}

    # Step 2 (publish) picks up the upstream context
    publish_node = StepNode(
        step_id="s_publish",
        task_id="t_publish",
        title="Publish Post",
        description="Publish hotel roundup",
        role_id="channel_messenger",
        assigned_role="channel_messenger",
        expected_output="post published successfully",
        depends_on=["s_research"],
    )
    upstream = _collect_upstream_context(publish_node, context_store)
    assert "[s_research]:" in upstream
    assert "Serhs" in upstream

    # Inject into entry (as the runner would)
    entry = DispatchEntry(
        task_id="t_publish",
        deliverable="publish hotel roundup post",
        executor="channel_messenger",
        dry_run=True,
    )
    entry.result_hint = upstream
    assert "Serhs" in entry.result_hint


# ── context_store populated in full graph dry run ────────────────────────────

def test_full_graph_dry_run_with_context_store():
    squad = compose_squad("pesquisar e publicar post de hoteis em Natal")
    task_plan = decompose_squad(squad)
    graph = build_graph(squad, task_plan)

    ctx = RunContext.new()
    store: dict[str, str] = {}
    step_run = run_graph_dry(graph, run_id=ctx.run_id, context_store=store)

    assert step_run.graph_run_id == ctx.run_id
    assert step_run.status == "done"
    assert len(store) > 0


# ── max_steps guard doesn't fire for normal missions ─────────────────────────

def test_max_steps_guard_silent_on_normal_mission():
    squad = compose_squad("criar carrossel para @oinatalrn")
    task_plan = decompose_squad(squad)
    graph = build_graph(squad, task_plan)

    step_run = run_graph_dry(graph)
    guard_logs = [log for log in step_run.logs if log.role_id == "guard"]
    assert len(guard_logs) == 0
    assert len(graph.nodes) < 50


# ── SkillRunnerBridge + LegoRegistry + context_store (run_graph_real) ─────────

def test_run_graph_real_with_lego_registry_and_context():
    squad = compose_squad("pesquisar hoteis e publicar")
    task_plan = decompose_squad(squad)
    graph = build_graph(squad, task_plan)

    reg = default_registry()
    bridge = SkillRunnerBridge(dry_run=True, lego_registry=reg)
    store: dict[str, str] = {}

    step_run = run_graph_real(graph, bridge, context_store=store)
    assert step_run.status == "done"
    assert len(store) > 0


# ── validator node does not block real missions ───────────────────────────────

def test_validator_does_not_block_full_pipeline(tmp_path):
    ctx = RunContext.new()
    orch_run, step_run = run_full_pipeline(
        request_text="criar post para hotel em Natal",
        allow_unknown=True,
        runs_root=tmp_path / "runs",
        runs_log=tmp_path / "runs.jsonl",
        run_context=ctx,
    )
    assert step_run is not None
    assert step_run.status == "done"
    # No validator failures on real pipeline (all expected_outputs pass validation)
    validator_error_logs = [
        log for log in step_run.logs
        if log.role_id == "validator" and "not propagated" in log.message
    ]
    assert len(validator_error_logs) == 0
