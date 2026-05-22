"""Tests for ApprovalGate — human approval before publishing."""
from __future__ import annotations

import pytest

from src.publishing.approval_gate import (
    ApprovalGate,
    ApprovalRequest,
    ApprovalDecision,
    ApprovalStatus,
)


class TestApprovalGateAuto:
    def test_auto_approve_above_threshold(self):
        gate = ApprovalGate(mode="auto", auto_approve_threshold=85)
        decision = gate.request_approval(
            content="Test caption content here",
            score=90,
        )
        assert decision.approved is True
        assert decision.decided_by == "auto"
        assert "auto-approved" in decision.reason

    def test_auto_reject_below_threshold(self):
        gate = ApprovalGate(mode="auto", auto_approve_threshold=85)
        decision = gate.request_approval(
            content="Low quality content",
            score=60,
        )
        assert decision.approved is False
        assert decision.decided_by == "auto"

    def test_auto_approve_at_threshold(self):
        gate = ApprovalGate(mode="auto", auto_approve_threshold=85)
        decision = gate.request_approval(content="Edge case", score=85)
        assert decision.approved is True

    def test_approval_logs_decisions(self):
        gate = ApprovalGate(mode="auto")
        gate.request_approval(content="A", score=90)
        gate.request_approval(content="B", score=50)
        assert len(gate.decisions) == 2

    def test_approval_rate_calculation(self):
        gate = ApprovalGate(mode="auto")
        gate.request_approval(content="A", score=90)  # approve
        gate.request_approval(content="B", score=90)  # approve
        gate.request_approval(content="C", score=50)  # reject
        rate = gate.approval_rate()
        assert rate == pytest.approx(2 / 3, rel=0.01)


class TestApprovalGateTelegram:
    def test_telegram_queues_requests(self):
        gate = ApprovalGate(mode="telegram")
        decision = gate.request_approval(content="Test", score=70)
        assert decision.approved is False
        assert decision.decided_by == "pending_telegram"
        assert len(gate.pending) == 1

    def test_approve_all_pending(self):
        gate = ApprovalGate(mode="telegram")
        gate.request_approval(content="A", score=70)
        gate.request_approval(content="B", score=80)
        decisions = gate.approve_all_pending()
        assert len(decisions) == 2
        assert all(d.approved for d in decisions)
        assert len(gate.pending) == 0


class TestApprovalGateUnknownMode:
    def test_unknown_mode_rejects(self):
        gate = ApprovalGate(mode="unknown_mode_xyz")
        decision = gate.request_approval(content="Test", score=90)
        assert decision.approved is False
        assert "unknown mode" in decision.reason


class TestApprovalRequest:
    def test_approval_request_defaults(self):
        req = ApprovalRequest(request_id="apr_001", content_preview="Preview")
        assert req.status == ApprovalStatus.PENDING
        assert req.score == 0

    def test_approval_request_to_dict(self):
        req = ApprovalRequest(
            request_id="apr_001",
            content_type="caption",
            content_preview="H",
            score=85,
            page="@test",
        )
        d = req.to_dict()
        assert d["request_id"] == "apr_001"
        assert d["score"] == 85


class TestApprovalDecision:
    def test_decision_defaults(self):
        d = ApprovalDecision(request_id="apr_001", approved=True)
        assert d.decided_by == "auto"
        assert d.approved is True

    def test_decision_to_dict(self):
        d = ApprovalDecision(request_id="apr_001", approved=False, reason="score too low")
        data = d.to_dict()
        assert data["approved"] is False
        assert data["reason"] == "score too low"


class TestApprovalGateToDict:
    def test_to_dict_snapshot(self):
        gate = ApprovalGate(mode="auto")
        gate.request_approval(content="X", score=90, page="@test")
        data = gate.to_dict()
        assert data["mode"] == "auto"
        assert data["approval_rate"] == 1.0
        assert len(data["decisions"]) == 1
        assert data["pending_count"] == 0
