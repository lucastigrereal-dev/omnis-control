"""Tests for GuardrailsEnforcer — risk score evaluation, batch, worst verdict."""
from __future__ import annotations

import pytest

from src.governance.enforcer import (
    GuardrailsEnforcer,
    EnforcerVerdict,
    RISK_SCORE,
    SCORE_AUTO_APPROVE,
    SCORE_NEEDS_APPROVAL,
    SCORE_AUTO_DENY,
)
from src.governance.models import (
    ACTION_READ,
    ACTION_WRITE,
    ACTION_SEND,
    ACTION_DEPLOY,
    ACTION_DELETE,
    ACTION_FINANCIAL,
    RISK_LOW,
    RISK_MEDIUM,
    RISK_HIGH,
    RISK_CRITICAL,
    VERDICT_APPROVED,
    VERDICT_DENIED,
    VERDICT_REQUIRES_APPROVAL,
)


@pytest.fixture
def enforcer():
    return GuardrailsEnforcer()


# ── EnforcerVerdict ────────────────────────────────────────────────────

class TestEnforcerVerdict:
    def test_blocked_is_true_when_denied(self):
        v = EnforcerVerdict(
            action_type=ACTION_DEPLOY, risk_level=RISK_CRITICAL,
            score=10, verdict=VERDICT_DENIED, reason="blocked",
        )
        assert v.blocked is True
        assert v.allowed is False
        assert v.needs_approval is False

    def test_needs_approval(self):
        v = EnforcerVerdict(
            action_type=ACTION_SEND, risk_level=RISK_HIGH,
            score=7, verdict=VERDICT_REQUIRES_APPROVAL, reason="needs ok",
        )
        assert v.needs_approval is True
        assert v.blocked is False
        assert v.allowed is False

    def test_allowed(self):
        v = EnforcerVerdict(
            action_type=ACTION_READ, risk_level=RISK_LOW,
            score=1, verdict=VERDICT_APPROVED, reason="ok",
        )
        assert v.allowed is True
        assert v.blocked is False
        assert v.needs_approval is False

    def test_to_dict(self):
        v = EnforcerVerdict(
            action_type=ACTION_WRITE, risk_level=RISK_MEDIUM,
            score=3, verdict=VERDICT_APPROVED, reason="ok",
        )
        d = v.to_dict()
        assert d["score"] == 3
        assert d["verdict"] == VERDICT_APPROVED


# ── evaluate ───────────────────────────────────────────────────────────

class TestEvaluate:
    def test_read_is_approved(self, enforcer):
        v = enforcer.evaluate(ACTION_READ)
        assert v.verdict == VERDICT_APPROVED
        assert v.score == RISK_SCORE[RISK_LOW]

    def test_write_is_approved(self, enforcer):
        v = enforcer.evaluate(ACTION_WRITE)
        assert v.verdict == VERDICT_APPROVED
        assert v.score == 3

    def test_send_needs_approval(self, enforcer):
        v = enforcer.evaluate(ACTION_SEND)
        assert v.verdict == VERDICT_REQUIRES_APPROVAL
        assert v.score == 7

    def test_deploy_is_denied(self, enforcer):
        v = enforcer.evaluate(ACTION_DEPLOY)
        assert v.verdict == VERDICT_DENIED
        assert v.score == 10

    def test_delete_is_denied(self, enforcer):
        v = enforcer.evaluate(ACTION_DELETE)
        assert v.verdict == VERDICT_DENIED

    def test_financial_is_denied(self, enforcer):
        v = enforcer.evaluate(ACTION_FINANCIAL)
        assert v.verdict == VERDICT_DENIED

    def test_records_to_log(self, enforcer):
        assert enforcer.log_count == 0
        enforcer.evaluate(ACTION_READ)
        assert enforcer.log_count == 1

    def test_can_clear_log(self, enforcer):
        enforcer.evaluate(ACTION_READ)
        enforcer.evaluate(ACTION_WRITE)
        assert enforcer.log_count == 2
        enforcer.clear_log()
        assert enforcer.log_count == 0


# ── evaluate_batch ─────────────────────────────────────────────────────

class TestEvaluateBatch:
    def test_batch_all_same_type(self, enforcer):
        verdicts = enforcer.evaluate_batch([ACTION_READ] * 5)
        assert len(verdicts) == 5
        assert all(v.verdict == VERDICT_APPROVED for v in verdicts)

    def test_batch_mixed_types(self, enforcer):
        verdicts = enforcer.evaluate_batch(
            [ACTION_READ, ACTION_WRITE, ACTION_DEPLOY]
        )
        assert len(verdicts) == 3
        assert verdicts[0].verdict == VERDICT_APPROVED
        assert verdicts[2].verdict == VERDICT_DENIED


# ── worst_verdict ──────────────────────────────────────────────────────

class TestWorstVerdict:
    def test_empty_actions_returns_safe(self, enforcer):
        v = enforcer.worst_verdict([])
        assert v.verdict == VERDICT_APPROVED
        assert v.score == 0

    def test_all_safe_returns_approved(self, enforcer):
        v = enforcer.worst_verdict([ACTION_READ, ACTION_READ])
        assert v.verdict == VERDICT_APPROVED

    def test_one_critical_makes_worst(self, enforcer):
        v = enforcer.worst_verdict([ACTION_READ, ACTION_DEPLOY])
        assert v.score == 10
        assert v.verdict == VERDICT_DENIED

    def test_one_high_makes_needs_approval(self, enforcer):
        v = enforcer.worst_verdict([ACTION_READ, ACTION_SEND])
        assert v.score == 7
        assert v.verdict == VERDICT_REQUIRES_APPROVAL


# ── score constants ────────────────────────────────────────────────────

def test_score_constants_make_sense():
    assert SCORE_AUTO_APPROVE < SCORE_NEEDS_APPROVAL
    assert SCORE_NEEDS_APPROVAL < SCORE_AUTO_DENY
    assert RISK_SCORE[RISK_LOW] <= SCORE_AUTO_APPROVE
    assert RISK_SCORE[RISK_CRITICAL] >= SCORE_AUTO_DENY
