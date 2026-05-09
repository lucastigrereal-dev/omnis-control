"""P5.1 — Approval Enforcement Hook tests."""
import pytest
from src.mission_orchestrator.planner import build_plan
from src.mission_orchestrator.executor import execute, RUN_STATUS_BLOCKED_APPROVAL
from src.mission_orchestrator.approval_gate import (
    check_approval_gate, create_approval_request,
    GATE_NOT_REQUIRED, GATE_APPROVED, GATE_REJECTED, GATE_BLOCKED,
)
from src.mission_orchestrator.models import RUN_STATUS_DRY_RUN, RUN_STATUS_BLOCKED
from src.approval_center import service as svc_mod
from src.approval_center import store as store_mod


def make_high_risk_run():
    return build_plan("cria app sistema api software", allow_unknown=True)


def make_low_risk_run():
    return build_plan("carrossel campanha instagram")


def test_high_risk_blocks_without_approval(tmp_path):
    run = make_high_risk_run()
    assert run.approval_required is True
    result = execute(run, approvals_log=tmp_path / "approvals.jsonl")
    assert result.status == RUN_STATUS_BLOCKED_APPROVAL
    assert len(result.blockers) >= 1


def test_high_risk_auto_creates_approval_request(tmp_path):
    run = make_high_risk_run()
    result = execute(run, approvals_log=tmp_path / "approvals.jsonl")
    assert result.approval_id is not None
    assert result.approval_id.startswith("req_")
    # Approval request should be persisted
    store = __import__("src.approval_center.store", fromlist=["ApprovalStore"]).ApprovalStore(
        tmp_path / "approvals.jsonl"
    )
    req = store.get(result.approval_id)
    assert req is not None
    assert req.status == "pending"


def test_approved_approval_allows_dry_run(tmp_path):
    run = make_high_risk_run()
    # First execute — auto-creates approval
    result = execute(run, approvals_log=tmp_path / "approvals.jsonl")
    assert result.status == RUN_STATUS_BLOCKED_APPROVAL
    approval_id = result.approval_id

    # Approve it
    svc_mod.approve(approval_id, note="cleared", approvals_log=tmp_path / "approvals.jsonl")

    # Second execute with approval_id set — should pass gate
    result.approval_id = approval_id
    result2 = execute(result, approvals_log=tmp_path / "approvals.jsonl")
    assert result2.status == RUN_STATUS_DRY_RUN


def test_rejected_approval_blocks_run(tmp_path):
    run = make_high_risk_run()
    result = execute(run, approvals_log=tmp_path / "approvals.jsonl")
    approval_id = result.approval_id

    # Reject it
    svc_mod.reject(approval_id, note="too risky", approvals_log=tmp_path / "approvals.jsonl")

    result.approval_id = approval_id
    result2 = execute(result, approvals_log=tmp_path / "approvals.jsonl")
    assert result2.status == RUN_STATUS_BLOCKED


def test_low_risk_runs_without_approval(tmp_path):
    run = make_low_risk_run()
    assert run.approval_required is False
    result = execute(run, approvals_log=tmp_path / "approvals.jsonl")
    assert result.status == RUN_STATUS_DRY_RUN


def test_gate_not_required_for_low_risk():
    run = make_low_risk_run()
    gate = check_approval_gate(run)
    assert gate == GATE_NOT_REQUIRED


def test_gate_blocked_when_no_approval_id():
    run = make_high_risk_run()
    gate = check_approval_gate(run)
    assert gate == GATE_BLOCKED


def test_gate_approved_after_approval(tmp_path):
    run = make_high_risk_run()
    req_id = create_approval_request(run, approvals_log=tmp_path / "approvals.jsonl")
    run.approval_id = req_id
    svc_mod.approve(req_id, approvals_log=tmp_path / "approvals.jsonl")
    gate = check_approval_gate(run, approvals_log=tmp_path / "approvals.jsonl")
    assert gate == GATE_APPROVED


def test_no_real_execution_in_blocked_run(tmp_path):
    run = make_high_risk_run()
    result = execute(run, approvals_log=tmp_path / "approvals.jsonl")
    # mission_id should not be set — s02 was never executed
    assert result.mission_id is None
