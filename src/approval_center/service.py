"""Approval Center service — request, approve, reject."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from src.approval_center.errors import ApprovalNotFoundError, ApprovalAlreadyResolvedError
from src.approval_center.models import (
    ApprovalRequest,
    APPROVAL_STATUS_PENDING,
    APPROVAL_STATUS_APPROVED,
    APPROVAL_STATUS_REJECTED,
)
from src.approval_center import store as store_mod
from src.approval_center.store import ApprovalStore

BASE = Path(__file__).resolve().parent.parent.parent
DEFAULT_APPROVALS_LOG = BASE / "data" / "approval_requests.jsonl"


def request_approval(
    subject: str,
    description: str = "",
    capability_id: str = "unknown",
    risk_level: str = "high",
    approvals_log=None,
) -> ApprovalRequest:
    log_path = approvals_log if approvals_log is not None else store_mod.DEFAULT_APPROVALS_LOG
    req = ApprovalRequest.new(
        subject=subject,
        description=description,
        capability_id=capability_id,
        risk_level=risk_level,
    )
    ApprovalStore(log_path).save(req)
    return req


def approve(request_id: str, note: str = "", approvals_log=None) -> ApprovalRequest:
    log_path = approvals_log if approvals_log is not None else store_mod.DEFAULT_APPROVALS_LOG
    store = ApprovalStore(log_path)
    existing = store.get(request_id)
    if existing is None:
        raise ApprovalNotFoundError(f"Request {request_id} not found")
    if existing.status != APPROVAL_STATUS_PENDING:
        raise ApprovalAlreadyResolvedError(
            f"Request {request_id} already resolved as {existing.status}"
        )
    updated = store.update_status(request_id, APPROVAL_STATUS_APPROVED, note=note)
    return updated


def reject(request_id: str, note: str = "", approvals_log=None) -> ApprovalRequest:
    log_path = approvals_log if approvals_log is not None else store_mod.DEFAULT_APPROVALS_LOG
    store = ApprovalStore(log_path)
    existing = store.get(request_id)
    if existing is None:
        raise ApprovalNotFoundError(f"Request {request_id} not found")
    if existing.status != APPROVAL_STATUS_PENDING:
        raise ApprovalAlreadyResolvedError(
            f"Request {request_id} already resolved as {existing.status}"
        )
    updated = store.update_status(request_id, APPROVAL_STATUS_REJECTED, note=note)
    return updated
