from src.approval_runtime.policy import ApprovalPolicy
from src.approval_runtime.models import (
    ApprovalRequest,
    ApprovalStatus,
    RiskLevel,
)


class TestApprovalPolicy:
    def test_low_non_destructive_auto_approve(self):
        policy = ApprovalPolicy()
        req = ApprovalRequest(risk=RiskLevel.LOW, is_destructive=False)
        decision = policy.evaluate(req)
        assert decision.status == ApprovalStatus.AUTO_APPROVED
        assert decision.requires_human is False
        assert decision.requires_dry_run is False

    def test_low_destructive_needs_human(self):
        policy = ApprovalPolicy()
        req = ApprovalRequest(risk=RiskLevel.LOW, is_destructive=True)
        decision = policy.evaluate(req)
        assert decision.requires_human is True

    def test_medium_needs_approval(self):
        policy = ApprovalPolicy()
        req = ApprovalRequest(risk=RiskLevel.MEDIUM, is_destructive=False)
        decision = policy.evaluate(req)
        assert decision.requires_human is True
        assert decision.requires_dry_run is False

    def test_medium_destructive_requires_dry_run(self):
        policy = ApprovalPolicy()
        req = ApprovalRequest(risk=RiskLevel.MEDIUM, is_destructive=True)
        decision = policy.evaluate(req)
        assert decision.requires_human is True
        assert decision.requires_dry_run is True

    def test_high_requires_dry_run_and_approval(self):
        policy = ApprovalPolicy()
        req = ApprovalRequest(risk=RiskLevel.HIGH, is_destructive=False)
        decision = policy.evaluate(req)
        assert decision.requires_human is True
        assert decision.requires_dry_run is True

    def test_critical_requires_everything(self):
        policy = ApprovalPolicy()
        req = ApprovalRequest(risk=RiskLevel.CRITICAL, is_destructive=True)
        decision = policy.evaluate(req)
        assert decision.requires_human is True
        assert decision.requires_dry_run is True
        assert decision.requires_documented_reason is True
