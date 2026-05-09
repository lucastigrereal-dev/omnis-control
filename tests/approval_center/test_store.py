"""Tests for approval store."""
import pytest
from src.approval_center.models import ApprovalRequest, APPROVAL_STATUS_APPROVED
from src.approval_center.store import ApprovalStore


def make_req(subject: str = "test subject") -> ApprovalRequest:
    return ApprovalRequest.new(subject, capability_id="campaign_package", risk_level="high")


def test_store_save_and_list(tmp_path):
    store = ApprovalStore(tmp_path / "approvals.jsonl")
    req = make_req()
    store.save(req)
    reqs = store.list_all()
    assert len(reqs) == 1
    assert reqs[0].request_id == req.request_id


def test_store_list_empty(tmp_path):
    store = ApprovalStore(tmp_path / "empty.jsonl")
    assert store.list_all() == []


def test_store_get_found(tmp_path):
    store = ApprovalStore(tmp_path / "approvals.jsonl")
    req = make_req()
    store.save(req)
    found = store.get(req.request_id)
    assert found is not None
    assert found.request_id == req.request_id


def test_store_get_not_found(tmp_path):
    store = ApprovalStore(tmp_path / "approvals.jsonl")
    assert store.get("req_ghost") is None


def test_store_update_status(tmp_path):
    store = ApprovalStore(tmp_path / "approvals.jsonl")
    req = make_req()
    store.save(req)
    updated = store.update_status(req.request_id, APPROVAL_STATUS_APPROVED, note="looks good")
    assert updated is not None
    assert updated.status == APPROVAL_STATUS_APPROVED
    assert updated.resolution_note == "looks good"
    assert updated.resolved_at is not None


def test_store_newest_first(tmp_path):
    store = ApprovalStore(tmp_path / "approvals.jsonl")
    r1 = make_req("first")
    r2 = make_req("second")
    store.save(r1)
    store.save(r2)
    reqs = store.list_all()
    assert reqs[0].request_id == r2.request_id


def test_store_filter_by_status(tmp_path):
    store = ApprovalStore(tmp_path / "approvals.jsonl")
    r1 = make_req("pending one")
    r2 = make_req("to approve")
    store.save(r1)
    store.save(r2)
    store.update_status(r2.request_id, APPROVAL_STATUS_APPROVED)
    pending = store.list_all(status="pending")
    assert len(pending) == 1
    assert pending[0].request_id == r1.request_id


def test_store_update_returns_latest(tmp_path):
    """update_status appends — get() should return the latest version."""
    store = ApprovalStore(tmp_path / "approvals.jsonl")
    req = make_req()
    store.save(req)
    store.update_status(req.request_id, APPROVAL_STATUS_APPROVED, note="ok")
    found = store.get(req.request_id)
    assert found.status == APPROVAL_STATUS_APPROVED
