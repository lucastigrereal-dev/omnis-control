"""Tests for P18 Governance/Audit models."""
from __future__ import annotations

import pytest

from src.governance.models import (
    ApprovalPolicy,
    ScopeRule,
    AuditEvent,
    GovernanceDecision,
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
    VALID_RISK_LEVELS,
    VALID_ACTION_TYPES,
    VALID_VERDICTS,
    DEFAULT_ACTION_RISK_MAP,
)


class TestApprovalPolicy:
    def test_new_creates_policy_with_id(self):
        p = ApprovalPolicy.new("Default Policy", RISK_HIGH)
        assert p.policy_id.startswith("pol_")
        assert len(p.policy_id) == 12  # "pol_" + 8 hex
        assert p.name == "Default Policy"
        assert p.risk_level == RISK_HIGH
        assert p.action_types == []
        assert p.requires_approval is True
        assert p.auto_deny is False

    def test_new_with_action_types(self):
        p = ApprovalPolicy.new(
            "Write Policy", RISK_MEDIUM,
            action_types=[ACTION_WRITE, ACTION_DELETE],
            requires_approval=True,
            description="Requires approval for writes",
        )
        assert p.action_types == [ACTION_WRITE, ACTION_DELETE]
        assert p.description == "Requires approval for writes"

    def test_new_auto_deny(self):
        p = ApprovalPolicy.new(
            "Block Deploy", RISK_CRITICAL,
            action_types=[ACTION_DEPLOY],
            auto_deny=True,
            requires_approval=False,
        )
        assert p.auto_deny is True
        assert p.requires_approval is False

    def test_new_rejects_invalid_risk_level(self):
        with pytest.raises(ValueError, match="Invalid risk level"):
            ApprovalPolicy.new("Bad", "extreme")

    def test_new_rejects_invalid_action_type(self):
        with pytest.raises(ValueError, match="Invalid action type"):
            ApprovalPolicy.new("Bad", RISK_HIGH, action_types=["hack"])

    def test_round_trip_dict(self):
        p = ApprovalPolicy.new(
            "Round Trip", RISK_CRITICAL,
            action_types=[ACTION_FINANCIAL, ACTION_DEPLOY],
            requires_approval=True, auto_deny=False, description="desc",
        )
        d = p.to_dict()
        p2 = ApprovalPolicy.from_dict(d)
        assert p2.policy_id == p.policy_id
        assert p2.name == p.name
        assert p2.risk_level == p.risk_level
        assert p2.action_types == p.action_types
        assert p2.auto_deny == p.auto_deny
        assert p2.description == p.description

    def test_timestamps_set(self):
        p = ApprovalPolicy.new("TS Policy", RISK_LOW)
        assert "T" in p.created_at
        assert "T" in p.updated_at


class TestScopeRule:
    def test_new_creates_rule_with_id(self):
        r = ScopeRule.new("Read-Only Scope", allowed_actions=[ACTION_READ])
        assert r.rule_id.startswith("scope_")
        assert r.name == "Read-Only Scope"
        assert r.allowed_actions == [ACTION_READ]
        assert r.blocked_actions == []
        assert r.target_paths == []
        assert r.blocked_paths == []
        assert r.enabled is True

    def test_new_blocked_actions(self):
        r = ScopeRule.new(
            "No Delete", blocked_actions=[ACTION_DELETE, ACTION_DEPLOY],
            target_paths=["src/core/"],
        )
        assert r.blocked_actions == [ACTION_DELETE, ACTION_DEPLOY]
        assert r.target_paths == ["src/core/"]

    def test_new_disabled(self):
        r = ScopeRule.new("Inactive", enabled=False)
        assert r.enabled is False

    def test_new_rejects_invalid_allowed_action(self):
        with pytest.raises(ValueError, match="Invalid action type"):
            ScopeRule.new("Bad", allowed_actions=["invalid"])

    def test_new_rejects_invalid_blocked_action(self):
        with pytest.raises(ValueError, match="Invalid action type"):
            ScopeRule.new("Bad", blocked_actions=["invalid"])

    def test_round_trip_dict(self):
        r = ScopeRule.new(
            "Full Rule",
            allowed_actions=[ACTION_READ, ACTION_WRITE],
            blocked_actions=[ACTION_DELETE],
            target_paths=["src/mission/"],
            blocked_paths=["src/core/"],
            enabled=True,
        )
        d = r.to_dict()
        r2 = ScopeRule.from_dict(d)
        assert r2.rule_id == r.rule_id
        assert r2.name == r.name
        assert r2.allowed_actions == r.allowed_actions
        assert r2.blocked_actions == r.blocked_actions
        assert r2.target_paths == r.target_paths
        assert r2.blocked_paths == r.blocked_paths


