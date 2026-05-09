"""Tests for P8.6 — E2E Mission → Squad → Graph → Approval."""
from __future__ import annotations

import json
import pytest

from src.mission_orchestrator.planner import build_plan
from src.mission_orchestrator.executor import execute
from src.execution_graph.mission_bridge import (
    build_graph_from_orchestrator,
    run_graph_from_orchestrator,
    run_full_pipeline,
)
from src.execution_graph.approval_bridge import (
    check_approval_gate,
    run_graph_with_approval_gate,
    GATE_BLOCKED,
    GATE_APPROVED,
    GATE_REJECTED,
    GATE_NOT_REQUIRED,
)
from src.approval_center.models import (
    APPROVAL_STATUS_PENDING,
    APPROVAL_STATUS_APPROVED,
    APPROVAL_STATUS_REJECTED,
)
from src.approval_center.service import request_approval, approve, reject


# ── Full Pipeline: Low Risk (No Approval) ──────────────────────────

def test_e2e_low_risk_full_flow():
    """Request → Orchestrator → Squad → Graph (no approval needed)."""
    orch_run, step_run = run_full_pipeline("criar post de viagem em natal")
    assert orch_run.status in ("dry_run", "complete")
    assert orch_run.approval_required is False
    assert step_run.status == "done"
    assert orch_run.squad_id is not None
    assert orch_run.graph_run_id is not None
    assert step_run.approval_required is False


# ── Full Pipeline: Medium Risk with Manual Approval ─────────────────

def test_e2e_medium_risk_approval_lifecycle():
    """Full lifecycle: request → get blocked → approve → run → done."""
    from src.squad_composer.composer import compose_squad
    from src.task_decomposer.decomposer import decompose_squad
    from src.execution_graph.builder import build_graph

    request_text = "criar proposta de vendas e collab para hotel fazenda"
    squad = compose_squad(request_text)
    assert squad.approval_required is True
    assert squad.risk_level == "medium"

    task_plan = decompose_squad(squad)
    graph = build_graph(squad, task_plan)

    # Step 1: Run gated — should block
    step_run = run_graph_with_approval_gate(graph, squad_plan=squad)
    assert step_run.status == "blocked_pending_approval"
    assert step_run.approval_required is True
    assert step_run.approval_id is not None
    approval_id = step_run.approval_id

    # Step 2: Approve the request
    approved = approve(approval_id, note="Lucas approved via test")
    assert approved.status == APPROVAL_STATUS_APPROVED

    # Step 3: Run again with approved ID — should execute
    step_run2 = run_graph_with_approval_gate(
        graph,
        squad_plan=squad,
        approval_id=approval_id,
    )
    assert step_run2.status == "done"
    assert step_run2.approval_id == approval_id


def test_e2e_medium_risk_rejected_stays_blocked():
    """Run gets blocked, gets rejected, replay stays blocked."""
    from src.squad_composer.composer import compose_squad
    from src.task_decomposer.decomposer import decompose_squad
    from src.execution_graph.builder import build_graph

    request_text = "criar proposta de vendas e collab para resort"
    squad = compose_squad(request_text)
    task_plan = decompose_squad(squad)
    graph = build_graph(squad, task_plan)

    step_run = run_graph_with_approval_gate(graph, squad_plan=squad)
    approval_id = step_run.approval_id

    # Reject
    rejected = reject(approval_id, note="Rejected by operator")
    assert rejected.status == APPROVAL_STATUS_REJECTED

    # Run again — should stay blocked
    step_run2 = run_graph_with_approval_gate(
        graph, squad_plan=squad, approval_id=approval_id
    )
    assert step_run2.status == "blocked_pending_approval"


# ── Full Pipeline with Orchestrator Run ────────────────────────────

def test_e2e_orchestrator_full_approval_flow():
    """Orchestrator detects approval_required → execute creates approval."""
    from src.mission_orchestrator import service as svc
    from src.mission_orchestrator.executor import (
        execute,
        RUN_STATUS_BLOCKED_APPROVAL,
    )

    orch_run = build_plan(
        "criar crm pipeline de leads com follow-up para pousada",
        allow_unknown=True,
    )
    assert orch_run.approval_required is True

    # Execute without approval → should block with auto-created request
    orch_run = execute(orch_run)
    assert orch_run.status == RUN_STATUS_BLOCKED_APPROVAL
    assert orch_run.approval_id is not None


def test_e2e_orchestrator_approve_then_run():
    """Blocked orchestrator → approve → re-run succeeds."""
    from src.mission_orchestrator import service as svc
    from src.mission_orchestrator.models import OrchestratorRun

    orch_run = build_plan(
        "criar crm pipeline leads follow-up para resort",
        allow_unknown=True,
    )
    orch_run = execute(orch_run)

    approval_id = orch_run.approval_id
    assert approval_id is not None

    # Approve
    approve(approval_id, note="Operator approved")

    # Re-run with approved ID
    orch_run2 = build_plan(
        "criar crm pipeline leads follow-up para resort",
        allow_unknown=True,
    )
    orch_run2.approval_id = approval_id
    orch_run2 = execute(orch_run2)
    assert orch_run2.status in ("dry_run", "complete")
    assert orch_run2.mission_id is not None


# ── Full Pipeline + Graph Bridge ───────────────────────────────────

