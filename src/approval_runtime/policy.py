from src.approval_runtime.models import (
    ApprovalRequest,
    ApprovalDecision,
    ApprovalStatus,
    RiskLevel,
    _now_iso,
    _new_id,
)


class ApprovalPolicy:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run

    def evaluate(self, request: ApprovalRequest) -> ApprovalDecision:
        decision = ApprovalDecision(
            request_id=request.request_id,
        )

        if request.risk == RiskLevel.CRITICAL:
            decision.status = ApprovalStatus.PENDING
            decision.requires_human = True
            decision.requires_dry_run = True
            decision.requires_documented_reason = True
            decision.message = "CRITICAL: requires human approval with documented reason and dry-run"
        elif request.risk == RiskLevel.HIGH:
            decision.status = ApprovalStatus.PENDING
            decision.requires_human = True
            decision.requires_dry_run = True
            decision.message = "HIGH: requires human approval with dry-run"
        elif request.risk == RiskLevel.MEDIUM:
            if request.is_destructive:
                decision.status = ApprovalStatus.PENDING
                decision.requires_human = True
                decision.requires_dry_run = True
                decision.message = "MEDIUM destructive: requires human approval with dry-run"
            else:
                decision.status = ApprovalStatus.PENDING
                decision.requires_human = True
                decision.requires_dry_run = False
                decision.message = "MEDIUM: requires human approval"
        else:
            if request.is_destructive:
                decision.status = ApprovalStatus.PENDING
                decision.requires_human = True
                decision.message = "LOW destructive: requires human approval"
            else:
                decision.status = ApprovalStatus.AUTO_APPROVED
                decision.requires_human = False
                decision.requires_dry_run = False
                decision.decided_at = _now_iso()
                decision.decided_by = "auto"
                decision.message = "LOW non-destructive: auto-approved"

        if self.dry_run and decision.requires_human:
            decision.message += " [DRY_RUN: approval simulated]"

        return decision
