"""Tests for P18 Governance/Audit services — RiskClassifier, ApprovalPolicyEngine, ScopeGuard, AuditLogPlanner."""
from __future__ import annotations

import pytest

from src.governance.models import (
    ApprovalPolicy,
    ScopeRule,
    RISK_LOW,
    RISK_MEDIUM,
    RISK_HIGH,
    RISK_CRITICAL,
    ACTION_READ,
    ACTION_WRITE,
    ACTION_SEND,
    ACTION_DEPLOY,
    ACTION_DELETE,
    ACTION_FINANCIAL,
    ACTION_CONFIGURE,
    VERDICT_APPROVED,
    VERDICT_DENIED,
    VERDICT_REQUIRES_APPROVAL,
)
from src.governance.service import (
    RiskClassifier,
    ApprovalPolicyEngine,
    PolicyEvalResult,
    ScopeGuard,
    AuditLogPlanner,
    DESTRUCTIVE_ACTIONS,
)
from src.governance.errors import (
    RiskClassificationError,
    PolicyViolationError,
    ScopeViolationError,
    AuditError,
    DecisionError,
)


# ── Helpers ───────────────────────────────────────────────────────────────

def _make_policy(name="P", risk_level=RISK_HIGH, action_types=None, auto_deny=False, requires_approval=True):
    return ApprovalPolicy.new(name=name, risk_level=risk_level, action_types=action_types, auto_deny=auto_deny, requires_approval=requires_approval)


def _make_rule(name="R", allowed_actions=None, blocked_actions=None, target_paths=None, blocked_paths=None, enabled=True):
    return ScopeRule.new(name=name, allowed_actions=allowed_actions, blocked_actions=blocked_actions, target_paths=target_paths, blocked_paths=blocked_paths, enabled=enabled)


# ── RiskClassifier ────────────────────────────────────────────────────────

class TestRiskClassifier:
    def test_read_is_low_risk(self):
        c = RiskClassifier()
        assert c.classify(ACTION_READ) == RISK_LOW

    def test_write_is_medium_risk(self):
        c = RiskClassifier()
        assert c.classify(ACTION_WRITE) == RISK_MEDIUM

    def test_send_is_high_risk(self):
        c = RiskClassifier()
        assert c.classify(ACTION_SEND) == RISK_HIGH

    def test_deploy_is_critical_risk(self):
        c = RiskClassifier()
        assert c.classify(ACTION_DEPLOY) == RISK_CRITICAL

    def test_delete_is_critical_risk(self):
        c = RiskClassifier()
        assert c.classify(ACTION_DELETE) == RISK_CRITICAL

    def test_financial_is_critical_risk(self):
        c = RiskClassifier()
        assert c.classify(ACTION_FINANCIAL) == RISK_CRITICAL

    def test_configure_is_high_risk(self):
        c = RiskClassifier()
        assert c.classify(ACTION_CONFIGURE) == RISK_HIGH

    def test_unknown_action_raises(self):
        c = RiskClassifier()
        with pytest.raises(RiskClassificationError, match="Unknown action type"):
            c.classify("unknown_action")

    def test_custom_risk_map(self):
        custom_map = {ACTION_READ: RISK_CRITICAL, ACTION_WRITE: RISK_LOW}
        c = RiskClassifier(risk_map=custom_map)
        assert c.classify(ACTION_READ) == RISK_CRITICAL
        assert c.classify(ACTION_WRITE) == RISK_LOW

    def test_classify_batch_all_valid(self):
        c = RiskClassifier()
        results = c.classify_batch([
            (ACTION_READ, "file.txt"),
            (ACTION_WRITE, "file.txt"),
            (ACTION_DELETE, "file.txt"),
        ])
        assert len(results) == 3
        assert results[0]["risk_level"] == RISK_LOW
        assert results[1]["risk_level"] == RISK_MEDIUM
        assert results[2]["risk_level"] == RISK_CRITICAL

    def test_classify_batch_with_errors(self):
        c = RiskClassifier()
        results = c.classify_batch([
            (ACTION_READ, "f1"),
            ("bad_action", "f2"),
            (ACTION_WRITE, "f3"),
        ])
        assert results[0]["error"] is None
        assert results[1]["error"] is not None
        assert results[2]["error"] is None

    def test_risk_map_property(self):
        c = RiskClassifier()
        assert c.risk_map[ACTION_READ] == RISK_LOW


