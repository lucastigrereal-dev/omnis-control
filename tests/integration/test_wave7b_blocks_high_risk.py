"""P45: HIGH/CRITICAL orders must be blocked without explicit approval."""

import tempfile
from pathlib import Path

from src.runtime_orchestrator.service import OrchestratorService
from src.approval_runtime.policy import ApprovalPolicy
from src.approval_runtime.models import ApprovalRequest, RiskLevel, ApprovalStatus


class TestBlocksHighRisk:
    def test_high_risk_requires_approval_in_orchestrator(self):
        """HIGH risk order: orchestrator flags requires_approval=True."""
        svc = OrchestratorService(dry_run=True)
        result = svc.run({
            "order_id": "wro_high",
            "risk": "HIGH",
        })
        assert result.status.value == "COMPLETED"  # pipeline completes in dry_run
        step_outputs = {s.name: s.output_data for s in result.steps if s.output_data}
        risk_eval = step_outputs.get("evaluate_risk", {})
        assert risk_eval.get("requires_approval") is True
        assert risk_eval.get("risk") == "HIGH"

    def test_critical_risk_requires_approval_in_orchestrator(self):
        """CRITICAL risk order: orchestrator flags requires_approval=True."""
        svc = OrchestratorService(dry_run=True)
        result = svc.run({
            "order_id": "wro_crit",
            "risk": "CRITICAL",
        })
        step_outputs = {s.name: s.output_data for s in result.steps if s.output_data}
        risk_eval = step_outputs.get("evaluate_risk", {})
        assert risk_eval.get("requires_approval") is True
        assert risk_eval.get("risk") == "CRITICAL"

    def test_low_risk_does_not_require_approval_in_orchestrator(self):
        """LOW risk order: auto-approved, no approval required."""
        svc = OrchestratorService(dry_run=True)
        result = svc.run({
            "order_id": "wro_low",
            "risk": "LOW",
        })
        step_outputs = {s.name: s.output_data for s in result.steps if s.output_data}
        risk_eval = step_outputs.get("evaluate_risk", {})
        assert risk_eval.get("requires_approval") is False

    def test_approval_policy_high_risk_pending(self):
        """Policy evaluates HIGH → PENDING + requires_human."""
        policy = ApprovalPolicy(dry_run=True)
        request = ApprovalRequest(risk=RiskLevel.HIGH, is_destructive=False)
        decision = policy.evaluate(request)
        assert decision.status == ApprovalStatus.PENDING
        assert decision.requires_human is True
        assert decision.requires_dry_run is True

    def test_approval_policy_critical_requires_documented_reason(self):
        """Policy evaluates CRITICAL → PENDING + requires_documented_reason."""
        policy = ApprovalPolicy(dry_run=True)
        request = ApprovalRequest(risk=RiskLevel.CRITICAL, is_destructive=False)
        decision = policy.evaluate(request)
        assert decision.status == ApprovalStatus.PENDING
        assert decision.requires_documented_reason is True

    def test_approval_policy_low_non_destructive_auto(self):
        """LOW non-destructive → AUTO_APPROVED."""
        policy = ApprovalPolicy(dry_run=True)
        request = ApprovalRequest(risk=RiskLevel.LOW, is_destructive=False)
        decision = policy.evaluate(request)
        assert decision.status == ApprovalStatus.AUTO_APPROVED
        assert decision.requires_human is False

    def test_approval_policy_medium_destructive_requires_dry_run(self):
        """MEDIUM destructive → PENDING + requires_dry_run."""
        policy = ApprovalPolicy(dry_run=True)
        request = ApprovalRequest(risk=RiskLevel.MEDIUM, is_destructive=True)
        decision = policy.evaluate(request)
        assert decision.status == ApprovalStatus.PENDING
        assert decision.requires_dry_run is True

    def test_pipeline_approval_step_reflects_required(self):
        """Check_approval step shows PENDING when approval required."""
        svc = OrchestratorService(dry_run=True)
        result = svc.run({
            "order_id": "wro_needs_approval",
            "risk": "CRITICAL",
        })
        step_outputs = {s.name: s.output_data for s in result.steps if s.output_data}
        approval = step_outputs.get("check_approval", {})
        assert approval.get("approval") == "PENDING"
