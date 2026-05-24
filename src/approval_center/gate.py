"""Shared approval gate — primitive check used by both orchestrator and execution_graph.

Onda 8 Passo 5: unifica mission_orchestrator/approval_gate.py e
execution_graph/approval_bridge.py num módulo compartilhado.
"""
from __future__ import annotations

from pathlib import Path

from src.approval_center import store as store_mod
from src.approval_center.store import ApprovalStore
from src.approval_center.models import (
    APPROVAL_STATUS_APPROVED,
    APPROVAL_STATUS_REJECTED,
)

GATE_NOT_REQUIRED = "not_required"
GATE_APPROVED = "approved"
GATE_REJECTED = "rejected"
GATE_BLOCKED = "blocked_pending_approval"


def check_gate(
    approval_required: bool,
    approval_id: str | None = None,
    approvals_log: Path | None = None,
) -> str:
    """Primitive approval gate check — shared by orchestrator and execution_graph.

    Returns one of: "not_required", "approved", "rejected", "blocked_pending_approval".
    Does NOT create requests or modify state — pure read.
    """
    if not approval_required:
        return GATE_NOT_REQUIRED

    if approval_id is None:
        return GATE_BLOCKED

    log_path = approvals_log if approvals_log is not None else store_mod.DEFAULT_APPROVALS_LOG
    store = ApprovalStore(log_path)
    req = store.get(approval_id)

    if req is None:
        return GATE_BLOCKED

    if req.status == APPROVAL_STATUS_APPROVED:
        return GATE_APPROVED
    if req.status == APPROVAL_STATUS_REJECTED:
        return GATE_REJECTED
    return GATE_BLOCKED
