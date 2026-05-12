"""Tests for P12 Automation service — WorkflowPlanner, spec exporter, validator."""
from __future__ import annotations

import pytest

from src.automation.models import (
    AutomationTrigger,
    AutomationStep,
    AutomationWorkflow,
    TRIGGER_WEBHOOK,
    TRIGGER_SCHEDULE,
    STEP_HTTP_REQUEST,
    STEP_TRANSFORM,
    STEP_FILTER,
    STEP_MERGE,
    STEP_DELAY,
    STEP_NOTIFY,
    RUN_PLANNED,
)
from src.automation.service import (
    WorkflowPlanner,
    export_n8n_spec,
    validate_workflow,
    ValidationResult,
)
from src.automation.errors import (
    CycleDetectedError,
    UnresolvedDependencyError,
    PlanError,
    WorkflowValidationError,
    EmptyWorkflowError,
)


def _make_trigger(tt=TRIGGER_WEBHOOK):
    return AutomationTrigger.new(tt)


def _make_step(name, st, depends_on=None, position=0):
    return AutomationStep.new(name, st, depends_on=depends_on, position=position)


def _make_workflow(name="Test WF", steps=None, trigger=None, description="desc"):
    return AutomationWorkflow.new(
        name=name,
        description=description,
        trigger=trigger or _make_trigger(),
        steps=steps or [],
    )


class TestTopologicalSort:
    def test_single_step_no_deps(self):
        planner = WorkflowPlanner()
        s1 = _make_step("S1", STEP_HTTP_REQUEST)
        wf = _make_workflow(steps=[s1])
        plan = planner.plan(wf)
        assert plan.steps_to_execute == [s1.step_id]

    def test_linear_chain(self):
        planner = WorkflowPlanner()
        s1 = _make_step("Fetch", STEP_HTTP_REQUEST)
        s2 = _make_step("Transform", STEP_TRANSFORM, depends_on=[s1.step_id])
        s3 = _make_step("Notify", STEP_NOTIFY, depends_on=[s2.step_id])
        wf = _make_workflow(steps=[s3, s1, s2])
        plan = planner.plan(wf)
        assert plan.steps_to_execute == [s1.step_id, s2.step_id, s3.step_id]

    def test_diamond_dependency(self):
        planner = WorkflowPlanner()
        s1 = _make_step("Fetch", STEP_HTTP_REQUEST)
        s2 = _make_step("Filter A", STEP_FILTER, depends_on=[s1.step_id])
        s3 = _make_step("Filter B", STEP_FILTER, depends_on=[s1.step_id])
        s4 = _make_step("Merge", STEP_MERGE, depends_on=[s2.step_id, s3.step_id])
        wf = _make_workflow(steps=[s4, s2, s3, s1])
        plan = planner.plan(wf)
        assert plan.steps_to_execute[0] == s1.step_id
        assert plan.steps_to_execute[3] == s4.step_id
        assert set(plan.steps_to_execute[1:3]) == {s2.step_id, s3.step_id}

    def test_independent_chains(self):
        planner = WorkflowPlanner()
        s1 = _make_step("Chain A-1", STEP_HTTP_REQUEST)
        s2 = _make_step("Chain B-1", STEP_HTTP_REQUEST)
        s3 = _make_step("Chain A-2", STEP_DELAY, depends_on=[s1.step_id])
        s4 = _make_step("Chain B-2", STEP_DELAY, depends_on=[s2.step_id])
        wf = _make_workflow(steps=[s1, s2, s3, s4])
        plan = planner.plan(wf)
        assert set(plan.steps_to_execute[:2]) == {s1.step_id, s2.step_id}
        assert set(plan.steps_to_execute[2:]) == {s3.step_id, s4.step_id}

    def test_cycle_detected(self):
        planner = WorkflowPlanner()
        s1 = _make_step("A", STEP_HTTP_REQUEST, depends_on=["step_b"])
        s2 = _make_step("B", STEP_HTTP_REQUEST, depends_on=["step_a"])
        s1.step_id = "step_a"
        s2.step_id = "step_b"
        s1.depends_on = [s2.step_id]
        s2.depends_on = [s1.step_id]
        wf = _make_workflow(steps=[s1, s2])
        with pytest.raises(CycleDetectedError, match="Cycle detected"):
            planner.plan(wf)

    def test_unresolved_dependency(self):
        planner = WorkflowPlanner()
        s1 = _make_step("A", STEP_HTTP_REQUEST, depends_on=["step_missing"])
        wf = _make_workflow(steps=[s1])
        with pytest.raises(UnresolvedDependencyError, match="does not exist"):
            planner.plan(wf)

    def test_empty_workflow(self):
        planner = WorkflowPlanner()
        wf = _make_workflow(steps=[])
        with pytest.raises(PlanError, match="no steps"):
            planner.plan(wf)

    def test_dry_run_flag(self):
        planner = WorkflowPlanner()
        s1 = _make_step("S1", STEP_HTTP_REQUEST)
        wf = _make_workflow(steps=[s1])
        plan = planner.plan(wf, dry_run=True)
        assert plan.dry_run is True

        plan2 = planner.plan(wf, dry_run=False)
        assert plan2.dry_run is False


