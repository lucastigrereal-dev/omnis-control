"""Tests for ApprovalGate runtime — risk eval, approval requests, status files."""
from __future__ import annotations

import json

import pytest

from src.governance.approval_gate import (
    ApprovalGate,
    ApprovalRequest,
    ApprovalStatus,
    _risk_rank,
)
from src.governance.models import (
    ACTION_READ,
    ACTION_WRITE,
    ACTION_SEND,
    ACTION_DEPLOY,
    ACTION_DELETE,
    ACTION_FINANCIAL,
    ACTION_CONFIGURE,
    RISK_LOW,
    RISK_MEDIUM,
    RISK_HIGH,
    RISK_CRITICAL,
    VERDICT_APPROVED,
    VERDICT_DENIED,
    VERDICT_REQUIRES_APPROVAL,
)


# ── fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def gate():
    return ApprovalGate(dry_run=True)


@pytest.fixture
def live_gate():
    return ApprovalGate(dry_run=False)


# ── _risk_rank ─────────────────────────────────────────────────────────

def test_risk_rank_ordering():
    assert _risk_rank("low") < _risk_rank("medium")
    assert _risk_rank("medium") < _risk_rank("high")
    assert _risk_rank("high") < _risk_rank("critical")
    assert _risk_rank("unknown") == 0


# ── ApprovalRequest ────────────────────────────────────────────────────

class TestApprovalRequest:
    def test_defaults(self):
        req = ApprovalRequest()
        assert req.request_id.startswith("APR-")
        assert req.risk_level == "low"
        assert req.dry_run is True

    def test_to_dict(self):
        req = ApprovalRequest(
            mission_id="MIS-001",
            summary="Teste",
            risk_level="high",
            action_count=5,
        )
        d = req.to_dict()
        assert d["mission_id"] == "MIS-001"
        assert d["risk_level"] == "high"

    def test_to_markdown(self):
        req = ApprovalRequest(
            mission_id="MIS-001",
            summary="Criar campanha",
            risk_level="medium",
            action_count=3,
            auto_verdict=VERDICT_APPROVED,
            reason="ok",
        )
        md = req.to_markdown()
        assert "MIS-001" in md
        assert "Criar campanha" in md
        assert VERDICT_APPROVED in md


# ── ApprovalStatus ─────────────────────────────────────────────────────

class TestApprovalStatus:
    def test_to_dict(self):
        status = ApprovalStatus(
            mission_id="MIS-001",
            request_id="APR-01",
            verdict=VERDICT_APPROVED,
            approved_by="lucas",
        )
        d = status.to_dict()
        assert d["verdict"] == VERDICT_APPROVED
        assert d["approved_by"] == "lucas"

    def test_from_dict(self):
        data = {
            "mission_id": "MIS-001",
            "request_id": "APR-01",
            "verdict": VERDICT_DENIED,
            "approved_by": "",
            "approved_at": "",
            "reason": "blocked",
            "gate_version": "1.0.0",
        }
        status = ApprovalStatus.from_dict(data)
        assert status.verdict == VERDICT_DENIED
        assert status.reason == "blocked"

    def test_round_trip(self):
        status = ApprovalStatus(
            mission_id="MIS-RT",
            request_id="APR-RT",
            verdict=VERDICT_APPROVED,
            approved_by="lucas",
            approved_at="2026-05-18T10:00:00Z",
            reason="passed",
        )
        assert ApprovalStatus.from_dict(status.to_dict()) == status


# ── evaluate ───────────────────────────────────────────────────────────

class TestEvaluate:
    def test_empty_actions_auto_approve(self, live_gate):
        req = live_gate.evaluate("MIS-001", "nada", [])
        assert req.auto_verdict == VERDICT_APPROVED
        assert req.requires_input is False

    def test_dry_run_always_auto_approve(self, gate):
        req = gate.evaluate("MIS-001", "fazer deploy", [ACTION_DEPLOY])
        assert req.auto_verdict == VERDICT_APPROVED
        assert req.requires_input is False

    def test_critical_auto_denies_in_live(self, live_gate):
        req = live_gate.evaluate("MIS-001", "deletar banco", [ACTION_DELETE])
        assert req.auto_verdict == VERDICT_DENIED
        assert req.risk_level == RISK_CRITICAL
        assert req.requires_input is False

    def test_high_risk_requires_input_in_live(self, live_gate):
        req = live_gate.evaluate("MIS-001", "enviar email", [ACTION_SEND])
        assert req.risk_level == RISK_HIGH
        assert req.requires_input is True
        assert req.auto_verdict == VERDICT_REQUIRES_APPROVAL

    def test_low_risk_auto_approve(self, live_gate):
        req = live_gate.evaluate("MIS-001", "ler arquivo", [ACTION_READ])
        assert req.auto_verdict == VERDICT_APPROVED
        assert req.requires_input is False

    def test_worst_risk_wins(self, live_gate):
        req = live_gate.evaluate(
            "MIS-001", "várias ações",
            [ACTION_READ, ACTION_WRITE, ACTION_DEPLOY]
        )
        assert req.risk_level == RISK_CRITICAL

    def test_action_count_tracks_total(self, live_gate):
        req = live_gate.evaluate("MIS-001", "muitas", [ACTION_READ] * 10)
        assert req.action_count == 10

    def test_financial_is_critical(self, live_gate):
        req = live_gate.evaluate("MIS-001", "cobrar", [ACTION_FINANCIAL])
        assert req.risk_level == RISK_CRITICAL

    def test_configure_is_high(self, live_gate):
        req = live_gate.evaluate("MIS-001", "configurar", [ACTION_CONFIGURE])
        assert req.risk_level == RISK_HIGH


