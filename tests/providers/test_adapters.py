"""Tests for provider adapters — runtime_orchestrator + mission_orchestrator via WorkflowProvider."""
import pytest
from src.providers.adapters import runtime_orchestrator_as_workflow, mission_plan_as_workflow
from src.providers.workflow import SequentialWorkflowProvider, WorkflowResult


class TestRuntimeOrchestratorAdapter:
    def test_dry_run_returns_workflow_result(self):
        result = runtime_orchestrator_as_workflow(
            {"order_id": "test-001", "risk": "LOW"},
            dry_run=True,
        )
        assert isinstance(result, WorkflowResult)

    def test_dry_run_completes_all_9_steps(self):
        result = runtime_orchestrator_as_workflow(
            {"order_id": "test-001"},
            dry_run=True,
        )
        assert result.steps_total == 9
        assert result.steps_completed == 9

    def test_dry_run_does_not_execute_real_steps(self):
        result = runtime_orchestrator_as_workflow(
            {"order_id": "test-001", "risk": "CRITICAL"},
            dry_run=True,
        )
        # dry_run=True should not fail on CRITICAL risk
        assert result.success

    def test_real_run_executes_all_steps(self):
        result = runtime_orchestrator_as_workflow(
            {"order_id": "test-002", "risk": "LOW"},
            dry_run=False,
        )
        assert result.steps_completed == 9
        assert "parse_order" in result.outputs
        assert result.outputs["parse_order"]["parsed"] is True

    def test_real_run_passes_state(self):
        result = runtime_orchestrator_as_workflow(
            {"order_id": "myorder"},
            dry_run=False,
        )
        assert result.outputs["parse_order"]["order_id"] == "myorder"

    def test_custom_provider(self):
        provider = SequentialWorkflowProvider()
        result = runtime_orchestrator_as_workflow(
            {"order_id": "x"},
            dry_run=True,
            provider=provider,
        )
        assert result.success

    def test_result_has_workflow_id(self):
        result = runtime_orchestrator_as_workflow({}, dry_run=True)
        assert isinstance(result.workflow_id, str) and len(result.workflow_id) > 0


class TestMissionPlanAdapter:
    def test_dry_run_returns_workflow_result(self):
        result = mission_plan_as_workflow(
            "Criar post para @lucastigrereal sobre gastronomia",
            dry_run=True,
        )
        assert isinstance(result, WorkflowResult)

    def test_dry_run_completes_2_steps(self):
        result = mission_plan_as_workflow("request text", dry_run=True)
        assert result.steps_total == 2
        assert result.steps_completed == 2

    def test_real_run_executes_plan(self):
        result = mission_plan_as_workflow(
            "Criar post sobre viagem",
            account_handle="lucastigrereal",
            dry_run=False,
        )
        assert result.steps_completed >= 1
        assert "plan" in result.outputs

    def test_success(self):
        result = mission_plan_as_workflow("test", dry_run=True)
        assert result.success
