"""Tests for Approval-Integrated Graph Run — P8.3."""
from __future__ import annotations

import json
import pytest

from src.execution_graph.models import (
    ExecutionGraph,
    StepNode,
    StepStatus,
    StepRun,
    RUN_STATUS_BLOCKED,
)
from src.execution_graph.approval_bridge import (
    check_approval_gate,
    request_graph_approval,
    run_graph_with_approval_gate,
    GATE_BLOCKED,
    GATE_APPROVED,
    GATE_REJECTED,
    GATE_NOT_REQUIRED,
)
from src.execution_graph.runner import run_graph_dry
from src.execution_graph.store import DEFAULT_STORE_ROOT
from src.approval_center.models import (
    ApprovalRequest,
    APPROVAL_STATUS_PENDING,
    APPROVAL_STATUS_APPROVED,
    APPROVAL_STATUS_REJECTED,
)
from src.approval_center.store import ApprovalStore
from src.squad_composer.composer import compose_squad
from src.task_decomposer.decomposer import decompose_squad
from src.execution_graph.builder import build_graph


# ── Fixtures ───────────────────────────────────────────────────────

@pytest.fixture
def approvals_log(tmp_path):
    return tmp_path / "approvals.jsonl"


@pytest.fixture
def store(approvals_log):
    return ApprovalStore(approvals_log)


@pytest.fixture
def sample_graph():
    squad = compose_squad("criar post de viagem em natal")
    task_plan = decompose_squad(squad)
    return build_graph(squad, task_plan)


# ── Unit: check_approval_gate ──────────────────────────────────────

def test_gate_not_required_when_approval_not_required(approvals_log):
    result = check_approval_gate(False, None, approvals_log)
    assert result == GATE_NOT_REQUIRED


def test_gate_blocked_when_no_approval_id(approvals_log):
    result = check_approval_gate(True, None, approvals_log)
    assert result == GATE_BLOCKED


def test_gate_blocked_when_approval_not_found(approvals_log):
    result = check_approval_gate(True, "req_fake123", approvals_log)
    assert result == GATE_BLOCKED


def test_gate_blocked_when_pending(store, approvals_log):
    req = ApprovalRequest.new("test", risk_level="medium")
    store.save(req)
    result = check_approval_gate(True, req.request_id, approvals_log)
    assert result == GATE_BLOCKED


def test_gate_approved(store, approvals_log):
    req = ApprovalRequest.new("test", risk_level="medium")
    store.save(req)
    store.update_status(req.request_id, APPROVAL_STATUS_APPROVED, "ok")
    result = check_approval_gate(True, req.request_id, approvals_log)
    assert result == GATE_APPROVED


def test_gate_rejected(store, approvals_log):
    req = ApprovalRequest.new("test", risk_level="medium")
    store.save(req)
    store.update_status(req.request_id, APPROVAL_STATUS_REJECTED, "no")
    result = check_approval_gate(True, req.request_id, approvals_log)
    assert result == GATE_REJECTED


# ── Unit: request_graph_approval ───────────────────────────────────

def test_request_graph_approval_creates_request(sample_graph, approvals_log):
    req_id = request_graph_approval(sample_graph, "medium", approvals_log)
    assert req_id.startswith("req_")

    store = ApprovalStore(approvals_log)
    req = store.get(req_id)
    assert req is not None
    assert req.status == APPROVAL_STATUS_PENDING
    assert sample_graph.request[:30] in req.subject


# ── Unit: StepRun.blocked factory ──────────────────────────────────

def test_step_run_blocked_structure(sample_graph):
    sr = StepRun.blocked(sample_graph, reason="test block", approval_id="req_abc", approval_required=True)
    assert sr.status == RUN_STATUS_BLOCKED
    assert sr.approval_id == "req_abc"
    assert sr.approval_required is True
    assert sr.step_states == {}
    assert len(sr.logs) == 1
    assert sr.logs[0].message == "test block"


def test_step_run_blocked_serialization(sample_graph):
    sr = StepRun.blocked(sample_graph, reason="test", approval_id="req_xyz")
    d = sr.to_dict()
    assert d["status"] == RUN_STATUS_BLOCKED
    assert d["approval_id"] == "req_xyz"
    assert d["approval_required"] is False
    assert d["graph_snapshot"] is not None


# ── Unit: approval fields on StepRun ───────────────────────────────

def test_step_run_serialization_includes_approval_fields(sample_graph):
    sr = run_graph_dry(sample_graph, include_snapshot=True, approval_id="req_123", approval_required=True)
    d = sr.to_dict()
    assert d["approval_id"] == "req_123"
    assert d["approval_required"] is True


def test_step_run_default_approval_fields(sample_graph):
    sr = run_graph_dry(sample_graph)
    assert sr.approval_id is None
    assert sr.approval_required is False


# ── Integration: run_graph_with_approval_gate ──────────────────────

def test_run_gated_bypasses_for_low_risk(sample_graph):
    """Low risk squad → approval not required → runs normally."""
    squad = compose_squad("criar post simples")
    task_plan = decompose_squad(squad)
    graph = build_graph(squad, task_plan)

    result = run_graph_with_approval_gate(graph, squad_plan=squad)
    assert result.status == "done"
    assert result.approval_id is None
    assert result.approval_required is False
    assert len(result.step_states) > 0


