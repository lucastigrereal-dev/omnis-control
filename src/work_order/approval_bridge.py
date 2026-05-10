"""Approval Bridge — conecta work orders ao approval_center."""
from __future__ import annotations

from pathlib import Path

from src.work_order.models import WorkOrder, WorkOrderStatus
from src.approval_center import store as approval_store_mod
from src.approval_center.store import ApprovalStore
from src.approval_center.models import (
    APPROVAL_STATUS_PENDING,
    APPROVAL_STATUS_APPROVED,
    APPROVAL_STATUS_REJECTED,
)

GATE_BLOCKED = "blocked_pending_approval"
GATE_APPROVED = "approved"
GATE_REJECTED = "rejected"
GATE_NOT_REQUIRED = "not_required"


def check_work_order_approval_gate(
    wo: WorkOrder,
    approvals_log=None,
) -> str:
    """Check approval gate status for a work order.

    Returns one of: "not_required", "approved", "rejected", "blocked_pending_approval".
    """
    if wo.approval_id is None:
        return GATE_NOT_REQUIRED if wo.status != WorkOrderStatus.BLOCKED else GATE_BLOCKED

    log_path = approvals_log if approvals_log is not None else approval_store_mod.DEFAULT_APPROVALS_LOG
    store = ApprovalStore(log_path)
    req = store.get(wo.approval_id)

    if req is None:
        return GATE_BLOCKED

    if req.status == APPROVAL_STATUS_APPROVED:
        return GATE_APPROVED
    if req.status == APPROVAL_STATUS_REJECTED:
        return GATE_REJECTED
    return GATE_BLOCKED


def request_work_order_approval(
    wo: WorkOrder,
    risk_level: str = "medium",
    approvals_log=None,
) -> str:
    """Create an approval request for a work order. Returns the request_id."""
    from src.approval_center.service import request_approval

    log_path = approvals_log if approvals_log is not None else approval_store_mod.DEFAULT_APPROVALS_LOG

    req = request_approval(
        subject=f"Work Order: {wo.step_label[:80]}",
        description=f"wo_id={wo.work_order_id} | role={wo.role} | graph_step={wo.graph_step_id}",
        capability_id=wo.work_order_id,
        risk_level=risk_level,
        approvals_log=log_path,
    )
    wo.approval_id = req.request_id

    if wo.can_transition_to(WorkOrderStatus.BLOCKED):
        wo.transition_to(WorkOrderStatus.BLOCKED)

    return req.request_id


def approve_work_order(
    wo: WorkOrder,
    note: str = "",
    approvals_log=None,
) -> WorkOrder:
    """Approve the linked approval request and transition BLOCKED -> APPROVED."""
    from src.approval_center.service import approve
    from src.work_order.errors import WorkOrderStatusError

    if not wo.approval_id:
        raise WorkOrderStatusError(
            f"Work order {wo.work_order_id} has no linked approval request"
        )

    log_path = approvals_log if approvals_log is not None else approval_store_mod.DEFAULT_APPROVALS_LOG
    approve(wo.approval_id, note=note, approvals_log=log_path)
    wo.transition_to(WorkOrderStatus.APPROVED)
    return wo


def reject_work_order(
    wo: WorkOrder,
    note: str = "",
    approvals_log=None,
) -> WorkOrder:
    """Reject the linked approval request and transition BLOCKED -> REJECTED."""
    from src.approval_center.service import reject
    from src.work_order.errors import WorkOrderStatusError

    if not wo.approval_id:
        raise WorkOrderStatusError(
            f"Work order {wo.work_order_id} has no linked approval request"
        )

    log_path = approvals_log if approvals_log is not None else approval_store_mod.DEFAULT_APPROVALS_LOG
    reject(wo.approval_id, note=note, approvals_log=log_path)
    wo.transition_to(WorkOrderStatus.REJECTED)
    return wo
