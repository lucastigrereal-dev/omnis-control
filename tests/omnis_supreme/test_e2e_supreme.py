"""End-to-end tests for P20 Supreme mission flows."""
from __future__ import annotations

import pytest

from src.omnis_supreme.errors import (
    UnknownIntentError,
    PlanError,
    StepAdapterError,
    ExecutionError,
)
from src.omnis_supreme.models import (
    SupremeMission,
    SupremePlan,
    SupremeStatus,
    SupremeStep,
)
from src.omnis_supreme.service import (
    SupremeOrchestrator,
    SupremeIntake,
    SupremeContextBuilder,
    SupremePlanner,
    SupremeExecutor,
    ExecutionResult,
)
from src.omnis_supreme.adapters import ADAPTER_REGISTRY


class TestIntakeToPlanFlow:
    def test_intake_classify_publish(self):
        orch = SupremeOrchestrator(dry_run=True)
        mission = orch.intake.parse("publicar conteúdo no feed")
        assert mission.intent == "publish_content"
        assert mission.status == SupremeStatus.INTAKE

    def test_intake_classify_analyze(self):
        orch = SupremeOrchestrator(dry_run=True)
        mission = orch.intake.parse("analisar métricas")
        assert mission.intent == "analyze_performance"

    def test_intake_unknown_raises(self):
        intake = SupremeIntake()
        with pytest.raises(UnknownIntentError):
            intake.parse("xyz unknown request 12345")


class TestPlanToExecutionFlow:
    def test_plan_has_correct_step_count(self):
        planner = SupremePlanner()
        mission = SupremeMission.new(request_text="test", intent="deliver_to_client")
        plan = planner.plan(mission)
        assert len(plan.steps) == 1
        assert plan.steps[0].module_ref == "P17"

    def test_plan_selected_modules_unique(self):
        planner = SupremePlanner()
        mission = SupremeMission.new(request_text="test", intent="create_campaign")
        plan = planner.plan(mission)
        assert len(plan.selected_modules) == len(set(plan.selected_modules))

    def test_dry_run_on_publish_pipeline(self):
        planner = SupremePlanner()
        executor = SupremeExecutor(dry_run=True)
        mission = SupremeMission.new(request_text="test", intent="publish_content")
        plan = planner.plan(mission)
        result = executor.dry_run(plan)
        assert isinstance(result, dict)
        assert result["status"] == "dry_complete"

    def test_dry_run_on_full_campaign_pipeline(self):
        planner = SupremePlanner()
        executor = SupremeExecutor(dry_run=True)
        mission = SupremeMission.new(request_text="test", intent="create_campaign")
        plan = planner.plan(mission)
        result = executor.dry_run(plan)
        assert result["status"] == "dry_complete"
        assert len(result["steps"]) == 7


class TestCycleDetection:
    def test_topological_sort_detects_cycle(self):
        planner = SupremePlanner()
        s1 = SupremeStep.new(module_ref="P5", operation="a")
        s2 = SupremeStep.new(module_ref="P19", operation="b")
        edges = [(s1.step_id, s2.step_id), (s2.step_id, s1.step_id)]
        with pytest.raises(PlanError, match="Cycle"):
            planner._topological_sort([s1, s2], edges)

    def test_topological_sort_three_node_diamond(self):
        planner = SupremePlanner()
        s1 = SupremeStep.new(module_ref="P5", operation="a")
        s2 = SupremeStep.new(module_ref="P19", operation="b")
        s3 = SupremeStep.new(module_ref="P8", operation="c")
        edges = [(s1.step_id, s2.step_id), (s1.step_id, s3.step_id)]
        result = planner._topological_sort([s1, s2, s3], edges)
        assert len(result) == 3
        assert result[0].step_id == s1.step_id


class TestAdapterMissing:
    def test_execute_step_missing_adapter_raises(self):
        executor = SupremeExecutor(dry_run=True)
        step = SupremeStep.new(module_ref="P99", operation="ghost_op")
        with pytest.raises(StepAdapterError, match="P99"):
            executor.execute_step(step, {})


class TestDryRunBlocking:
    def test_orchestrator_dry_run_stops_before_execution(self):
        orch = SupremeOrchestrator(dry_run=True)
        mission = orch.run("publicar conteúdo")
        assert mission.status == SupremeStatus.DRY_RUN
        assert "steps" in mission.execution

    def test_dry_run_simulates_without_module_calls(self):
        executor = SupremeExecutor(dry_run=True)
        mission = SupremeMission.new(request_text="test", intent="publish_content")
        planner = SupremePlanner()
        plan = planner.plan(mission)
        result = executor.dry_run(plan)
        for step in result["steps"]:
            assert step["status"] == "dry_ok"


class TestDifferentIntents:
    def test_commercial_outreach_pipeline(self):
        orch = SupremeOrchestrator(dry_run=True)
        mission = orch.run("fazer prospecção de leads no interior de SP")
        assert mission.intent == "commercial_outreach"
        plan = mission.plan
        assert len(plan.steps) == 2

    def test_deliver_to_client_pipeline(self):
        orch = SupremeOrchestrator(dry_run=True)
        mission = orch.run("entregar material ao cliente")
        assert mission.intent == "deliver_to_client"
        plan = mission.plan
        assert len(plan.steps) == 1
        assert plan.steps[0].module_ref == "P17"


class TestExecutionResult:
    def test_execution_result_new(self):
        result = ExecutionResult.new(mission_id="spr_test", dry_run=True)
        assert result.mission_id == "spr_test"
        assert result.dry_run is True
        assert result.started_at != ""

    def test_execution_result_to_dict(self):
        result = ExecutionResult.new(mission_id="spr_test")
        d = result.to_dict()
        assert d["mission_id"] == "spr_test"
        assert d["status"] == "pending"
        assert d["dry_run"] is True


class TestRetryBehavior:
    def test_execute_step_uses_registry(self):
        executor = SupremeExecutor(dry_run=True)
        step = SupremeStep.new(module_ref="P8", operation="validate_publish_readiness")
        result = executor.execute_step(step, {})
        assert result["status"] == "ok"
        assert "output" in result

    def test_retry_counter_on_step(self):
        step = SupremeStep.new(module_ref="P5", operation="build_campaign_brief")
        assert step.retry_attempt == 0
        step.retry_attempt = 2
        assert step.retry_attempt == 2


class TestOrchestratorFullFlow:
    def test_full_dry_run_publish_flow(self):
        orch = SupremeOrchestrator(dry_run=True)
        mission = orch.run("post no feed")
        assert mission.intent == "publish_content"
        assert mission.status == SupremeStatus.DRY_RUN
        exec_data = mission.execution
        assert exec_data["status"] == "dry_complete"

    def test_full_dry_run_campaign_flow(self):
        orch = SupremeOrchestrator(dry_run=True)
        mission = orch.run("criar campanha de marketing para o hotel")
        assert mission.intent == "create_campaign"
        assert mission.status == SupremeStatus.DRY_RUN
        assert len(mission.execution["steps"]) == 7

    def test_full_dry_run_analytics_flow(self):
        orch = SupremeOrchestrator(dry_run=True)
        mission = orch.run("analisar métricas do mês")
        assert mission.intent == "analyze_performance"
        assert mission.status == SupremeStatus.DRY_RUN


class TestTracerIntegration:
    def test_dry_run_includes_trace(self):
        orch = SupremeOrchestrator(dry_run=True)
        mission = orch.run("publicar conteúdo")
        assert "trace" in mission.execution
        trace = mission.execution["trace"]
        assert "trace_count" in trace
        assert trace["ok_count"] >= 0