def test_run_gated_blocks_for_medium_risk_no_approval(sample_graph, approvals_log):
    """Medium risk → blocked, auto-creates approval request."""
    squad = compose_squad("criar proposta de vendas e collab para hotel fazenda")
    task_plan = decompose_squad(squad)
    graph = build_graph(squad, task_plan)

    result = run_graph_with_approval_gate(graph, squad_plan=squad, approvals_log=approvals_log)
    assert result.status == RUN_STATUS_BLOCKED
    assert result.approval_id is not None
    assert result.approval_required is True
    assert result.approval_id.startswith("req_")

    # Verify approval was created in the store
    store = ApprovalStore(approvals_log)
    req = store.get(result.approval_id)
    assert req is not None
    assert req.status == APPROVAL_STATUS_PENDING


def test_run_gated_runs_with_approved_request(sample_graph, approvals_log):
    """Medium risk with approved request → runs normally."""
    squad = compose_squad("criar proposta de vendas e collab para hotel fazenda")
    task_plan = decompose_squad(squad)
    graph = build_graph(squad, task_plan)

    # Create and approve
    req_id = request_graph_approval(graph, squad.risk_level, approvals_log)
    store = ApprovalStore(approvals_log)
    store.update_status(req_id, APPROVAL_STATUS_APPROVED, "go ahead")

    result = run_graph_with_approval_gate(graph, squad_plan=squad, approval_id=req_id, approvals_log=approvals_log)
    assert result.status == "done"
    assert result.approval_id == req_id
    assert result.approval_required is True
    assert len(result.step_states) > 0


def test_run_gated_blocks_for_rejected_request(sample_graph, approvals_log):
    """Medium risk with rejected request → blocked."""
    squad = compose_squad("criar proposta de vendas e collab para hotel fazenda")
    task_plan = decompose_squad(squad)
    graph = build_graph(squad, task_plan)

    # Create and reject
    req_id = request_graph_approval(graph, squad.risk_level, approvals_log)
    store = ApprovalStore(approvals_log)
    store.update_status(req_id, APPROVAL_STATUS_REJECTED, "not now")

    result = run_graph_with_approval_gate(graph, squad_plan=squad, approval_id=req_id, approvals_log=approvals_log)
    assert result.status == RUN_STATUS_BLOCKED
    assert result.approval_id == req_id
    assert result.approval_required is True
    assert "rejected" in result.logs[0].message.lower()


def test_run_gated_high_risk_auto_creates_approval(sample_graph, approvals_log):
    """High risk without approval → blocked + auto-create."""
    squad = compose_squad("criar dashboard e sistema de api para hotel")
    task_plan = decompose_squad(squad)
    graph = build_graph(squad, task_plan)

    result = run_graph_with_approval_gate(graph, squad_plan=squad, approvals_log=approvals_log)
    assert result.status == RUN_STATUS_BLOCKED
    assert result.approval_id is not None
    assert "jarvis approvals-center approve" in result.logs[0].message


def test_run_gated_failure_injection_still_checks_gate(sample_graph, approvals_log):
    """Failure injection only applies after gate passes."""
    squad = compose_squad("criar proposta de vendas e collab para hotel fazenda")
    task_plan = decompose_squad(squad)
    graph = build_graph(squad, task_plan)

    # Approve first
    req_id = request_graph_approval(graph, squad.risk_level, approvals_log)
    store = ApprovalStore(approvals_log)
    store.update_status(req_id, APPROVAL_STATUS_APPROVED, "ok")

    fail_step = graph.topological_order[0]
    result = run_graph_with_approval_gate(
        graph, squad_plan=squad, approval_id=req_id,
        approvals_log=approvals_log, fail_at=fail_step,
    )
    assert result.status == "failed"
    assert result.step_states[fail_step] == "failed"


# ── CLI smoke ──────────────────────────────────────────────────────

def test_cli_graph_run_gated_json(tmp_path, approvals_log, monkeypatch):
    import subprocess, sys, os

    # Use a low-risk request that bypasses gate so it runs deterministically
    r = subprocess.run(
        [sys.executable, "jarvis.py", "graph", "run-gated",
         "fazer post de viagem simples", "--json"],
        capture_output=True, text=True, timeout=30,
        cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    )
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert "graph_run_id" in data
    assert "status" in data
    assert "approval_id" in data
    assert "approval_required" in data


def test_cli_graph_run_gated_blocked():
    import subprocess, sys, os

    r = subprocess.run(
        [sys.executable, "jarvis.py", "graph", "run-gated",
         "criar proposta de vendas e collab para hotel fazenda"],
        capture_output=True, text=True, timeout=30,
        cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    )
    assert r.returncode == 0
    assert "blocked" in r.stdout.lower() or "BLOCKED" in r.stdout


def test_cli_graph_run_gated_with_existing_approval(tmp_path):
    import subprocess, sys, os

    cwd = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

    # First create an approval request
    r1 = subprocess.run(
        [sys.executable, "jarvis.py", "approvals-center", "request",
         "test graph approval", "--json"],
        capture_output=True, text=True, timeout=30, cwd=cwd,
    )
    data1 = json.loads(r1.stdout)
    req_id = data1["request_id"]

    # Approve it
    subprocess.run(
        [sys.executable, "jarvis.py", "approvals-center", "approve", req_id],
        capture_output=True, text=True, timeout=30, cwd=cwd,
    )

    # Run gated with the approval ID
    r3 = subprocess.run(
        [sys.executable, "jarvis.py", "graph", "run-gated",
         "criar proposta de vendas e collab para hotel fazenda",
         "--approval-id", req_id, "--json"],
        capture_output=True, text=True, timeout=30, cwd=cwd,
    )
    data3 = json.loads(r3.stdout)
    # Should bypass gate with approved request
    assert data3["status"] == "done"
    assert data3["approval_id"] == req_id
