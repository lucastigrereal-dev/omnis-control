"""P18 Governance/Audit services — RiskClassifier, ApprovalPolicyEngine, ScopeGuard, AuditLogPlanner."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.governance.models import (
    ApprovalPolicy,
    ScopeRule,
    AuditEvent,
    GovernanceDecision,
    DEFAULT_ACTION_RISK_MAP,
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
    VERDICT_APPROVED,
    VERDICT_DENIED,
    VERDICT_REQUIRES_APPROVAL,
    VALID_ACTION_TYPES,
    VALID_RISK_LEVELS,
)
from src.governance.errors import (
    RiskClassificationError,
    PolicyViolationError,
    ScopeViolationError,
    AuditError,
    DecisionError,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── Destructive action helper ─────────────────────────────────────────────

DESTRUCTIVE_ACTIONS = {ACTION_DEPLOY, ACTION_DELETE, ACTION_FINANCIAL}


def _is_destructive(action_type: str) -> bool:
    return action_type in DESTRUCTIVE_ACTIONS


# ── RiskClassifier ────────────────────────────────────────────────────────

class RiskClassifier:
    """Classifies actions into risk levels based on action type and target context."""

    def __init__(self, risk_map: dict[str, str] | None = None) -> None:
        self._risk_map = risk_map or dict(DEFAULT_ACTION_RISK_MAP)

    def classify(self, action_type: str, target: str = "") -> str:
        """Return risk level for an action type. Unknown types raise RiskClassificationError."""
        if action_type not in VALID_ACTION_TYPES:
            raise RiskClassificationError(
                f"Unknown action type: {action_type!r}. Must be one of {sorted(VALID_ACTION_TYPES)}"
            )
        level = self._risk_map.get(action_type, RISK_MEDIUM)
        if level not in VALID_RISK_LEVELS:
            raise RiskClassificationError(f"Mapped risk level {level!r} is not valid")
        return level

    def classify_batch(self, actions: list[tuple[str, str]]) -> list[dict[str, object]]:
        """Classify multiple (action_type, target) pairs. Returns list of dicts with results."""
        results: list[dict[str, object]] = []
        for action_type, target in actions:
            try:
                level = self.classify(action_type, target)
                results.append({"action_type": action_type, "target": target, "risk_level": level, "error": None})
            except RiskClassificationError as exc:
                results.append({"action_type": action_type, "target": target, "risk_level": None, "error": str(exc)})
        return results

    @property
    def risk_map(self) -> dict[str, str]:
        return dict(self._risk_map)


# ── ApprovalPolicyEngine ──────────────────────────────────────────────────

@dataclass
class PolicyEvalResult:
    matched: bool
    policy_id: str | None
    verdict: str
    reason: str
    requires_approval: bool


class ApprovalPolicyEngine:
    """Evaluates an action against a set of approval policies."""

    def __init__(self, policies: list[ApprovalPolicy] | None = None) -> None:
        self._policies: list[ApprovalPolicy] = list(policies or [])

    def add_policy(self, policy: ApprovalPolicy) -> None:
        self._policies.append(policy)

    def evaluate(self, action_type: str, risk_level: str, target: str, actor: str = "system") -> PolicyEvalResult:
        """Evaluate action against registered policies. Returns first matching policy result."""
        for policy in self._policies:
            if risk_level != policy.risk_level:
                continue
            if policy.action_types and action_type not in policy.action_types:
                continue

            if policy.auto_deny:
                return PolicyEvalResult(
                    matched=True,
                    policy_id=policy.policy_id,
                    verdict=VERDICT_DENIED,
                    reason=f"Auto-denied by policy {policy.name!r}",
                    requires_approval=False,
                )

            if policy.requires_approval:
                return PolicyEvalResult(
                    matched=True,
                    policy_id=policy.policy_id,
                    verdict=VERDICT_REQUIRES_APPROVAL,
                    reason=f"Approval required by policy {policy.name!r}",
                    requires_approval=True,
                )

        # No matching policy — default: destructive always requires approval
        if _is_destructive(action_type):
            return PolicyEvalResult(
                matched=False,
                policy_id=None,
                verdict=VERDICT_REQUIRES_APPROVAL,
                reason="Destructive action requires approval (default rule)",
                requires_approval=True,
            )

        return PolicyEvalResult(
            matched=False,
            policy_id=None,
            verdict=VERDICT_APPROVED,
            reason="No matching policy — allowed by default",
            requires_approval=False,
        )

    @property
    def policies(self) -> list[ApprovalPolicy]:
        return list(self._policies)


# ── ScopeGuard ────────────────────────────────────────────────────────────

class ScopeGuard:
    """Guards actions by validating them against allowed and blocked scope rules."""

    def __init__(self, rules: list[ScopeRule] | None = None) -> None:
        self._rules: list[ScopeRule] = list(rules or [])

    def add_rule(self, rule: ScopeRule) -> None:
        self._rules.append(rule)

    def check(self, action_type: str, target: str) -> bool:
        """Check if action is allowed. Returns True if allowed, False if blocked."""
        for rule in self._rules:
            if not rule.enabled:
                continue

            # Check blocked actions
            if rule.blocked_actions and action_type in rule.blocked_actions:
                return False

            # Check blocked paths
            for bp in rule.blocked_paths:
                if target.startswith(bp):
                    return False

            # Check if action is explicitly allowed
            if rule.allowed_actions and action_type in rule.allowed_actions:
                for tp in rule.target_paths:
                    if target.startswith(tp):
                        return True

        # No matching rule — allow by default
        return True

    def check_with_reason(self, action_type: str, target: str) -> tuple[bool, str]:
        """Check if action is allowed. Returns (allowed, reason)."""
        for rule in self._rules:
            if not rule.enabled:
                continue

            if rule.blocked_actions and action_type in rule.blocked_actions:
                return False, f"Action {action_type!r} blocked by scope rule {rule.name!r}"

            for bp in rule.blocked_paths:
                if target.startswith(bp):
                    return False, f"Path {target!r} blocked by scope rule {rule.name!r}"

            if rule.allowed_actions and action_type in rule.allowed_actions:
                for tp in rule.target_paths:
                    if target.startswith(tp):
                        return True, f"Allowed by scope rule {rule.name!r}"

        return True, "No matching scope rule — allowed by default"

    @property
    def rules(self) -> list[ScopeRule]:
        return list(self._rules)


# ── AuditLogPlanner ───────────────────────────────────────────────────────

class AuditLogPlanner:
    """Generates and stores audit events for governance actions."""

    def __init__(self) -> None:
        self._events: list[AuditEvent] = []
        self._decisions: list[GovernanceDecision] = []

    def record_event(
        self,
        action_type: str,
        risk_level: str,
        target: str,
        actor: str,
        verdict: str,
        details: dict[str, object] | None = None,
        approved_by: str | None = None,
    ) -> AuditEvent:
        """Create and store an audit event."""
        event = AuditEvent.new(
            action_type=action_type,
            risk_level=risk_level,
            target=target,
            actor=actor,
            verdict=verdict,
            details=details,
            approved_by=approved_by,
        )
        self._events.append(event)
        return event

    def record_decision(
        self,
        action_type: str,
        risk_level: str,
        target: str,
        verdict: str,
        reason: str,
        policy_id: str | None = None,
        audit_event_id: str | None = None,
    ) -> GovernanceDecision:
        """Create and store a governance decision."""
        decision = GovernanceDecision.new(
            action_type=action_type,
            risk_level=risk_level,
            target=target,
            verdict=verdict,
            reason=reason,
            policy_id=policy_id,
            audit_event_id=audit_event_id,
        )
        self._decisions.append(decision)
        return decision

    def get_events_by_risk(self, risk_level: str) -> list[AuditEvent]:
        """Filter audit events by risk level."""
        return [e for e in self._events if e.risk_level == risk_level]

    def get_events_by_action(self, action_type: str) -> list[AuditEvent]:
        """Filter audit events by action type."""
        return [e for e in self._events if e.action_type == action_type]

    def get_decisions_by_verdict(self, verdict: str) -> list[GovernanceDecision]:
        """Filter decisions by verdict."""
        return [d for d in self._decisions if d.verdict == verdict]

    def generate_audit_log(self) -> list[dict[str, object]]:
        """Generate a full audit log as a list of dicts merging events and decisions."""
        log: list[dict[str, object]] = []
        for event in self._events:
            entry = event.to_dict()
            matching_decisions = [d for d in self._decisions if d.audit_event_id == event.event_id]
            entry["decisions"] = [d.to_dict() for d in matching_decisions]
            log.append(entry)
        return log

    @property
    def events(self) -> list[AuditEvent]:
        return list(self._events)

    @property
    def decisions(self) -> list[GovernanceDecision]:
        return list(self._decisions)

    @property
    def event_count(self) -> int:
        return len(self._events)

    @property
    def decision_count(self) -> int:
        return len(self._decisions)
