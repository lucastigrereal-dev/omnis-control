"""Tests for P8.5 — Mission → Squad → Graph Integration."""
from __future__ import annotations

import pytest

from src.mission_orchestrator.planner import build_plan
from src.mission_orchestrator.executor import execute
from src.mission_orchestrator.models import OrchestratorRun
from src.execution_graph.mission_bridge import (
    build_graph_from_orchestrator,
    run_graph_from_orchestrator,
    run_full_pipeline,
)


# ── Planner s06/s07 ────────────────────────────────────────────────

def test_plan_includes_s06_s07():
    """Plan should include squad composition and graph steps."""
    run = build_plan("criar post de viagem em natal")
    step_ids = [s.step_id for s in run.steps]
    assert "s06" in step_ids
    assert "s07" in step_ids


def test_plan_s06_has_correct_module():
    run = build_plan("criar post de viagem em natal")
    s06 = next(s for s in run.steps if s.step_id == "s06")
    assert s06.module == "squad_composer"


def test_plan_s07_has_correct_module():
    run = build_plan("criar post de viagem em natal")
    s07 = next(s for s in run.steps if s.step_id == "s07")
    assert s07.module == "execution_graph"


def test_plan_total_steps_is_7():
    run = build_plan("criar post de viagem em natal")
    assert len(run.steps) == 7


# ── Models: squad_id + graph_run_id fields ─────────────────────────

def test_orchestrator_run_has_squad_id_field():
    run = build_plan("criar post de viagem")
    assert hasattr(run, "squad_id")
    assert run.squad_id is None


def test_orchestrator_run_has_graph_run_id_field():
    run = build_plan("criar post de viagem")
    assert hasattr(run, "graph_run_id")
    assert run.graph_run_id is None


def test_orchestrator_run_to_dict_includes_squad_id():
    run = build_plan("criar post de viagem")
    d = run.to_dict()
    assert "squad_id" in d
    assert "graph_run_id" in d


def test_orchestrator_run_roundtrip_with_new_fields():
    run = build_plan("criar post de viagem", allow_unknown=True)
    run.squad_id = "squad_test123"
    run.graph_run_id = "grun_test456"
    d = run.to_dict()
    reloaded = OrchestratorRun.from_dict(d)
    assert reloaded.squad_id == "squad_test123"
    assert reloaded.graph_run_id == "grun_test456"


# ── build_graph_from_orchestrator ──────────────────────────────────

def test_build_graph_from_orchestrator_populates_squad_id():
    run = build_plan("criar post de viagem em natal")
    graph = build_graph_from_orchestrator(run)
    assert run.squad_id is not None
    assert run.squad_id.startswith("squad_")
    assert graph.squad_id == run.squad_id


def test_build_graph_from_orchestrator_returns_valid_graph():
    run = build_plan("criar post de viagem em natal")
    graph = build_graph_from_orchestrator(run)
    assert len(graph.nodes) > 0
    assert len(graph.edges) > 0
    assert len(graph.topological_order) > 0


# ── run_graph_from_orchestrator ────────────────────────────────────

def test_run_graph_from_orchestrator_returns_step_run():
    run = build_plan("criar post de viagem em natal")
    step_run = run_graph_from_orchestrator(run)
    assert step_run.status == "done"
    assert run.graph_run_id == step_run.graph_run_id


def test_run_graph_from_orchestrator_with_failure():
    """Fail the first step — use graph directly since step IDs are random UUIDs."""
    from src.execution_graph.runner import run_graph_dry

    run = build_plan("criar post de viagem em natal")
    graph = build_graph_from_orchestrator(run)
    step_run = run_graph_dry(graph, fail_at=graph.topological_order[0], include_snapshot=True)
    assert step_run.status == "failed"


# ── run_full_pipeline ──────────────────────────────────────────────

def test_run_full_pipeline_returns_both():
    orch_run, step_run = run_full_pipeline("criar post de viagem em natal")
    assert orch_run is not None
    assert step_run is not None


def test_run_full_pipeline_orchestrator_status():
    orch_run, step_run = run_full_pipeline("criar post de viagem em natal")
    assert orch_run.status in ("dry_run", "complete")


def test_run_full_pipeline_graph_status():
    orch_run, step_run = run_full_pipeline("criar post de viagem em natal")
    assert step_run.status == "done"


def test_run_full_pipeline_links_squad_id():
    orch_run, step_run = run_full_pipeline("criar post de viagem em natal")
    assert orch_run.squad_id is not None
    assert orch_run.squad_id.startswith("squad_")


def test_run_full_pipeline_links_graph_run_id():
    orch_run, step_run = run_full_pipeline("criar post de viagem em natal")
    assert orch_run.graph_run_id is not None
    assert orch_run.graph_run_id == step_run.graph_run_id


def test_run_full_pipeline_s06_done():
    orch_run, step_run = run_full_pipeline("criar post de viagem em natal")
    s06 = next(s for s in orch_run.steps if s.step_id == "s06")
    assert s06.status == "done"


def test_run_full_pipeline_s07_done():
    orch_run, step_run = run_full_pipeline("criar post de viagem em natal")
    s07 = next(s for s in orch_run.steps if s.step_id == "s07")
    assert s07.status == "done"


# ── Integration: orchestrator run includes all data ────────────────

def test_full_pipeline_to_dict_roundtrip():
    orch_run, step_run = run_full_pipeline("criar post de viagem em natal")
    d = orch_run.to_dict()
    assert d["squad_id"] is not None
    assert d["graph_run_id"] is not None
    assert d["status"] in ("dry_run", "complete")

    # Step run also roundtrips
    sd = step_run.to_dict()
    assert sd["status"] == "done"
    assert sd["graph_id"] is not None


# ── Multiple runs ──────────────────────────────────────────────────

def test_run_full_pipeline_multiple_requests():
    results = []
    for request in [
        "criar post de viagem",
        "fazer carrossel de praia",
        "campanha de marketing para pousada",
    ]:
        orch_run, step_run = run_full_pipeline(request)
        results.append((orch_run, step_run))
        assert orch_run.status in ("dry_run", "complete")
        assert step_run.status == "done"
    assert len(results) == 3


# ── Dry-run safety ─────────────────────────────────────────────────

def test_full_pipeline_is_dry_run_by_default():
    orch_run, step_run = run_full_pipeline("criar post de viagem em natal")
    # Dry-run means no real publishing, all faked
    assert step_run.status == "done"
    for entry in step_run.logs:
        assert "publicado" not in entry.message.lower() or "simulado" in entry.message.lower()


# ── Intent matching still works in full pipeline ───────────────────

def test_full_pipeline_detects_marketing_intent():
    orch_run, step_run = run_full_pipeline("criar carrossel campanha instagram")
    assert orch_run.sector_id == "marketing"


def test_full_pipeline_detects_sales_intent():
    orch_run, step_run = run_full_pipeline(
        "criar proposta de vendas e collab para hotel fazenda",
        allow_unknown=True,
    )
    assert orch_run.sector_id == "sales"


# ── Approval flows in full pipeline ────────────────────────────────

def test_full_pipeline_no_approval_for_low_risk():
    orch_run, step_run = run_full_pipeline("criar post carrossel instagram")
    assert orch_run.approval_required is False
    assert step_run.approval_required is False


def test_full_pipeline_approval_flag_for_medium_risk():
    orch_run, step_run = run_full_pipeline(
        "criar crm pipeline de leads com follow-up para hotel",
        allow_unknown=True,
    )
    # crm_pipeline capability = medium risk = approval required
    assert orch_run.approval_required is True