# ── approve / deny ─────────────────────────────────────────────────────

class TestApproveDeny:
    def test_approve_returns_status(self, live_gate):
        req = live_gate.evaluate("MIS-001", "fazer", [ACTION_READ])
        status = live_gate.approve(req, approved_by="lucas")
        assert status.verdict == VERDICT_APPROVED
        assert status.approved_by == "lucas"
        assert status.approved_at != ""

    def test_deny_returns_status(self, live_gate):
        req = live_gate.evaluate("MIS-001", "não fazer", [ACTION_WRITE])
        status = live_gate.deny(req, reason="muito arriscado")
        assert status.verdict == VERDICT_DENIED
        assert status.reason == "muito arriscado"

    def test_approve_records_audit_event(self, live_gate):
        req = live_gate.evaluate("MIS-001", "ok", [ACTION_READ])
        assert live_gate.audit.event_count == 0
        live_gate.approve(req, approved_by="lucas")
        assert live_gate.audit.event_count == 1

    def test_deny_records_audit_event(self, live_gate):
        req = live_gate.evaluate("MIS-001", "nok", [ACTION_WRITE])
        live_gate.deny(req)
        assert live_gate.audit.event_count == 1

    def test_approve_records_decision(self, live_gate):
        req = live_gate.evaluate("MIS-001", "ok", [ACTION_READ])
        live_gate.approve(req, approved_by="lucas")
        assert live_gate.audit.decision_count == 1


# ── file writing ───────────────────────────────────────────────────────

class TestFileWriting:
    def test_writes_approval_files(self, gate, tmp_path):
        approval_dir = tmp_path / "07_approval"
        req = gate.evaluate("MIS-001", "teste", [ACTION_READ])
        status = gate.approve(req, approved_by="lucas")
        gate.write_approval_files(approval_dir, req, status)

        req_md = approval_dir / "approval_request.md"
        assert req_md.exists()
        content = req_md.read_text(encoding="utf-8")
        assert "MIS-001" in content

        status_json = approval_dir / "approval_status.json"
        assert status_json.exists()
        data = json.loads(status_json.read_text(encoding="utf-8"))
        assert data["verdict"] == VERDICT_APPROVED
        assert data["approved_by"] == "lucas"

    def test_creates_missing_dirs(self, gate, tmp_path):
        approval_dir = tmp_path / "missions" / "MIS-001" / "07_approval"
        req = gate.evaluate("MIS-001", "x", [])
        status = gate.approve(req, approved_by="lucas")
        gate.write_approval_files(approval_dir, req, status)
        assert approval_dir.exists()
        assert (approval_dir / "approval_request.md").exists()
        assert (approval_dir / "approval_status.json").exists()


# ── integration with existing governance ───────────────────────────────

class TestGovernanceIntegration:
    def test_uses_risk_classifier_default_map(self):
        gate = ApprovalGate(dry_run=False)
        assert gate.risk_classifier.classify(ACTION_DEPLOY) == RISK_CRITICAL
        assert gate.risk_classifier.classify(ACTION_READ) == RISK_LOW
        assert gate.risk_classifier.classify(ACTION_WRITE) == RISK_MEDIUM

    def test_can_inject_custom_classifier(self):
        custom = {"custom_action": "high"}
        gate = ApprovalGate(
            dry_run=False,
            risk_classifier=None,  # relies on default
        )
        req = gate.evaluate("MIS-001", "teste", [ACTION_READ, ACTION_WRITE])
        assert req.risk_level == RISK_MEDIUM

    def test_evaluate_summary_preserved(self, live_gate):
        req = live_gate.evaluate("MIS-001", "campanha de marketing", [ACTION_READ])
        assert req.summary == "campanha de marketing"
