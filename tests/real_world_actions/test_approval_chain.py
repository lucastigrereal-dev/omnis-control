"""Tests for P27 ApprovalChain (P18 bridge)."""
import pytest

from src.real_world_actions.approval_chain import ApprovalChain
from src.real_world_actions.models import (
    ActionDefinition,
    ACTION_READ, ACTION_SEND, ACTION_DEPLOY, ACTION_DELETE,
    RISK_LOW, RISK_MEDIUM, RISK_HIGH, RISK_CRITICAL,
)
from src.governance.models import (
    VERDICT_APPROVED, VERDICT_DENIED, VERDICT_REQUIRES_APPROVAL,
)
from src.governance.service import ApprovalPolicyEngine


class TestApprovalChain:
    @pytest.fixture
    def chain(self):
        engine = ApprovalPolicyEngine()
        return ApprovalChain(engine)

    def test_auto_approves_low_risk_read(self, chain):
        a = ActionDefinition.new("health_check", "mock", ACTION_READ)
        decision = chain.request_approval(a, {})
        assert decision.verdict == VERDICT_APPROVED

    def test_auto_approves_medium_risk_write(self, chain):
        a = ActionDefinition.new("save_draft", "mock", "write")
        decision = chain.request_approval(a, {"data": "draft"})
        assert decision.verdict == VERDICT_APPROVED

    def test_high_risk_requires_approval(self, chain):
        a = ActionDefinition.new("send_email", "gmail", ACTION_SEND)
        decision = chain.request_approval(a, {"to": "x@y.com"})
        assert decision.verdict == VERDICT_REQUIRES_APPROVAL
        assert chain.pending_count >= 1

    def test_critical_risk_requires_approval(self, chain):
        a = ActionDefinition.new("delete_db", "db", ACTION_DELETE)
        decision = chain.request_approval(a, {})
        assert decision.verdict == VERDICT_REQUIRES_APPROVAL

    def test_is_auto_approved_helper(self, chain):
        assert chain.is_auto_approved(ActionDefinition.new("x", "t", ACTION_READ)) is True
        assert chain.is_auto_approved(ActionDefinition.new("x", "t", ACTION_SEND)) is False
        assert chain.is_auto_approved(ActionDefinition.new("x", "t", ACTION_DEPLOY)) is False

    def test_approve_pending_request(self, chain):
        a = ActionDefinition.new("send_email", "gmail", ACTION_SEND)
        decision = chain.request_approval(a, {"to": "x@y.com"})
        pending = chain.get_pending()
        assert len(pending) == 1
        approved = chain.approve(pending[0].request_id, approved_by="lucas", reason="ok")
        assert approved.verdict == VERDICT_APPROVED
        assert chain.pending_count == 0

    def test_deny_pending_request(self, chain):
        a = ActionDefinition.new("send_email", "gmail", ACTION_SEND)
        chain.request_approval(a, {"to": "x@y.com"})
        pending = chain.get_pending()
        denied = chain.deny(pending[0].request_id, reason="not needed")
        assert denied.verdict == VERDICT_DENIED
        assert chain.pending_count == 0

    def test_approve_generates_audit_event(self, chain):
        a = ActionDefinition.new("send_email", "gmail", ACTION_SEND)
        chain.request_approval(a, {"to": "x@y.com"})
        pending = chain.get_pending()
        chain.approve(pending[0].request_id, approved_by="lucas")
        events = chain.get_events()
        # at least 2 events: one for request, one for approval
        assert len(events) >= 2

    def test_deny_generates_audit_event(self, chain):
        a = ActionDefinition.new("send_email", "gmail", ACTION_SEND)
        chain.request_approval(a, {"to": "x@y.com"})
        pending = chain.get_pending()
        chain.deny(pending[0].request_id, "spam")
        events = chain.get_events()
        assert len(events) >= 2

    def test_evaluate_deploy_critical(self, chain):
        a = ActionDefinition.new("git_push", "github", ACTION_DEPLOY)
        decision = chain.evaluate(a, {"branch": "main"})
        assert decision.risk_level == RISK_CRITICAL
        assert decision.verdict == VERDICT_REQUIRES_APPROVAL

    def test_get_decisions_accumulates(self, chain):
        a = ActionDefinition.new("send_email", "gmail", ACTION_SEND)
        chain.request_approval(a, {})
        assert len(chain.get_decisions()) >= 1

    def test_pending_count_zero_initially(self, chain):
        assert chain.pending_count == 0

    def test_multiple_pending_requests(self, chain):
        a1 = ActionDefinition.new("send_email", "gmail", ACTION_SEND)
        a2 = ActionDefinition.new("call_webhook", "webhook", ACTION_SEND)
        chain.request_approval(a1, {"to": "a@b.com"})
        chain.request_approval(a2, {"url": "https://x.com"})
        assert chain.pending_count == 2
        pending = chain.get_pending()
        assert len(pending) == 2

    def test_financial_requires_approval(self, chain):
        a = ActionDefinition.new("charge", "stripe", "financial")
        decision = chain.request_approval(a, {"amount": 100})
        assert decision.verdict == VERDICT_REQUIRES_APPROVAL