# ── ApprovalPolicyEngine ──────────────────────────────────────────────────

class TestApprovalPolicyEngine:
    def test_no_policies_allows_read(self):
        engine = ApprovalPolicyEngine()
        result = engine.evaluate(ACTION_READ, RISK_LOW, "file.txt")
        assert result.verdict == VERDICT_APPROVED
        assert result.matched is False

    def test_no_policies_requires_approval_for_destructive(self):
        engine = ApprovalPolicyEngine()
        result = engine.evaluate(ACTION_DELETE, RISK_CRITICAL, "data/")
        assert result.verdict == VERDICT_REQUIRES_APPROVAL
        assert "Destructive action requires approval" in result.reason

    def test_policy_match_requires_approval(self):
        p = _make_policy("Write Policy", RISK_MEDIUM, action_types=[ACTION_WRITE])
        engine = ApprovalPolicyEngine(policies=[p])
        result = engine.evaluate(ACTION_WRITE, RISK_MEDIUM, "src/file.py")
        assert result.matched is True
        assert result.policy_id == p.policy_id
        assert result.verdict == VERDICT_REQUIRES_APPROVAL

    def test_policy_auto_deny(self):
        p = _make_policy("Block Deploy", RISK_CRITICAL, action_types=[ACTION_DEPLOY], auto_deny=True, requires_approval=False)
        engine = ApprovalPolicyEngine(policies=[p])
        result = engine.evaluate(ACTION_DEPLOY, RISK_CRITICAL, "production")
        assert result.verdict == VERDICT_DENIED
        assert "Auto-denied" in result.reason

    def test_policy_risk_mismatch_skips(self):
        p = _make_policy("High Only", RISK_HIGH, action_types=[ACTION_WRITE])
        engine = ApprovalPolicyEngine(policies=[p])
        result = engine.evaluate(ACTION_WRITE, RISK_MEDIUM, "file.txt")
        assert result.matched is False

    def test_policy_action_mismatch_skips(self):
        p = _make_policy("Deploy Only", RISK_CRITICAL, action_types=[ACTION_DEPLOY])
        engine = ApprovalPolicyEngine(policies=[p])
        result = engine.evaluate(ACTION_DELETE, RISK_CRITICAL, "data/")
        assert result.verdict == VERDICT_REQUIRES_APPROVAL  # destructive default

    def test_multiple_policies_first_match_wins(self):
        p1 = _make_policy("First", RISK_HIGH, action_types=[ACTION_SEND], auto_deny=True, requires_approval=False)
        p2 = _make_policy("Second", RISK_HIGH, action_types=[ACTION_SEND], requires_approval=True)
        engine = ApprovalPolicyEngine(policies=[p1, p2])
        result = engine.evaluate(ACTION_SEND, RISK_HIGH, "api/external")
        assert result.policy_id == p1.policy_id
        assert result.verdict == VERDICT_DENIED

    def test_add_policy(self):
        engine = ApprovalPolicyEngine()
        engine.add_policy(_make_policy("Added", RISK_LOW, action_types=[ACTION_READ], requires_approval=True))
        result = engine.evaluate(ACTION_READ, RISK_LOW, "file.txt")
        assert result.matched is True
        assert result.verdict == VERDICT_REQUIRES_APPROVAL

    def test_policies_property(self):
        p = _make_policy("P1", RISK_HIGH)
        engine = ApprovalPolicyEngine(policies=[p])
        assert len(engine.policies) == 1


class TestPolicyEvalResult:
    def test_matched_approved(self):
        r = PolicyEvalResult(matched=True, policy_id="pol_x", verdict=VERDICT_APPROVED, reason="ok", requires_approval=False)
        assert r.matched is True
        assert r.requires_approval is False

    def test_unmatched_denied(self):
        r = PolicyEvalResult(matched=False, policy_id=None, verdict=VERDICT_DENIED, reason="blocked", requires_approval=False)
        assert r.matched is False
        assert r.verdict == VERDICT_DENIED


# ── ScopeGuard ────────────────────────────────────────────────────────────

