"""Testes do gate compartilhado (Onda 8 Passo 5).

Verifica que approval_center/gate.py é a fonte canônica e que ambos
os adaptadores (orchestrator + execution_graph) delegam pra ele.
"""
from __future__ import annotations

import pytest

from src.approval_center.gate import (
    check_gate,
    GATE_NOT_REQUIRED,
    GATE_APPROVED,
    GATE_REJECTED,
    GATE_BLOCKED,
)


# ── check_gate (primitiva) ────────────────────────────────────────────────────

def test_gate_not_required_when_approval_false():
    assert check_gate(approval_required=False) == GATE_NOT_REQUIRED


def test_gate_blocked_when_required_no_id():
    assert check_gate(approval_required=True, approval_id=None) == GATE_BLOCKED


def test_gate_blocked_when_id_not_in_store(tmp_path):
    log = tmp_path / "approvals.jsonl"
    result = check_gate(
        approval_required=True,
        approval_id="nonexistent-id",
        approvals_log=log,
    )
    assert result == GATE_BLOCKED


def test_gate_approved_when_store_has_approved(tmp_path):
    from src.approval_center.service import request_approval, approve
    log = tmp_path / "approvals.jsonl"
    req = request_approval(
        subject="test", description="test", capability_id="cap1",
        risk_level="low", approvals_log=log,
    )
    approve(req.request_id, approvals_log=log)
    result = check_gate(
        approval_required=True,
        approval_id=req.request_id,
        approvals_log=log,
    )
    assert result == GATE_APPROVED


def test_gate_rejected_when_store_has_rejected(tmp_path):
    from src.approval_center.service import request_approval, reject
    log = tmp_path / "approvals.jsonl"
    req = request_approval(
        subject="test", description="test", capability_id="cap1",
        risk_level="low", approvals_log=log,
    )
    reject(req.request_id, approvals_log=log)
    result = check_gate(
        approval_required=True,
        approval_id=req.request_id,
        approvals_log=log,
    )
    assert result == GATE_REJECTED


# ── orchestrator approval_gate delegates to shared gate ──────────────────────

def test_orchestrator_gate_delegates_not_required():
    from src.mission_orchestrator.approval_gate import check_approval_gate
    from src.mission_orchestrator.models import OrchestratorRun

    run = OrchestratorRun.new(request_text="test")
    run.approval_required = False
    assert check_approval_gate(run) == GATE_NOT_REQUIRED


def test_orchestrator_gate_delegates_blocked():
    from src.mission_orchestrator.approval_gate import check_approval_gate
    from src.mission_orchestrator.models import OrchestratorRun

    run = OrchestratorRun.new(request_text="test")
    run.approval_required = True
    run.approval_id = None
    assert check_approval_gate(run) == GATE_BLOCKED


# ── execution_graph approval_bridge delegates to shared gate ─────────────────

def test_graph_bridge_delegates_not_required():
    from src.execution_graph.approval_bridge import check_approval_gate

    assert check_approval_gate(approval_required=False) == GATE_NOT_REQUIRED


def test_graph_bridge_delegates_blocked_no_id():
    from src.execution_graph.approval_bridge import check_approval_gate

    assert check_approval_gate(approval_required=True, approval_id=None) == GATE_BLOCKED


def test_graph_bridge_delegates_blocked_bad_id(tmp_path):
    from src.execution_graph.approval_bridge import check_approval_gate

    log = tmp_path / "approvals.jsonl"
    result = check_approval_gate(
        approval_required=True,
        approval_id="bad-id",
        approvals_log=log,
    )
    assert result == GATE_BLOCKED
