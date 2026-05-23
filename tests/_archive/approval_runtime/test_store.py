import json
import pytest

from src.approval_runtime.store import ApprovalStore
from src.approval_runtime.models import (
    ApprovalRequest,
    ApprovalStatus,
    RiskLevel,
)
from src.approval_runtime.errors import AlreadyDecidedError


class TestApprovalStore:
    def test_save_and_list_pending(self):
        store = ApprovalStore()
        req = ApprovalRequest(action="test")
        store.save_request(req)
        pending = store.pending()
        assert len(pending) == 1
        assert pending[0].action == "test"

    def test_get_pending_by_id(self):
        store = ApprovalStore()
        req = ApprovalRequest(action="get_me")
        store.save_request(req)
        fetched = store.get_pending(req.request_id)
        assert fetched is not None
        assert fetched.action == "get_me"

    def test_get_pending_missing(self):
        store = ApprovalStore()
        assert store.get_pending("nonexistent") is None

    def test_approve_removes_from_pending(self):
        store = ApprovalStore()
        req = ApprovalRequest(action="approve_me")
        store.save_request(req)
        decision = store.approve(req.request_id, "lucas")
        assert decision.status == ApprovalStatus.APPROVED
        assert decision.decided_by == "lucas"
        assert store.pending() == []

    def test_reject_removes_from_pending(self):
        store = ApprovalStore()
        req = ApprovalRequest(action="reject_me")
        store.save_request(req)
        decision = store.reject(req.request_id, "too risky", "lucas")
        assert decision.status == ApprovalStatus.REJECTED
        assert decision.message == "too risky"

    def test_cannot_approve_twice(self):
        store = ApprovalStore()
        req = ApprovalRequest(action="once")
        store.save_request(req)
        store.approve(req.request_id)
        with pytest.raises(AlreadyDecidedError):
            store.approve(req.request_id)

    def test_persist_to_file(self, tmp_path):
        path = tmp_path / "approvals.json"
        store = ApprovalStore(str(path), dry_run=False)
        req = ApprovalRequest(action="persisted")
        store.save_request(req)
        store.approve(req.request_id, "lucas")

        store2 = ApprovalStore(str(path), dry_run=False)
        store2.load()
        decision = store2.get_decision(req.request_id)
        assert decision is not None
        assert decision.status == ApprovalStatus.APPROVED

    def test_dry_run_does_not_write(self, tmp_path):
        path = tmp_path / "dry.json"
        store = ApprovalStore(str(path), dry_run=True)
        req = ApprovalRequest(action="not_persisted")
        store.save_request(req)
        assert not path.exists()