class TestScopeGuard:
    def test_no_rules_allows_all(self):
        g = ScopeGuard()
        assert g.check(ACTION_DELETE, "anywhere/") is True

    def test_allowed_action_in_target_path(self):
        r = _make_rule("Allow Read", allowed_actions=[ACTION_READ], target_paths=["src/mission/"])
        g = ScopeGuard(rules=[r])
        assert g.check(ACTION_READ, "src/mission/scan.py") is True

    def test_allowed_action_outside_target_path(self):
        r = _make_rule("Allow Read", allowed_actions=[ACTION_READ], target_paths=["src/mission/"])
        g = ScopeGuard(rules=[r])
        assert g.check(ACTION_READ, "src/core/config.py") is True  # default allow

    def test_blocked_action(self):
        r = _make_rule("No Delete", blocked_actions=[ACTION_DELETE])
        g = ScopeGuard(rules=[r])
        assert g.check(ACTION_DELETE, "data/cache") is False

    def test_blocked_path(self):
        r = _make_rule("Block Core", blocked_paths=["src/core/"])
        g = ScopeGuard(rules=[r])
        assert g.check(ACTION_WRITE, "src/core/config.py") is False
        assert g.check(ACTION_WRITE, "src/mission/scan.py") is True

    def test_disabled_rule_ignored(self):
        r = _make_rule("Inactive", blocked_actions=[ACTION_WRITE], enabled=False)
        g = ScopeGuard(rules=[r])
        assert g.check(ACTION_WRITE, "file.txt") is True

    def test_check_with_reason_allowed(self):
        r = _make_rule("Read Scope", allowed_actions=[ACTION_READ], target_paths=["src/"])
        g = ScopeGuard(rules=[r])
        ok, reason = g.check_with_reason(ACTION_READ, "src/file.py")
        assert ok is True
        assert "Allowed" in reason

    def test_check_with_reason_blocked(self):
        r = _make_rule("Block Delete", blocked_actions=[ACTION_DELETE])
        g = ScopeGuard(rules=[r])
        ok, reason = g.check_with_reason(ACTION_DELETE, "data/cache")
        assert ok is False
        assert "blocked" in reason.lower()

    def test_check_with_reason_blocked_path(self):
        r = _make_rule("Block Core", blocked_paths=["src/core/"])
        g = ScopeGuard(rules=[r])
        ok, reason = g.check_with_reason(ACTION_WRITE, "src/core/init.py")
        assert ok is False
        assert "blocked" in reason.lower()

    def test_multiple_rules(self):
        r1 = _make_rule("Allow Read", allowed_actions=[ACTION_READ], target_paths=["src/"])
        r2 = _make_rule("Block Delete", blocked_actions=[ACTION_DELETE])
        g = ScopeGuard(rules=[r1, r2])
        assert g.check(ACTION_READ, "src/file.py") is True
        assert g.check(ACTION_DELETE, "src/file.py") is False

    def test_add_rule(self):
        g = ScopeGuard()
        g.add_rule(_make_rule("Block All", blocked_actions=[ACTION_WRITE]))
        assert g.check(ACTION_WRITE, "any") is False

    def test_rules_property(self):
        r = _make_rule("R1")
        g = ScopeGuard(rules=[r])
        assert len(g.rules) == 1


# ── AuditLogPlanner ───────────────────────────────────────────────────────