class TestExportN8nSpec:
    def test_exports_basic_structure(self):
        s1 = _make_step("Fetch", STEP_HTTP_REQUEST)
        wf = _make_workflow(name="Test Export", steps=[s1])
        spec = export_n8n_spec(wf)
        assert spec["name"] == "Test Export"
        assert spec["active"] is True
        assert spec["versionId"] == "1.0.0-dryrun"
        assert spec["meta"]["dry_run"] is True

    def test_exports_nodes(self):
        s1 = _make_step("Fetch", STEP_HTTP_REQUEST)
        s2 = _make_step("Notify", STEP_NOTIFY, depends_on=[s1.step_id])
        wf = _make_workflow(steps=[s1, s2])
        spec = export_n8n_spec(wf)
        assert len(spec["nodes"]) == 3  # trigger + 2 steps
        node_ids = [n["id"] for n in spec["nodes"]]
        assert wf.trigger.trigger_id in node_ids
        assert s1.step_id in node_ids
        assert s2.step_id in node_ids

    def test_exports_n8n_type_mapping(self):
        s1 = _make_step("Transform", STEP_TRANSFORM)
        wf = _make_workflow(steps=[s1])
        spec = export_n8n_spec(wf)
        step_node = next(n for n in spec["nodes"] if n["id"] == s1.step_id)
        assert step_node["type"] == "n8n-nodes-base.function"

    def test_exports_connections(self):
        s1 = _make_step("Fetch", STEP_HTTP_REQUEST)
        s2 = _make_step("Notify", STEP_NOTIFY, depends_on=[s1.step_id])
        wf = _make_workflow(steps=[s1, s2])
        spec = export_n8n_spec(wf)
        assert spec["connections"]
        assert s1.step_id in spec["connections"]

    def test_exports_positions(self):
        s1 = _make_step("Fetch", STEP_HTTP_REQUEST)
        wf = _make_workflow(steps=[s1])
        spec = export_n8n_spec(wf)
        trigger_node = next(n for n in spec["nodes"] if "trig_" in n["id"])
        assert trigger_node["position"] == [0, 0]
        step_node = next(n for n in spec["nodes"] if "step_" in n["id"])
        assert step_node["position"] == [250, 300]


class TestValidateWorkflow:
    def test_valid_workflow_passes(self):
        s1 = _make_step("Fetch", STEP_HTTP_REQUEST)
        wf = _make_workflow(steps=[s1])
        result = validate_workflow(wf)
        assert result.valid is True
        assert len(result.errors) == 0

    def test_empty_name_fails(self):
        s1 = _make_step("S1", STEP_HTTP_REQUEST)
        wf = _make_workflow(name="  ", steps=[s1])
        result = validate_workflow(wf)
        assert result.valid is False
        assert any("name" in e.lower() for e in result.errors)

    def test_no_steps_fails(self):
        wf = _make_workflow(steps=[])
        result = validate_workflow(wf)
        assert result.valid is False
        assert any("no steps" in e.lower() for e in result.errors)

    def test_missing_dependency_fails(self):
        s1 = _make_step("A", STEP_HTTP_REQUEST, depends_on=["step_ghost"])
        wf = _make_workflow(steps=[s1])
        result = validate_workflow(wf)
        assert result.valid is False
        assert any("non-existent" in e.lower() for e in result.errors)

    def test_cycle_detected_fails(self):
        s1 = _make_step("A", STEP_HTTP_REQUEST)
        s2 = _make_step("B", STEP_HTTP_REQUEST)
        s1.depends_on = [s2.step_id]
        s2.depends_on = [s1.step_id]
        wf = _make_workflow(steps=[s1, s2])
        result = validate_workflow(wf)
        assert result.valid is False

    def test_duplicate_positions_warns(self):
        s1 = _make_step("A", STEP_HTTP_REQUEST, position=1)
        s2 = _make_step("B", STEP_TRANSFORM, position=1)
        wf = _make_workflow(steps=[s1, s2])
        result = validate_workflow(wf)
        assert len(result.warnings) >= 1
        assert any("position" in w.lower() for w in result.warnings)

    def test_disabled_trigger_warns(self):
        t = AutomationTrigger.new(TRIGGER_SCHEDULE, enabled=False)
        s1 = _make_step("A", STEP_HTTP_REQUEST)
        wf = _make_workflow(trigger=t, steps=[s1])
        result = validate_workflow(wf)
        assert result.valid is True
        assert any("disabled" in w.lower() for w in result.warnings)

    def test_valid_linear_chain(self):
        s1 = _make_step("Fetch", STEP_HTTP_REQUEST)
        s2 = _make_step("Transform", STEP_TRANSFORM, depends_on=[s1.step_id])
        s3 = _make_step("Notify", STEP_NOTIFY, depends_on=[s2.step_id])
        wf = _make_workflow(steps=[s1, s2, s3])
        result = validate_workflow(wf)
        assert result.valid is True


class TestValidationResult:
    def test_valid_no_errors(self):
        vr = ValidationResult(valid=True)
        assert vr.valid is True
        assert vr.errors == []

    def test_invalid_with_errors(self):
        vr = ValidationResult(valid=False, errors=["Bad"], warnings=["Hint"])
        assert vr.valid is False
        assert vr.has_warnings is True

    def test_no_warnings(self):
        vr = ValidationResult(valid=True)
        assert vr.has_warnings is False
