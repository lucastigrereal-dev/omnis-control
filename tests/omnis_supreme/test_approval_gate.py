"""Tests for P20 Supreme Approval Gate + Reporter."""
from __future__ import annotations

import pytest

from src.omnis_supreme.models import (
    SupremeMission,
    SupremePlan,
    SupremeStep,
    MissionReport,
    SupremeStatus,
)
from src.omnis_supreme.service import SupremePlanner, SupremeExecutor
from src.omnis_supreme.approval_gate import SupremeApprovalGate
from src.omnis_supreme.reporter import SupremeReporter
from src.governance.models import (
    VERDICT_REQUIRES_APPROVAL,
    VERDICT_APPROVED,
    RISK_LOW,
    RISK_MEDIUM,
    RISK_HIGH,
)


class TestSupremeApprovalGateInit:
    def test_init_creates_gate(self):
        gate = SupremeApprovalGate()
        assert gate is not None

    def test_gate_has_risk_classifier(self):
        gate = SupremeApprovalGate()
        assert gate._risk is not None

    def test_gate_has_policy_engine(self):
        gate = SupremeApprovalGate()
        assert gate._engine is not None


class TestGate1PreExecution:
    def test_submit_low_risk_plan_returns_approved(self):
        gate = SupremeApprovalGate()
        planner = SupremePlanner()
        executor = SupremeExecutor(dry_run=True)
        mission = SupremeMission.new(request_text="test", intent="publish_content")
        plan = planner.plan(mission)
        dry_result = executor.dry_run(plan)
        decision = gate.submit(plan, dry_result)
        assert decision.verdict in (VERDICT_APPROVED, VERDICT_REQUIRES_APPROVAL)
        assert decision.action_type == "write"

    def test_submit_multi_step_plan_returns_decision(self):
        gate = SupremeApprovalGate()
        planner = SupremePlanner()
        executor = SupremeExecutor(dry_run=True)
        mission = SupremeMission.new(request_text="test", intent="create_campaign")
        plan = planner.plan(mission)
        dry_result = executor.dry_run(plan)
        decision = gate.submit(plan, dry_result)
        assert decision.verdict is not None
        assert decision.risk_level in (RISK_LOW, RISK_MEDIUM, RISK_HIGH)

    def test_submit_returns_governance_decision(self):
        gate = SupremeApprovalGate()
        planner = SupremePlanner()
        executor = SupremeExecutor(dry_run=True)
        mission = SupremeMission.new(request_text="test", intent="publish_content")
        plan = planner.plan(mission)
        dry_result = executor.dry_run(plan)
        decision = gate.submit(plan, dry_result)
        from src.governance.models import GovernanceDecision
        assert isinstance(decision, GovernanceDecision)

    def test_assess_plan_risk_single_step_is_low(self):
        gate = SupremeApprovalGate()
        s1 = SupremeStep.new(module_ref="P8", operation="validate")
        plan = SupremePlan.new(mission_id="spr_x", steps=[s1])
        dry = {"steps": [{"step_id": s1.step_id, "status": "dry_ok"}]}
        risk = gate._assess_plan_risk(plan, dry)
        assert risk == RISK_LOW

    def test_assess_plan_risk_many_steps_is_medium(self):
        gate = SupremeApprovalGate()
        steps = [SupremeStep.new(module_ref=f"P{i}", operation="op") for i in range(5)]
        plan = SupremePlan.new(mission_id="spr_x", steps=steps)
        dry = {"steps": [{"step_id": s.step_id, "status": "dry_ok"} for s in steps]}
        risk = gate._assess_plan_risk(plan, dry)
        assert risk == RISK_MEDIUM

    def test_assess_plan_risk_blocked_is_high(self):
        gate = SupremeApprovalGate()
        s1 = SupremeStep.new(module_ref="P5", operation="brief")
        plan = SupremePlan.new(mission_id="spr_x", steps=[s1])
        dry = {"steps": [{"step_id": s1.step_id, "status": "dry_blocked", "error": "boom"}]}
        risk = gate._assess_plan_risk(plan, dry)
        assert risk == RISK_HIGH


class TestGate2Delivery:
    def test_gate_delivery_returns_decision(self):
        gate = SupremeApprovalGate()
        planner = SupremePlanner()
        executor = SupremeExecutor(dry_run=True)
        mission = SupremeMission.new(request_text="test", intent="publish_content")
        plan = planner.plan(mission)
        dry_result = executor.dry_run(plan)
        decision = gate.gate_delivery(plan, dry_result)
        assert decision is not None
        assert decision.action_type == "send"

    def test_gate_delivery_high_risk(self):
        gate = SupremeApprovalGate()
        s1 = SupremeStep.new(module_ref="P17", operation="build_delivery_package")
        plan = SupremePlan.new(mission_id="spr_x", steps=[s1])
        dry = {"steps": []}
        decision = gate.gate_delivery(plan, dry)
        assert decision.risk_level == RISK_HIGH

    def test_gate_delivery_requires_approval(self):
        gate = SupremeApprovalGate()
        s1 = SupremeStep.new(module_ref="P17", operation="build_delivery_package")
        plan = SupremePlan.new(mission_id="spr_x", steps=[s1])
        dry = {"steps": []}
        decision = gate.gate_delivery(plan, dry)
        assert decision.verdict == VERDICT_REQUIRES_APPROVAL