class TestAuditLogPlanner:
    def test_record_event(self):
        p = AuditLogPlanner()
        e = p.record_event(ACTION_WRITE, RISK_MEDIUM, "src/file.py", "admin", VERDICT_APPROVED)
        assert e.event_id.startswith("audit_")
        assert p.event_count == 1

    def test_record_multiple_events(self):
        p = AuditLogPlanner()
        p.record_event(ACTION_READ, RISK_LOW, "f1.txt", "u1", VERDICT_APPROVED)
        p.record_event(ACTION_WRITE, RISK_MEDIUM, "f2.txt", "u2", VERDICT_REQUIRES_APPROVAL)
        p.record_event(ACTION_DELETE, RISK_CRITICAL, "f3.txt", "u3", VERDICT_DENIED)
        assert p.event_count == 3

    def test_record_decision(self):
        p = AuditLogPlanner()
        d = p.record_decision(ACTION_WRITE, RISK_MEDIUM, "src/file.py", VERDICT_REQUIRES_APPROVAL, "Policy match")
        assert d.decision_id.startswith("dec_")
        assert p.decision_count == 1

    def test_get_events_by_risk(self):
        p = AuditLogPlanner()
        p.record_event(ACTION_READ, RISK_LOW, "f1", "u1", VERDICT_APPROVED)
        p.record_event(ACTION_WRITE, RISK_MEDIUM, "f2", "u2", VERDICT_APPROVED)
        p.record_event(ACTION_READ, RISK_LOW, "f3", "u3", VERDICT_APPROVED)
        low_events = p.get_events_by_risk(RISK_LOW)
        assert len(low_events) == 2
        med_events = p.get_events_by_risk(RISK_MEDIUM)
        assert len(med_events) == 1

    def test_get_events_by_action(self):
        p = AuditLogPlanner()
        p.record_event(ACTION_READ, RISK_LOW, "f1", "u1", VERDICT_APPROVED)
        p.record_event(ACTION_DELETE, RISK_CRITICAL, "f2", "u2", VERDICT_DENIED)
        read_events = p.get_events_by_action(ACTION_READ)
        assert len(read_events) == 1
        del_events = p.get_events_by_action(ACTION_DELETE)
        assert len(del_events) == 1

    def test_get_decisions_by_verdict(self):
        p = AuditLogPlanner()
        p.record_decision(ACTION_READ, RISK_LOW, "f1", VERDICT_APPROVED, "ok")
        p.record_decision(ACTION_WRITE, RISK_MEDIUM, "f2", VERDICT_REQUIRES_APPROVAL, "needs review")
        p.record_decision(ACTION_DELETE, RISK_CRITICAL, "f3", VERDICT_DENIED, "blocked")
        assert len(p.get_decisions_by_verdict(VERDICT_APPROVED)) == 1
        assert len(p.get_decisions_by_verdict(VERDICT_DENIED)) == 1
        assert len(p.get_decisions_by_verdict(VERDICT_REQUIRES_APPROVAL)) == 1

    def test_generate_audit_log(self):
        p = AuditLogPlanner()
        e1 = p.record_event(ACTION_READ, RISK_LOW, "f1.txt", "user1", VERDICT_APPROVED)
        d1 = p.record_decision(ACTION_READ, RISK_LOW, "f1.txt", VERDICT_APPROVED, "allowed", audit_event_id=e1.event_id)
        log = p.generate_audit_log()
        assert len(log) == 1
        assert log[0]["event_id"] == e1.event_id
        assert len(log[0]["decisions"]) == 1
        assert log[0]["decisions"][0]["decision_id"] == d1.decision_id

    def test_generate_audit_log_event_without_decisions(self):
        p = AuditLogPlanner()
        p.record_event(ACTION_READ, RISK_LOW, "f1.txt", "user1", VERDICT_APPROVED)
        log = p.generate_audit_log()
        assert len(log) == 1
        assert log[0]["decisions"] == []

    def test_events_and_decisions_properties(self):
        p = AuditLogPlanner()
        p.record_event(ACTION_READ, RISK_LOW, "f1", "u1", VERDICT_APPROVED)
        p.record_decision(ACTION_READ, RISK_LOW, "f1", VERDICT_APPROVED, "ok")
        assert len(p.events) == 1
        assert len(p.decisions) == 1

    def test_empty_planner(self):
        p = AuditLogPlanner()
        assert p.event_count == 0
        assert p.decision_count == 0
        assert p.generate_audit_log() == []


# ── Destructive actions ───────────────────────────────────────────────────

class TestDestructiveActions:
    def test_deploy_is_destructive(self):
        assert ACTION_DEPLOY in DESTRUCTIVE_ACTIONS

    def test_delete_is_destructive(self):
        assert ACTION_DELETE in DESTRUCTIVE_ACTIONS

    def test_financial_is_destructive(self):
        assert ACTION_FINANCIAL in DESTRUCTIVE_ACTIONS

    def test_read_is_not_destructive(self):
        assert ACTION_READ not in DESTRUCTIVE_ACTIONS

    def test_write_is_not_destructive(self):
        assert ACTION_WRITE not in DESTRUCTIVE_ACTIONS
