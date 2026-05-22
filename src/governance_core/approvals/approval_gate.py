"""Single canonical approval gate for the OMNIS ecosystem.

Replaces 9 parallel approval systems:
  1. OMNIS Approval Center (JSONL store, no tokens)
  2. OMNIS Approval Runtime (in-memory dict, UUID tokens)
  3. KRATOS Approval Service (in-memory list, REST CRUD)
  4. Remote Control Approval (ChallengeEngine, Token+TTL)
  5. Content Factory ApprovalFlow (5 stages)
  6. Caption Approval Gate (PreApprovalResult)
  7. Publisher Approval Gate (CaptionApproval)
  8. Supreme Approval Gate (SupremeApprovalGate)
  9. Real World Actions ApprovalChain (chain pattern)

Single chain:
  Risk Classify → Policy Evaluate → Approve/Deny/Escalate → Audit Log
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from ..policies.risk_taxonomy import get_level, requires_human_slot, is_auto_approved
from ..risks.risk_classifier import classify_action


class ApprovalDecision(str, Enum):
    APPROVED = "approved"
    DENIED = "denied"
    ESCALATED = "escalated"
    PENDING_HUMAN = "pending_human"


@dataclass
class ApprovalRequest:
    action: str
    context: dict = field(default_factory=dict)
    request_id: str = field(default_factory=lambda: f"apr-{uuid.uuid4().hex[:8]}")
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ApprovalResult:
    request_id: str
    decision: ApprovalDecision
    risk_level: int
    risk_name: str
    reason: str
    requires_human: bool
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ApprovalGate:
    """Single canonical approval gate.

    Usage:
        gate = ApprovalGate()
        result = gate.evaluate(ApprovalRequest(action="write file.py", context={...}))
        if result.decision == ApprovalDecision.APPROVED:
            execute()
    """

    def __init__(self, audit_log=None):
        self._audit_log = audit_log

    def evaluate(self, request: ApprovalRequest) -> ApprovalResult:
        """Evaluate an action through the canonical approval chain.

        1. Risk Classify → ABA 4 L0-L5
        2. Policy Evaluate → check policies, permissions, manifests
        3. Approve/Deny/Escalate
        4. Audit → log decision
        """
        # Step 1: Risk classify
        classification = classify_action(request.action)
        level = classification["level"]

        # Step 2: Policy evaluate (expandable — currently: risk taxonomy)
        # Future: check permissions, manifests, contracts

        # Step 3: Approve/Deny/Escalate
        if is_auto_approved(level):
            decision = ApprovalDecision.APPROVED
            reason = f"Auto-approved: L{level} ({classification['name']}) — {classification['description']}"
        elif requires_human_slot(level):
            decision = ApprovalDecision.PENDING_HUMAN
            reason = f"Human Slot required: L{level} ({classification['name']}) — {classification['description']}"
        else:
            # L3: deny by default, allow with explicit approval or dry_run
            decision = ApprovalDecision.DENIED
            reason = f"Auto-denied: L{level} ({classification['name']}) — requires review or dry_run"

        result = ApprovalResult(
            request_id=request.request_id,
            decision=decision,
            risk_level=level,
            risk_name=classification["name"],
            reason=reason,
            requires_human=requires_human_slot(level),
        )

        # Step 4: Audit
        if self._audit_log:
            self._audit_log.log(request, result)

        return result

    def override_approve(self, request: ApprovalRequest, reason: str) -> ApprovalResult:
        """Manual override: approve a previously denied/escalated request."""
        classification = classify_action(request.action)
        result = ApprovalResult(
            request_id=request.request_id,
            decision=ApprovalDecision.APPROVED,
            risk_level=classification["level"],
            risk_name=classification["name"],
            reason=f"MANUAL OVERRIDE: {reason}",
            requires_human=False,
        )
        if self._audit_log:
            self._audit_log.log(request, result, override=True)
        return result