class TestAuditEvent:
    def test_new_creates_event_with_id(self):
        e = AuditEvent.new(
            action_type=ACTION_WRITE,
            risk_level=RISK_MEDIUM,
            target="src/governance/models.py",
            actor="system",
            verdict=VERDICT_APPROVED,
        )
        assert e.event_id.startswith("audit_")
        assert e.action_type == ACTION_WRITE
        assert e.risk_level == RISK_MEDIUM
        assert e.target == "src/governance/models.py"
        assert e.actor == "system"
        assert e.verdict == VERDICT_APPROVED
        assert e.details == {}
        assert e.approved_by is None

    def test_new_with_details_and_approver(self):
        e = AuditEvent.new(
            action_type=ACTION_DEPLOY,
            risk_level=RISK_CRITICAL,
            target="production",
            actor="admin",
            verdict=VERDICT_REQUIRES_APPROVAL,
            details={"env": "prod", "version": "2.0"},
            approved_by="security-team",
        )
        assert e.details == {"env": "prod", "version": "2.0"}
        assert e.approved_by == "security-team"

    def test_new_rejects_invalid_action_type(self):
        with pytest.raises(ValueError, match="Invalid action type"):
            AuditEvent.new("bad", RISK_LOW, "t", "a", VERDICT_APPROVED)

    def test_new_rejects_invalid_risk_level(self):
        with pytest.raises(ValueError, match="Invalid risk level"):
            AuditEvent.new(ACTION_READ, "extreme", "t", "a", VERDICT_APPROVED)

    def test_new_rejects_invalid_verdict(self):
        with pytest.raises(ValueError, match="Invalid verdict"):
            AuditEvent.new(ACTION_READ, RISK_LOW, "t", "a", "maybe")

    def test_round_trip_dict(self):
        e = AuditEvent.new(
            action_type=ACTION_SEND,
            risk_level=RISK_HIGH,
            target="api/external",
            actor="service-x",
            verdict=VERDICT_DENIED,
            details={"reason": "rate limit"},
            approved_by=None,
        )
        d = e.to_dict()
        e2 = AuditEvent.from_dict(d)
        assert e2.event_id == e.event_id
        assert e2.action_type == e.action_type
        assert e2.risk_level == e.risk_level
        assert e2.verdict == e.verdict
        assert e2.details == e.details

    def test_timestamp_set(self):
        e = AuditEvent.new(ACTION_READ, RISK_LOW, "file.txt", "user", VERDICT_APPROVED)
        assert "T" in e.timestamp


