"""Tests for P9.3 — Approval-to-Execution Bridge."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from src.work_order.models import (
    OutputContract,
    OutputType,
    WorkOrder,
    WorkOrderStatus,
    make_work_order_id,
)
from src.work_order.approval_bridge import (
    GATE_APPROVED,
    GATE_BLOCKED,
    GATE_NOT_REQUIRED,
    GATE_REJECTED,
    approve_work_order,
    check_work_order_approval_gate,
    reject_work_order,
    request_work_order_approval,
)
from src.work_order.errors import WorkOrderStatusError
from src.approval_center.errors import ApprovalAlreadyResolvedError


def make_wo(**overrides) -> WorkOrder:
    kwargs = dict(
        work_order_id=make_work_order_id(),
        graph_step_id="step_abc",
        graph_run_id="grun_xyz",
        role="copywriter",
        step_label="Criar legenda",
        status=WorkOrderStatus.READY,
        contracts=[
            OutputContract("c01", OutputType.MARKDOWN, "Legenda", min_count=1),
        ],
    )
    kwargs.update(overrides)
    return WorkOrder(**kwargs)


@pytest.fixture
def tmp_approvals_log():
    d = tempfile.mkdtemp(prefix="p9_approvals_")
    p = Path(d) / "approvals.jsonl"
    yield p
    import shutil
    shutil.rmtree(d, ignore_errors=True)


class TestCheckApprovalGate:
    def test_not_required_when_no_approval_id_and_not_blocked(self):
        wo = make_wo(status=WorkOrderStatus.DRAFT)
        assert check_work_order_approval_gate(wo) == GATE_NOT_REQUIRED

    def test_blocked_when_approval_id_is_none_but_status_blocked(self):
        wo = make_wo(status=WorkOrderStatus.BLOCKED)
        assert check_work_order_approval_gate(wo) == GATE_BLOCKED

    def test_blocked_when_approval_not_found(self, tmp_approvals_log):
        wo = make_wo(approval_id="req_nonexistent")
        assert check_work_order_approval_gate(wo, approvals_log=tmp_approvals_log) == GATE_BLOCKED

    def test_approved_when_request_approved(self, tmp_approvals_log):
        wo = make_wo()
        req_id = request_work_order_approval(wo, approvals_log=tmp_approvals_log)
        approve_work_order(wo, approvals_log=tmp_approvals_log)
        assert check_work_order_approval_gate(wo, approvals_log=tmp_approvals_log) == GATE_APPROVED

    def test_rejected_when_request_rejected(self, tmp_approvals_log):
        wo = make_wo()
        req_id = request_work_order_approval(wo, approvals_log=tmp_approvals_log)
        reject_work_order(wo, "bad output", approvals_log=tmp_approvals_log)
        assert check_work_order_approval_gate(wo, approvals_log=tmp_approvals_log) == GATE_REJECTED

    def test_blocked_when_pending(self, tmp_approvals_log):
        wo = make_wo()
        request_work_order_approval(wo, approvals_log=tmp_approvals_log)
        assert check_work_order_approval_gate(wo, approvals_log=tmp_approvals_log) == GATE_BLOCKED


class TestRequestApproval:
    def test_creates_request_and_sets_approval_id(self, tmp_approvals_log):
        wo = make_wo()
        req_id = request_work_order_approval(wo, approvals_log=tmp_approvals_log)
        assert req_id.startswith("req_")
        assert wo.approval_id == req_id

    def test_transitions_ready_to_blocked(self, tmp_approvals_log):
        wo = make_wo(status=WorkOrderStatus.READY)
        request_work_order_approval(wo, approvals_log=tmp_approvals_log)
        assert wo.status == WorkOrderStatus.BLOCKED

    def test_persists_approval_request(self, tmp_approvals_log):
        wo = make_wo()
        req_id = request_work_order_approval(wo, approvals_log=tmp_approvals_log)

        from src.approval_center.store import ApprovalStore
        store = ApprovalStore(tmp_approvals_log)
        req = store.get(req_id)
        assert req is not None
        assert req.status == "pending"
        assert "Work Order" in req.subject

    def test_no_transition_if_already_blocked(self, tmp_approvals_log):
        wo = make_wo(status=WorkOrderStatus.BLOCKED)
        request_work_order_approval(wo, approvals_log=tmp_approvals_log)
        assert wo.status == WorkOrderStatus.BLOCKED

    def test_with_custom_risk_level(self, tmp_approvals_log):
        wo = make_wo()
        req_id = request_work_order_approval(wo, risk_level="high", approvals_log=tmp_approvals_log)

        from src.approval_center.store import ApprovalStore
        req = ApprovalStore(tmp_approvals_log).get(req_id)
        assert req.risk_level == "high"


class TestApproveWorkOrder:
    def test_approves_and_transitions_to_approved(self, tmp_approvals_log):
        wo = make_wo()
        request_work_order_approval(wo, approvals_log=tmp_approvals_log)
        result = approve_work_order(wo, note="LGTM", approvals_log=tmp_approvals_log)
        assert result.status == WorkOrderStatus.APPROVED

    def test_approve_updates_approval_store(self, tmp_approvals_log):
        wo = make_wo()
        req_id = request_work_order_approval(wo, approvals_log=tmp_approvals_log)
        approve_work_order(wo, approvals_log=tmp_approvals_log)

        from src.approval_center.store import ApprovalStore
        req = ApprovalStore(tmp_approvals_log).get(req_id)
        assert req.status == "approved"

    def test_raises_if_no_approval_id(self):
        wo = make_wo()
        with pytest.raises(WorkOrderStatusError, match="no linked approval"):
            approve_work_order(wo)

    def test_raises_if_already_approved(self, tmp_approvals_log):
        wo = make_wo()
        request_work_order_approval(wo, approvals_log=tmp_approvals_log)
        approve_work_order(wo, approvals_log=tmp_approvals_log)
        with pytest.raises(ApprovalAlreadyResolvedError):
            approve_work_order(wo, approvals_log=tmp_approvals_log)


class TestRejectWorkOrder:
    def test_rejects_and_transitions_to_rejected(self, tmp_approvals_log):
        wo = make_wo()
        request_work_order_approval(wo, approvals_log=tmp_approvals_log)
        result = reject_work_order(wo, note="Bad format", approvals_log=tmp_approvals_log)
        assert result.status == WorkOrderStatus.REJECTED

    def test_reject_updates_approval_store(self, tmp_approvals_log):
        wo = make_wo()
        req_id = request_work_order_approval(wo, approvals_log=tmp_approvals_log)
        reject_work_order(wo, note="incomplete", approvals_log=tmp_approvals_log)

        from src.approval_center.store import ApprovalStore
        req = ApprovalStore(tmp_approvals_log).get(req_id)
        assert req.status == "rejected"
        assert req.resolution_note == "incomplete"

    def test_raises_if_no_approval_id(self):
        wo = make_wo()
        with pytest.raises(WorkOrderStatusError, match="no linked approval"):
            reject_work_order(wo)

    def test_raises_if_already_rejected(self, tmp_approvals_log):
        wo = make_wo()
        request_work_order_approval(wo, approvals_log=tmp_approvals_log)
        reject_work_order(wo, approvals_log=tmp_approvals_log)
        with pytest.raises(ApprovalAlreadyResolvedError):
            reject_work_order(wo, approvals_log=tmp_approvals_log)


class TestE2EApprovalFlow:
    def test_full_approval_flow(self, tmp_approvals_log):
        """READY -> request -> BLOCKED -> approve -> APPROVED."""
        wo = make_wo(status=WorkOrderStatus.READY)
        assert wo.approval_id is None

        gate_before = check_work_order_approval_gate(wo, approvals_log=tmp_approvals_log)
        assert gate_before == GATE_NOT_REQUIRED

        req_id = request_work_order_approval(wo, approvals_log=tmp_approvals_log)
        assert wo.status == WorkOrderStatus.BLOCKED
        assert check_work_order_approval_gate(wo, approvals_log=tmp_approvals_log) == GATE_BLOCKED

        approve_work_order(wo, note="Approved!", approvals_log=tmp_approvals_log)
        assert wo.status == WorkOrderStatus.APPROVED
        assert check_work_order_approval_gate(wo, approvals_log=tmp_approvals_log) == GATE_APPROVED

    def test_full_rejection_flow(self, tmp_approvals_log):
        """READY -> request -> BLOCKED -> reject -> REJECTED."""
        wo = make_wo(status=WorkOrderStatus.READY)

        request_work_order_approval(wo, approvals_log=tmp_approvals_log)
        assert wo.status == WorkOrderStatus.BLOCKED

        reject_work_order(wo, note="Needs revision", approvals_log=tmp_approvals_log)
        assert wo.status == WorkOrderStatus.REJECTED
        assert check_work_order_approval_gate(wo, approvals_log=tmp_approvals_log) == GATE_REJECTED

    def test_multiple_work_orders_independent_approvals(self, tmp_approvals_log):
        """Two work orders get independent approval requests."""
        wo1 = make_wo()
        wo2 = make_wo()

        req1 = request_work_order_approval(wo1, approvals_log=tmp_approvals_log)
        req2 = request_work_order_approval(wo2, approvals_log=tmp_approvals_log)
        assert req1 != req2

        approve_work_order(wo1, approvals_log=tmp_approvals_log)
        reject_work_order(wo2, approvals_log=tmp_approvals_log)

        assert wo1.status == WorkOrderStatus.APPROVED
        assert wo2.status == WorkOrderStatus.REJECTED