class TestSupremeReporter:
    def test_generate_returns_mission_report(self):
        reporter = SupremeReporter()
        orch = SupremeExecutor(dry_run=True)
        planner = SupremePlanner()
        mission = SupremeMission.new(request_text="test", intent="publish_content")
        plan = planner.plan(mission)
        execution = orch.dry_run(plan)
        mission.execution = execution
        report = reporter.generate(mission)
        assert isinstance(report, MissionReport)
        assert report.mission_id == mission.mission_id

    def test_generate_has_summary(self):
        reporter = SupremeReporter()
        orch = SupremeExecutor(dry_run=True)
        planner = SupremePlanner()
        mission = SupremeMission.new(request_text="test", intent="publish_content")
        plan = planner.plan(mission)
        mission.execution = orch.dry_run(plan)
        report = reporter.generate(mission)
        assert report.summary != ""
        assert "Mission" in report.summary

    def test_generate_has_steps_summary(self):
        reporter = SupremeReporter()
        orch = SupremeExecutor(dry_run=True)
        planner = SupremePlanner()
        mission = SupremeMission.new(request_text="test", intent="publish_content")
        plan = planner.plan(mission)
        mission.execution = orch.dry_run(plan)
        report = reporter.generate(mission)
        assert len(report.steps_summary) > 0

    def test_generate_has_metrics(self):
        reporter = SupremeReporter()
        orch = SupremeExecutor(dry_run=True)
        planner = SupremePlanner()
        mission = SupremeMission.new(request_text="test", intent="publish_content")
        plan = planner.plan(mission)
        mission.execution = orch.dry_run(plan)
        report = reporter.generate(mission)
        assert "total_steps" in report.metrics

    def test_generate_multi_step_has_learnings(self):
        reporter = SupremeReporter()
        orch = SupremeExecutor(dry_run=True)
        planner = SupremePlanner()
        mission = SupremeMission.new(request_text="test", intent="create_campaign")
        plan = planner.plan(mission)
        mission.execution = orch.dry_run(plan)
        report = reporter.generate(mission)
        assert len(report.learnings) > 0

    def test_generate_with_warnings(self):
        reporter = SupremeReporter()
        orch = SupremeExecutor(dry_run=True)
        planner = SupremePlanner()
        mission = SupremeMission.new(request_text="test", intent="publish_content")
        mission.warnings.append("low memory")
        plan = planner.plan(mission)
        mission.execution = orch.dry_run(plan)
        report = reporter.generate(mission)
        assert "low memory" in report.warnings

    def test_extract_learnings_empty(self):
        reporter = SupremeReporter()
        result = reporter._extract_learnings({"steps": []}, [])
        assert any(l["type"] == "clean_run" for l in result)

    def test_extract_learnings_with_failure(self):
        reporter = SupremeReporter()
        execution = {
            "steps": [{"step_id": "step_01", "status": "failed", "error": "timeout"}]
        }
        learnings = reporter._extract_learnings(execution, [])
        assert any(l["type"] == "step_failure" for l in learnings)

    def test_extract_learnings_modules_used(self):
        reporter = SupremeReporter()
        execution = {
            "steps": [
                {"step_id": "s1", "status": "ok", "output": {"module_ref": "P5", "operation": "brief"}},
                {"step_id": "s2", "status": "ok", "output": {"module_ref": "P8", "operation": "validate"}},
            ]
        }
        learnings = reporter._extract_learnings(execution, [])
        mod_learning = next((l for l in learnings if l["type"] == "modules_used"), None)
        assert mod_learning is not None
        assert "P5" in mod_learning["modules"]
        assert "P8" in mod_learning["modules"]


class TestGateReporterIntegration:
    def test_gate_then_report_flow(self):
        gate = SupremeApprovalGate()
        reporter = SupremeReporter()
        planner = SupremePlanner()
        executor = SupremeExecutor(dry_run=True)

        mission = SupremeMission.new(request_text="test", intent="publish_content")
        plan = planner.plan(mission)
        dry_result = executor.dry_run(plan)

        decision = gate.submit(plan, dry_result)
        assert decision is not None

        mission.execution = dry_result
        mission.approval_decisions.append(decision.to_dict())
        report = reporter.generate(mission)
        assert report.summary != ""

    def test_mission_to_dict_with_approval(self):
        gate = SupremeApprovalGate()
        reporter = SupremeReporter()
        planner = SupremePlanner()
        executor = SupremeExecutor(dry_run=True)

        mission = SupremeMission.new(request_text="test", intent="publish_content")
        plan = planner.plan(mission)
        dry_result = executor.dry_run(plan)
        decision = gate.submit(plan, dry_result)

        mission.plan = plan
        mission.execution = dry_result
        mission.approval_decisions.append(decision.to_dict())
        report = reporter.generate(mission)
        mission.report = report.to_dict()

        d = mission.to_dict()
        assert d["report"] is not None
        assert len(d["approval_decisions"]) == 1
