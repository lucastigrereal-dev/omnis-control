from src.skill_execution.request import SkillExecutionRequest, SkillExecutionRisk
from src.skill_execution.dryrun_executor import DryRunExecutor
from src.skill_execution.result import ExecutionStatus


class TestDryRunExecutor:
    def test_execute_dryrun(self):
        executor = DryRunExecutor()
        req = SkillExecutionRequest(skill_id="seogram", intent="Generate SEO caption")
        result = executor.execute(req)
        assert result.status == ExecutionStatus.DRY_RUN_OK
        assert "seogram" in result.summary

    def test_execute_not_dryrun_blocked(self):
        executor = DryRunExecutor(dry_run=False)
        req = SkillExecutionRequest(skill_id="seogram", intent="test")
        result = executor.execute(req)
        assert result.status == ExecutionStatus.BLOCKED

    def test_history_tracks_executions(self):
        executor = DryRunExecutor()
        r1 = SkillExecutionRequest(skill_id="a", intent="ia", risk_level=SkillExecutionRisk.LOW)
        r2 = SkillExecutionRequest(skill_id="b", intent="ib", risk_level=SkillExecutionRisk.LOW)
        executor.execute(r1)
        executor.execute(r2)
        assert executor.execution_count == 2
        assert len(executor.history) == 2

    def test_payload_echoed_in_artifacts(self):
        executor = DryRunExecutor()
        req = SkillExecutionRequest(skill_id="test", payload={"key": "val"})
        result = executor.execute(req)
        assert len(result.artifacts) > 0
        assert result.artifacts[0]["echo"] == {"key": "val"}

    def test_logs_generated(self):
        executor = DryRunExecutor()
        req = SkillExecutionRequest(skill_id="x", intent="y", risk_level=SkillExecutionRisk.MEDIUM)
        result = executor.execute(req)
        assert len(result.logs) >= 3
