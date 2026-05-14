"""P27 ApprovalChain — bridge to P18 Governance for action approval."""
from typing import Optional

from src.real_world_actions.models import (
    ActionDefinition, ActionRequest,
    RISK_LOW, RISK_MEDIUM, RISK_HIGH, RISK_CRITICAL,
)
from src.real_world_actions.errors import ActionDeniedError

# P18 contracts used by the approval chain
from src.governance.models import (
    AuditEvent, GovernanceDecision, ApprovalPolicy,
    VERDICT_APPROVED, VERDICT_DENIED, VERDICT_REQUIRES_APPROVAL,
)
from src.governance.service import ApprovalPolicyEngine, PolicyEvalResult

_ACTOR = "omnis-p27"

_AUTO_APPROVE_RISKS = {RISK_LOW, RISK_MEDIUM}


class ApprovalChain:
    """Bridge between P27 actions and P18 Governance.

    Low/medium risk: auto-approved with audit log.
    High risk: requires 1 approval.
    Critical risk: requires double confirmation.
    """

    def __init__(self, policy_engine: Optional[ApprovalPolicyEngine] = None):
        self._engine = policy_engine or ApprovalPolicyEngine()
        self._pending: dict[str, ActionRequest] = {}
        self._decisions: list[GovernanceDecision] = []
        self._events: list[AuditEvent] = []
        self._seed_policies()

    def _seed_policies(self) -> None:
        """Register default P27 action-approval policies in the engine."""
        self._engine.add_policy(ApprovalPolicy.new(
            "p27-high-risk-approval", RISK_HIGH, requires_approval=True,
            description="High-risk actions (send) require operator approval",
        ))
        self._engine.add_policy(ApprovalPolicy.new(
            "p27-critical-risk-approval", RISK_CRITICAL, requires_approval=True,
            description="Critical actions (deploy, financial, delete) require double confirmation",
        ))

    # ── Core: evaluate action ────────────────────────────────────

    def evaluate(self, action: ActionDefinition, params: dict,
                 request_id: str = "", mission_id: str = "") -> GovernanceDecision:
        """Evaluate an action against governance policies. Returns decision with verdict."""
        result = self._engine.evaluate(
            action_type=action.action_type,
            risk_level=action.risk_level,
            target=action.name,
        )

        decision = GovernanceDecision.new(
            action_type=action.action_type,
            risk_level=action.risk_level,
            target=action.name,
            verdict=self._map_verdict(action, result),
            reason=result.reason,
        )
        self._decisions.append(decision)
        return decision

    def _map_verdict(self, action: ActionDefinition, result: PolicyEvalResult) -> str:
        if result.verdict == VERDICT_DENIED:
            return VERDICT_DENIED
        if result.requires_approval:
            return VERDICT_REQUIRES_APPROVAL
        if action.risk_level in _AUTO_APPROVE_RISKS:
            return VERDICT_APPROVED
        return VERDICT_APPROVED

    # ── Helpers ──────────────────────────────────────────────────

    def _make_event(self, action: ActionDefinition, verdict: str,
                    details: Optional[dict] = None, approved_by: Optional[str] = None) -> AuditEvent:
        return AuditEvent.new(
            action_type=action.action_type,
            risk_level=action.risk_level,
            target=action.name,
            actor=_ACTOR,
            verdict=verdict,
            details=details or {},
            approved_by=approved_by,
        )

    # ── Approval flow ────────────────────────────────────────────

    def request_approval(self, action: ActionDefinition, params: dict,
                         request_id: str = "", mission_id: str = "") -> GovernanceDecision:
        """Request approval for an action. If risk is low/medium, auto-approves."""
        decision = self.evaluate(action, params, request_id, mission_id)

        if decision.verdict == VERDICT_REQUIRES_APPROVAL:
            req = ActionRequest.new(action.action_id, params, mission_id=mission_id)
            self._pending[req.request_id] = req
            event = self._make_event(action, VERDICT_REQUIRES_APPROVAL,
                                     {"params": params, "request_id": req.request_id})
            self._events.append(event)
            decision.audit_event_id = event.event_id

        if decision.verdict == VERDICT_APPROVED:
            event = self._make_event(action, VERDICT_APPROVED,
                                     {"params": params, "auto_approved": True})
            self._events.append(event)
            decision.audit_event_id = event.event_id

        if decision.verdict == VERDICT_DENIED:
            event = self._make_event(action, VERDICT_DENIED,
                                     {"params": params, "reason": decision.reason})
            self._events.append(event)
            decision.audit_event_id = event.event_id

        return decision

    # ── Manual approval / denial ─────────────────────────────────

    def approve(self, request_id: str, approved_by: str = "operator",
                reason: str = "") -> GovernanceDecision:
        """Manually approve a pending action request."""
        self._pending.pop(request_id, None)

        decision = GovernanceDecision.new(
            action_type="send",
            risk_level=RISK_HIGH,
            target=request_id,
            verdict=VERDICT_APPROVED,
            reason=f"Approved by {approved_by}" + (f": {reason}" if reason else ""),
        )
        event = AuditEvent.new(
            action_type="send", risk_level=RISK_HIGH, target=request_id,
            actor=_ACTOR, verdict=VERDICT_APPROVED,
            details={"approved_by": approved_by, "reason": reason},
            approved_by=approved_by,
        )
        self._events.append(event)
        decision.audit_event_id = event.event_id
        self._decisions.append(decision)
        return decision

    def deny(self, request_id: str, reason: str = "") -> GovernanceDecision:
        """Deny a pending action request."""
        self._pending.pop(request_id, None)
        decision = GovernanceDecision.new(
            action_type="send", risk_level=RISK_HIGH, target=request_id,
            verdict=VERDICT_DENIED, reason=reason,
        )
        event = AuditEvent.new(
            action_type="send", risk_level=RISK_HIGH, target=request_id,
            actor=_ACTOR, verdict=VERDICT_DENIED, details={"reason": reason},
        )
        self._events.append(event)
        decision.audit_event_id = event.event_id
        self._decisions.append(decision)
        return decision

    # ── Queries ──────────────────────────────────────────────────

    def get_pending(self) -> list[ActionRequest]:
        return list(self._pending.values())

    def get_decisions(self) -> list[GovernanceDecision]:
        return list(self._decisions)

    def get_events(self) -> list[AuditEvent]:
        return list(self._events)

    def is_auto_approved(self, action: ActionDefinition) -> bool:
        return action.risk_level in _AUTO_APPROVE_RISKS

    @property
    def pending_count(self) -> int:
        return len(self._pending)
