"""P18 Governance/Audit models — risk, policy, scope, audit, decision skeleton."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

# ── Risk level constants ──────────────────────────────────────────────────
RISK_LOW = "low"
RISK_MEDIUM = "medium"
RISK_HIGH = "high"
RISK_CRITICAL = "critical"

VALID_RISK_LEVELS = {RISK_LOW, RISK_MEDIUM, RISK_HIGH, RISK_CRITICAL}

# ── Action type constants ─────────────────────────────────────────────────
ACTION_READ = "read"
ACTION_WRITE = "write"
ACTION_SEND = "send"
ACTION_DEPLOY = "deploy"
ACTION_DELETE = "delete"
ACTION_FINANCIAL = "financial"
ACTION_CONFIGURE = "configure"

VALID_ACTION_TYPES = {ACTION_READ, ACTION_WRITE, ACTION_SEND, ACTION_DEPLOY, ACTION_DELETE, ACTION_FINANCIAL, ACTION_CONFIGURE}

# ── Decision verdict constants ────────────────────────────────────────────
VERDICT_APPROVED = "approved"
VERDICT_DENIED = "denied"
VERDICT_REQUIRES_APPROVAL = "requires_approval"

VALID_VERDICTS = {VERDICT_APPROVED, VERDICT_DENIED, VERDICT_REQUIRES_APPROVAL}

# ── Default risk mapping ──────────────────────────────────────────────────
DEFAULT_ACTION_RISK_MAP = {
    ACTION_READ: RISK_LOW,
    ACTION_WRITE: RISK_MEDIUM,
    ACTION_SEND: RISK_HIGH,
    ACTION_DEPLOY: RISK_CRITICAL,
    ACTION_DELETE: RISK_CRITICAL,
    ACTION_FINANCIAL: RISK_CRITICAL,
    ACTION_CONFIGURE: RISK_HIGH,
}

# ── Helpers ───────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


# ── Models ────────────────────────────────────────────────────────────────

@dataclass
class ApprovalPolicy:
    policy_id: str
    name: str
    risk_level: str
    action_types: list[str] = field(default_factory=list)
    requires_approval: bool = True
    auto_deny: bool = False
    description: str = ""
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        name: str,
        risk_level: str,
        action_types: list[str] | None = None,
        requires_approval: bool = True,
        auto_deny: bool = False,
        description: str = "",
    ) -> "ApprovalPolicy":
        if risk_level not in VALID_RISK_LEVELS:
            raise ValueError(f"Invalid risk level: {risk_level!r}. Must be one of {sorted(VALID_RISK_LEVELS)}")
        for at in (action_types or []):
            if at not in VALID_ACTION_TYPES:
                raise ValueError(f"Invalid action type: {at!r}. Must be one of {sorted(VALID_ACTION_TYPES)}")
        return cls(
            policy_id=_new_id("pol"),
            name=name,
            risk_level=risk_level,
            action_types=action_types or [],
            requires_approval=requires_approval,
            auto_deny=auto_deny,
            description=description,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "risk_level": self.risk_level,
            "action_types": self.action_types,
            "requires_approval": self.requires_approval,
            "auto_deny": self.auto_deny,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "ApprovalPolicy":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ScopeRule:
    rule_id: str
    name: str
    allowed_actions: list[str] = field(default_factory=list)
    blocked_actions: list[str] = field(default_factory=list)
    target_paths: list[str] = field(default_factory=list)
    blocked_paths: list[str] = field(default_factory=list)
    enabled: bool = True
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        name: str,
        allowed_actions: list[str] | None = None,
        blocked_actions: list[str] | None = None,
        target_paths: list[str] | None = None,
        blocked_paths: list[str] | None = None,
        enabled: bool = True,
    ) -> "ScopeRule":
        for at in (allowed_actions or []):
            if at not in VALID_ACTION_TYPES:
                raise ValueError(f"Invalid action type: {at!r}. Must be one of {sorted(VALID_ACTION_TYPES)}")
        for at in (blocked_actions or []):
            if at not in VALID_ACTION_TYPES:
                raise ValueError(f"Invalid action type: {at!r}. Must be one of {sorted(VALID_ACTION_TYPES)}")
        return cls(
            rule_id=_new_id("scope"),
            name=name,
            allowed_actions=allowed_actions or [],
            blocked_actions=blocked_actions or [],
            target_paths=target_paths or [],
            blocked_paths=blocked_paths or [],
            enabled=enabled,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "allowed_actions": self.allowed_actions,
            "blocked_actions": self.blocked_actions,
            "target_paths": self.target_paths,
            "blocked_paths": self.blocked_paths,
            "enabled": self.enabled,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "ScopeRule":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class AuditEvent:
    event_id: str
    action_type: str
    risk_level: str
    target: str
    actor: str
    verdict: str
    timestamp: str = field(default_factory=_now_iso)
    details: dict[str, object] = field(default_factory=dict)
    approved_by: str | None = None

    @classmethod
    def new(
        cls,
        action_type: str,
        risk_level: str,
        target: str,
        actor: str,
        verdict: str,
        details: dict[str, object] | None = None,
        approved_by: str | None = None,
    ) -> "AuditEvent":
        if action_type not in VALID_ACTION_TYPES:
            raise ValueError(f"Invalid action type: {action_type!r}. Must be one of {sorted(VALID_ACTION_TYPES)}")
        if risk_level not in VALID_RISK_LEVELS:
            raise ValueError(f"Invalid risk level: {risk_level!r}. Must be one of {sorted(VALID_RISK_LEVELS)}")
        if verdict not in VALID_VERDICTS:
            raise ValueError(f"Invalid verdict: {verdict!r}. Must be one of {sorted(VALID_VERDICTS)}")
        return cls(
            event_id=_new_id("audit"),
            action_type=action_type,
            risk_level=risk_level,
            target=target,
            actor=actor,
            verdict=verdict,
            details=details or {},
            approved_by=approved_by,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "event_id": self.event_id,
            "action_type": self.action_type,
            "risk_level": self.risk_level,
            "target": self.target,
            "actor": self.actor,
            "verdict": self.verdict,
            "timestamp": self.timestamp,
            "details": self.details,
            "approved_by": self.approved_by,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "AuditEvent":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class GovernanceDecision:
    decision_id: str
    action_type: str
    risk_level: str
    target: str
    verdict: str
    reason: str
    timestamp: str = field(default_factory=_now_iso)
    policy_id: str | None = None
    audit_event_id: str | None = None

    @classmethod
    def new(
        cls,
        action_type: str,
        risk_level: str,
        target: str,
        verdict: str,
        reason: str,
        policy_id: str | None = None,
        audit_event_id: str | None = None,
    ) -> "GovernanceDecision":
        if action_type not in VALID_ACTION_TYPES:
            raise ValueError(f"Invalid action type: {action_type!r}. Must be one of {sorted(VALID_ACTION_TYPES)}")
        if risk_level not in VALID_RISK_LEVELS:
            raise ValueError(f"Invalid risk level: {risk_level!r}. Must be one of {sorted(VALID_RISK_LEVELS)}")
        if verdict not in VALID_VERDICTS:
            raise ValueError(f"Invalid verdict: {verdict!r}. Must be one of {sorted(VALID_VERDICTS)}")
        return cls(
            decision_id=_new_id("dec"),
            action_type=action_type,
            risk_level=risk_level,
            target=target,
            verdict=verdict,
            reason=reason,
            policy_id=policy_id,
            audit_event_id=audit_event_id,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "decision_id": self.decision_id,
            "action_type": self.action_type,
            "risk_level": self.risk_level,
            "target": self.target,
            "verdict": self.verdict,
            "reason": self.reason,
            "timestamp": self.timestamp,
            "policy_id": self.policy_id,
            "audit_event_id": self.audit_event_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "GovernanceDecision":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