class TestGovernanceDecision:
    def test_new_creates_decision_with_id(self):
        d = GovernanceDecision.new(
            action_type=ACTION_WRITE,
            risk_level=RISK_MEDIUM,
            target="src/governance/",
            verdict=VERDICT_REQUIRES_APPROVAL,
            reason="Policy match: write requires approval",
        )
        assert d.decision_id.startswith("dec_")
        assert d.action_type == ACTION_WRITE
        assert d.risk_level == RISK_MEDIUM
        assert d.verdict == VERDICT_REQUIRES_APPROVAL
        assert d.reason == "Policy match: write requires approval"
        assert d.policy_id is None
        assert d.audit_event_id is None

    def test_new_with_policy_and_audit_refs(self):
        d = GovernanceDecision.new(
            action_type=ACTION_DELETE,
            risk_level=RISK_CRITICAL,
            target="data/cache",
            verdict=VERDICT_DENIED,
            reason="Auto-deny by critical policy",
            policy_id="pol_abc123",
            audit_event_id="audit_def456",
        )
        assert d.policy_id == "pol_abc123"
        assert d.audit_event_id == "audit_def456"

    def test_new_rejects_invalid_action_type(self):
        with pytest.raises(ValueError, match="Invalid action type"):
            GovernanceDecision.new("bad", RISK_LOW, "t", VERDICT_APPROVED, "r")

    def test_new_rejects_invalid_risk_level(self):
        with pytest.raises(ValueError, match="Invalid risk level"):
            GovernanceDecision.new(ACTION_READ, "bad", "t", VERDICT_APPROVED, "r")

    def test_new_rejects_invalid_verdict(self):
        with pytest.raises(ValueError, match="Invalid verdict"):
            GovernanceDecision.new(ACTION_READ, RISK_LOW, "t", "bad", "r")

    def test_round_trip_dict(self):
        d = GovernanceDecision.new(
            action_type=ACTION_CONFIGURE,
            risk_level=RISK_HIGH,
            target="settings.json",
            verdict=VERDICT_REQUIRES_APPROVAL,
            reason="Config change needs review",
            policy_id="pol_xyz",
            audit_event_id="audit_xyz",
        )
        data = d.to_dict()
        d2 = GovernanceDecision.from_dict(data)
        assert d2.decision_id == d.decision_id
        assert d2.action_type == d.action_type
        assert d2.verdict == d.verdict
        assert d2.reason == d.reason
        assert d2.policy_id == d.policy_id
        assert d2.audit_event_id == d.audit_event_id

    def test_timestamp_set(self):
        d = GovernanceDecision.new(ACTION_READ, RISK_LOW, "t", VERDICT_APPROVED, "ok")
        assert "T" in d.timestamp


class TestConstants:
    def test_valid_risk_levels(self):
        assert len(VALID_RISK_LEVELS) == 4
        assert RISK_LOW in VALID_RISK_LEVELS
        assert RISK_CRITICAL in VALID_RISK_LEVELS

    def test_valid_action_types(self):
        assert len(VALID_ACTION_TYPES) == 7
        assert ACTION_READ in VALID_ACTION_TYPES
        assert ACTION_FINANCIAL in VALID_ACTION_TYPES

    def test_valid_verdicts(self):
        assert len(VALID_VERDICTS) == 3
        assert VERDICT_APPROVED in VALID_VERDICTS
        assert VERDICT_DENIED in VALID_VERDICTS
        assert VERDICT_REQUIRES_APPROVAL in VALID_VERDICTS

    def test_default_risk_map_mappings(self):
        assert DEFAULT_ACTION_RISK_MAP[ACTION_READ] == RISK_LOW
        assert DEFAULT_ACTION_RISK_MAP[ACTION_WRITE] == RISK_MEDIUM
        assert DEFAULT_ACTION_RISK_MAP[ACTION_SEND] == RISK_HIGH
        assert DEFAULT_ACTION_RISK_MAP[ACTION_DEPLOY] == RISK_CRITICAL
        assert DEFAULT_ACTION_RISK_MAP[ACTION_DELETE] == RISK_CRITICAL
        assert DEFAULT_ACTION_RISK_MAP[ACTION_FINANCIAL] == RISK_CRITICAL
        assert DEFAULT_ACTION_RISK_MAP[ACTION_CONFIGURE] == RISK_HIGH

    def test_default_risk_map_covers_all_action_types(self):
        for at in VALID_ACTION_TYPES:
            assert at in DEFAULT_ACTION_RISK_MAP, f"Missing risk mapping for {at}"
