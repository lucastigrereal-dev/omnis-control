"""Tests for publisher approval gate (W085)."""
from __future__ import annotations

import pytest

from src.publisher.approval_gate import (
    ApprovalGate,
    ApprovalStatus,
    CaptionApproval,
)


class TestCaptionApproval:
    def test_defaults(self):
        a = CaptionApproval(approval_id="ap1", content_id="c1", caption="Test caption")
        assert a.status == ApprovalStatus.PENDING
        assert a.approver == ""

    def test_approve(self):
        a = CaptionApproval(approval_id="ap1", content_id="c1", caption="Test")
        a.approve("lucas")
        assert a.status == ApprovalStatus.APPROVED
        assert a.approver == "lucas"
        assert a.resolved_at != ""

    def test_reject(self):
        a = CaptionApproval(approval_id="ap1", content_id="c1", caption="Test")
        a.reject("lucas", "bad caption")
        assert a.status == ApprovalStatus.REJECTED
        assert a.reason == "bad caption"

    def test_is_approved(self):
        a = CaptionApproval(approval_id="ap1", content_id="c1", caption="Test")
        assert a.is_approved() is False
        a.approve("lucas")
        assert a.is_approved() is True

    def test_to_dict_roundtrip(self):
        a = CaptionApproval(approval_id="ap1", content_id="c1", caption="Test")
        a.approve("lucas")
        restored = CaptionApproval.from_dict(a.to_dict())
        assert restored.approval_id == "ap1"
        assert restored.status == ApprovalStatus.APPROVED
        assert restored.approver == "lucas"


class TestApprovalGate:
    def test_submit_creates_pending_approval(self):
        gate = ApprovalGate()
        approval = gate.submit("c1", "My caption")
        assert approval.status == ApprovalStatus.PENDING
        assert gate.check("c1") == ApprovalStatus.PENDING

    def test_approve_transitions(self):
        gate = ApprovalGate()
        gate.submit("c1", "My caption")
        gate.approve("c1", "operator")
        assert gate.check("c1") == ApprovalStatus.APPROVED
        assert gate.can_proceed("c1") is True

    def test_reject_transitions(self):
        gate = ApprovalGate()
        gate.submit("c1", "My caption")
        gate.reject("c1", "operator", "needs revision")
        assert gate.check("c1") == ApprovalStatus.REJECTED
        assert gate.can_proceed("c1") is False

    def test_check_unknown_returns_pending(self):
        gate = ApprovalGate()
        assert gate.check("nonexistent") == ApprovalStatus.PENDING

    def test_can_proceed_unknown_returns_false(self):
        gate = ApprovalGate()
        assert gate.can_proceed("nonexistent") is False

    def test_approve_unknown_raises(self):
        gate = ApprovalGate()
        with pytest.raises(KeyError):
            gate.approve("nonexistent")

    def test_reject_unknown_raises(self):
        gate = ApprovalGate()
        with pytest.raises(KeyError):
            gate.reject("nonexistent", "op")

    def test_multiple_approvals_independent(self):
        gate = ApprovalGate()
        gate.submit("c1", "Caption 1")
        gate.submit("c2", "Caption 2")
        gate.approve("c1")
        assert gate.can_proceed("c1") is True
        assert gate.can_proceed("c2") is False

    def test_to_dict(self):
        gate = ApprovalGate()
        gate.submit("c1", "Test caption")
        gate.approve("c1")
        d = gate.to_dict()
        assert "approvals" in d
        assert d["approvals"]["c1"]["status"] == "approved"
