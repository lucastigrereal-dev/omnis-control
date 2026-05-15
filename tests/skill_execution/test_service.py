from src.skill_execution.request import SkillExecutionRequest, SkillExecutionRisk
from src.skill_execution.service import SkillExecutionService
from src.skill_execution.result import ExecutionStatus


class TestSkillExecutionService:
    def test_safe_execution_flow(self):
        svc = SkillExecutionService(dry_run=True)
        req = SkillExecutionRequest(skill_id="seogram", intent="Generate caption", risk_level=SkillExecutionRisk.LOW)
        result = svc.execute(req)
        assert result.status == ExecutionStatus.DRY_RUN_OK
        assert svc.events.event_count >= 2

    def test_critical_blocked(self):
        svc = SkillExecutionService(dry_run=True)
        req = SkillExecutionRequest(skill_id="deploy", intent="deploy production", risk_level=SkillExecutionRisk.CRITICAL)
        result = svc.execute(req)
        assert result.status == ExecutionStatus.BLOCKED

    def test_high_requires_approval(self):
        svc = SkillExecutionService(dry_run=True)
        req = SkillExecutionRequest(skill_id="shell_exec", intent="run script", risk_level=SkillExecutionRisk.HIGH)
        result = svc.execute(req)
        assert result.status == ExecutionStatus.NEEDS_APPROVAL

    def test_events_emitted_for_safe_execution(self):
        svc = SkillExecutionService(dry_run=True)
        req = SkillExecutionRequest(skill_id="x", intent="y", risk_level=SkillExecutionRisk.LOW)
        svc.execute(req)
        types = [e.event_type.value for e in svc.events.query()]
        assert "REQUEST_RECEIVED" in types
        assert "EXECUTION_COMPLETED" in types

    def test_events_for_blocked_execution(self):
        svc = SkillExecutionService(dry_run=True)
        req = SkillExecutionRequest(skill_id="d", intent="deploy_production", risk_level=SkillExecutionRisk.CRITICAL)
        svc.execute(req)
        types = [e.event_type.value for e in svc.events.query()]
        assert "EXECUTION_BLOCKED" in types

    def test_artifacts_registered(self):
        svc = SkillExecutionService(dry_run=True)
        req = SkillExecutionRequest(skill_id="seogram", intent="test", risk_level=SkillExecutionRisk.LOW)
        result = svc.execute(req)
        artifacts = svc.artifacts.get_by_result(result.result_id)
        assert len(artifacts) >= 1