def test_e2e_full_pipeline_with_approval_bridge():
    """Orchestrator run → blocked → approve → graph resume."""
    from src.mission_orchestrator import service as svc
    from src.mission_orchestrator.models import OrchestratorRun

    orch_run = build_plan(
        "criar crm pipeline leads follow-up para resort fazenda",
        allow_unknown=True,
    )
    orch_run = execute(orch_run)

    assert orch_run.status == "blocked_pending_approval"
    assert orch_run.approval_id is not None
    approval_id = orch_run.approval_id

    # Approve
    approve(approval_id, note="Approved for E2E test")

    # Now run full pipeline with the approved ID
    orch_run2, step_run = run_full_pipeline(
        "criar crm pipeline leads follow-up para resort fazenda",
        allow_unknown=True,
        approval_id=approval_id,
    )
    assert orch_run2.status in ("dry_run", "complete")
    assert step_run is not None
    assert step_run.status == "done"
    assert orch_run2.squad_id is not None


# ── Multi-account scenarios ────────────────────────────────────────

def test_e2e_different_account_handles():
    """Same request, different accounts — all succeed."""
    for handle in ["oinatalrn", "afamiliatigrereal", "oquecomernatalrn"]:
        orch_run, step_run = run_full_pipeline(
            "criar post de viagem",
            account_handle=handle,
        )
        assert orch_run.account_handle == handle
        assert orch_run.status in ("dry_run", "complete")
        assert step_run.status == "done"


# ── High risk: full block → approve → run ──────────────────────────

def test_e2e_high_risk_full_lifecycle():
    """High risk request: block → approve → run → verify."""
    from src.squad_composer.composer import compose_squad
    from src.task_decomposer.decomposer import decompose_squad
    from src.execution_graph.builder import build_graph

    request_text = "criar app sistema api dashboard para hotel"
    squad = compose_squad(request_text)
    assert squad.risk_level == "high"
    assert squad.approval_required is True

    task_plan = decompose_squad(squad)
    graph = build_graph(squad, task_plan)

    # Block
    step_run = run_graph_with_approval_gate(graph, squad_plan=squad)
    assert step_run.status == "blocked_pending_approval"
    approval_id = step_run.approval_id

    # Approve
    approve(approval_id)

    # Run
    step_run2 = run_graph_with_approval_gate(
        graph, squad_plan=squad, approval_id=approval_id
    )
    assert step_run2.status == "done"


# ── Serialization / Round-trip ─────────────────────────────────────

def test_e2e_full_output_json_roundtrip():
    """OrchestratorRun + StepRun → JSON → validate all fields."""
    orch_run, step_run = run_full_pipeline("criar post de viagem em natal")

    orch_dict = orch_run.to_dict()
    step_dict = step_run.to_dict()

    # Orchestrator fields
    assert "run_id" in orch_dict
    assert "request_text" in orch_dict
    assert "status" in orch_dict
    assert "squad_id" in orch_dict
    assert "graph_run_id" in orch_dict
    assert "approval_required" in orch_dict
    assert "steps" in orch_dict
    assert len(orch_dict["steps"]) == 7

    # StepRun fields
    assert "graph_run_id" in step_dict
    assert "status" in step_dict
    assert "step_states" in step_dict
    assert "logs" in step_dict
    assert "approval_required" in step_dict
    assert step_dict["approval_required"] is False


# ── Event log bridge in E2E ────────────────────────────────────────

def test_e2e_pipeline_to_event_log():
    """Full pipeline run → convert to event log → compute metrics."""
    from src.execution_graph.events import event_log_from_step_run
    from src.execution_graph.metrics import compute_run_metrics

    orch_run, step_run = run_full_pipeline("criar post de viagem em natal")
    event_log = event_log_from_step_run(step_run)
    metrics = compute_run_metrics(event_log)

    assert metrics.total_steps > 0
    assert metrics.steps_done > 0
    assert metrics.success_rate == 1.0


# ── Dry-run safety (no side effects) ───────────────────────────────

def test_e2e_no_side_effects():
    """Running full pipeline 10 times produces no duplicate data issues."""
    results = []
    for _ in range(3):
        orch_run, step_run = run_full_pipeline("criar post de viagem em natal")
        results.append((orch_run.run_id, step_run.graph_run_id))

    # All runs have unique IDs
    run_ids = {r[0] for r in results}
    graph_ids = {r[1] for r in results}
    assert len(run_ids) == 3
    assert len(graph_ids) == 3


# ── Unknown intent edge case ───────────────────────────────────────

def test_e2e_unknown_intent_with_allow():
    """Unknown intent + allow_unknown should still succeed."""
    orch_run, step_run = run_full_pipeline(
        "fazer algo que nao existe no sistema xyz",
        allow_unknown=True,
    )
    assert orch_run.intent == "unknown"
    # Pipeline should still complete (no crash)
    if step_run is not None:
        assert step_run.status == "done"


# ── CLI integration smoke ──────────────────────────────────────────

def test_cli_run_full_works():
    """CLI run-full command exits 0."""
    import subprocess
    import sys
    import os

    cwd = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

    result = subprocess.run(
        [
            sys.executable, "jarvis.py", "orchestrator", "run-full",
            "criar post de viagem em natal", "--json",
        ],
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=30,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    data = json.loads(result.stdout)
    assert "orchestrator" in data
    assert "graph" in data
    assert data["orchestrator"]["status"] in ("dry_run", "complete")
    assert data["graph"]["status"] == "done"


def test_cli_run_full_blocked():
    """CLI run-full with --json returns blocked status for high risk without approval."""
    import subprocess
    import sys
    import os

    cwd = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

    result = subprocess.run(
        [
            sys.executable, "jarvis.py", "orchestrator", "run-full",
            "criar app sistema api dashboard para hotel",
            "--json",
        ],
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=30,
    )
    # --json path returns 0 even for blocked; validate via JSON payload
    assert result.returncode == 0, f"stderr: {result.stderr}"
    data = json.loads(result.stdout)
    assert data["graph"] is None
    assert data["orchestrator"]["status"] == "blocked_pending_approval"
    assert len(data["orchestrator"]["blockers"]) > 0
