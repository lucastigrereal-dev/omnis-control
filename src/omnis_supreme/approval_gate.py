"""P20 OMNIS Supreme Activation — Approval gate (thin P18 bridge)."""
from __future__ import annotations

from src.governance.models import (
    ApprovalPolicy,
    GovernanceDecision,
    RISK_LOW,
    RISK_MEDIUM,
    RISK_HIGH,
    ACTION_SEND,
    ACTION_WRITE,
    VERDICT_APPROVED,
    VERDICT_REQUIRES_APPROVAL,
)
from src.governance.service import RiskClassifier, ApprovalPolicyEngine
from src.omnis_supreme.models import SupremePlan, _now_iso


class SupremeApprovalGate:
    """Two-gate approval bridge: pre-execution (plan) and pre-delivery (send)."""

    def __init__(self):
        self._risk = RiskClassifier()
        self._engine = ApprovalPolicyEngine()
        self._register_defaults()

    def _register_defaults(self) -> None:
        self._engine.add_policy(ApprovalPolicy.new(
            name="execution-gate", risk_level=RISK_HIGH,
            action_types=[ACTION_WRITE], requires_approval=True,
            description="High-risk write operations require human approval",
        ))
        self._engine.add_policy(ApprovalPolicy.new(
            name="delivery-gate", risk_level=RISK_HIGH,
            action_types=[ACTION_SEND], requires_approval=True,
            description="SEND actions require explicit approval",
        ))

    def submit(self, plan: SupremePlan, dry_run_result: dict) -> GovernanceDecision:
        risk = self._assess_plan_risk(plan, dry_run_result)
        target = f"supreme://missions/{plan.mission_id}"
        result = self._engine.evaluate(ACTION_WRITE, risk, target, actor="supreme")
        return GovernanceDecision.new(
            action_type=ACTION_WRITE, risk_level=risk, target=target,
            verdict=result.verdict, reason=result.reason, policy_id=result.policy_id,
        )

    def gate_delivery(self, plan: SupremePlan, dry_run_result: dict) -> GovernanceDecision:
        target = f"supreme://missions/{plan.mission_id}/delivery"
        result = self._engine.evaluate(ACTION_SEND, RISK_HIGH, target, actor="supreme")
        return GovernanceDecision.new(
            action_type=ACTION_SEND, risk_level=RISK_HIGH, target=target,
            verdict=result.verdict, reason=result.reason, policy_id=result.policy_id,
        )

    def _assess_plan_risk(self, plan: SupremePlan, dry_run_result: dict) -> str:
        steps = dry_run_result.get("steps", [])
        blocked = [s for s in steps if s.get("status") == "dry_blocked"]
        if blocked:
            return RISK_HIGH
        if len(plan.steps) > 3:
            return RISK_MEDIUM
        return RISK_LOW
