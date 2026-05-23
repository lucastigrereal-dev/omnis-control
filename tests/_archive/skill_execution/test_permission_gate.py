from src.skill_execution.request import SkillExecutionRequest, SkillExecutionRisk
from src.skill_execution.permission_gate import PermissionGate
from src.skill_execution.result import ExecutionStatus


class TestPermissionGate:
    def test_low_risk_passes(self):
        gate = PermissionGate()
        req = SkillExecutionRequest(skill_id="seogram", risk_level=SkillExecutionRisk.LOW)
        result = gate.evaluate(req)
        assert result.status == ExecutionStatus.DRY_RUN_OK

    def test_critical_blocked(self):
        gate = PermissionGate()
        req = SkillExecutionRequest(skill_id="deploy", risk_level=SkillExecutionRisk.CRITICAL)
        result = gate.evaluate(req)
        assert result.status == ExecutionStatus.BLOCKED

    def test_high_requires_approval(self):
        gate = PermissionGate()
        req = SkillExecutionRequest(skill_id="shell", risk_level=SkillExecutionRisk.HIGH)
        result = gate.evaluate(req)
        assert result.status == ExecutionStatus.NEEDS_APPROVAL

    def test_forbidden_action_blocked(self):
        gate = PermissionGate()
        req = SkillExecutionRequest(skill_id="rm", intent="rm_rf /tmp", risk_level=SkillExecutionRisk.LOW)
        result = gate.evaluate(req)
        assert result.status == ExecutionStatus.BLOCKED

    def test_deploy_blocked(self):
        gate = PermissionGate()
        req = SkillExecutionRequest(skill_id="deploy", intent="deploy to production", risk_level=SkillExecutionRisk.LOW)
        result = gate.evaluate(req)
        assert result.status == ExecutionStatus.BLOCKED

    def test_forbidden_zone_detected(self):
        gate = PermissionGate()
        req = SkillExecutionRequest(
            skill_id="reader",
            intent="read file",
            risk_level=SkillExecutionRisk.LOW,
            forbidden_paths=[".env", "secrets/key.pem"],
        )
        result = gate.evaluate(req)
        assert result.status == ExecutionStatus.BLOCKED

    def test_safe_skill_passes(self):
        gate = PermissionGate()
        req = SkillExecutionRequest(
            skill_id="seogram",
            intent="Generate SEO caption",
            risk_level=SkillExecutionRisk.LOW,
            allowed_paths=["src/content/"],
        )
        result = gate.evaluate(req)
        assert result.status == ExecutionStatus.DRY_RUN_OK

    def test_custom_forbidden(self):
        gate = PermissionGate()
        gate.add_forbidden("experimental_destroy")
        req = SkillExecutionRequest(
            skill_id="test",
            intent="experimental_destroy",
            risk_level=SkillExecutionRisk.LOW,
        )
        result = gate.evaluate(req)
        assert result.status == ExecutionStatus.BLOCKED

    def test_medium_no_dryrun_needs_approval(self):
        gate = PermissionGate()
        req = SkillExecutionRequest(skill_id="migration", risk_level=SkillExecutionRisk.MEDIUM, dry_run=False)
        result = gate.evaluate(req)
        assert result.status == ExecutionStatus.NEEDS_APPROVAL
