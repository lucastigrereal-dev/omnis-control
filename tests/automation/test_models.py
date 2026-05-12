"""Tests for P12 Automation models."""
from __future__ import annotations

import pytest

from src.automation.models import (
    AutomationTrigger,
    AutomationStep,
    AutomationWorkflow,
    AutomationRunPlan,
    TRIGGER_WEBHOOK,
    TRIGGER_SCHEDULE,
    TRIGGER_MANUAL,
    TRIGGER_MISSION_COMPLETED,
    STEP_HTTP_REQUEST,
    STEP_TRANSFORM,
    STEP_FILTER,
    STEP_MERGE,
    STEP_DELAY,
    STEP_NOTIFY,
    RUN_PLANNED,
    RUN_RUNNING,
    RUN_COMPLETED,
    RUN_FAILED,
    VALID_TRIGGERS,
    VALID_STEPS,
    VALID_RUN_STATUSES,
)


class TestAutomationTrigger:
    def test_new_creates_trigger_with_id(self):
        t = AutomationTrigger.new(TRIGGER_WEBHOOK)
        assert t.trigger_id.startswith("trig_")
        assert len(t.trigger_id) == 13  # "trig_" + 8 hex
        assert t.trigger_type == TRIGGER_WEBHOOK
        assert t.enabled is True
        assert t.config == {}

    def test_new_with_config_and_disabled(self):
        cfg = {"url": "/hook"}
        t = AutomationTrigger.new(TRIGGER_SCHEDULE, config=cfg, enabled=False)
        assert t.config == cfg
        assert t.enabled is False

    def test_new_rejects_invalid_type(self):
        with pytest.raises(ValueError, match="Invalid trigger type"):
            AutomationTrigger.new("invalid_type")

    def test_all_trigger_types_are_valid(self):
        for tt in [TRIGGER_WEBHOOK, TRIGGER_SCHEDULE, TRIGGER_MANUAL, TRIGGER_MISSION_COMPLETED]:
            t = AutomationTrigger.new(tt)
            assert t.trigger_type == tt

    def test_round_trip_dict(self):
        t = AutomationTrigger.new(TRIGGER_MANUAL, config={"param": 1}, enabled=False)
        d = t.to_dict()
        t2 = AutomationTrigger.from_dict(d)
        assert t2.trigger_id == t.trigger_id
        assert t2.trigger_type == t.trigger_type
        assert t2.config == t.config
        assert t2.enabled == t.enabled


class TestAutomationStep:
    def test_new_creates_step_with_id(self):
        s = AutomationStep.new("Fetch Data", STEP_HTTP_REQUEST)
        assert s.step_id.startswith("step_")
        assert s.name == "Fetch Data"
        assert s.step_type == STEP_HTTP_REQUEST
        assert s.config == {}
        assert s.position == 0
        assert s.depends_on == []

    def test_new_with_all_fields(self):
        s = AutomationStep.new(
            "Transform", STEP_TRANSFORM,
            config={"expr": "x*2"}, position=2, depends_on=["step_abc"]
        )
        assert s.config == {"expr": "x*2"}
        assert s.position == 2
        assert s.depends_on == ["step_abc"]

    def test_new_rejects_invalid_type(self):
        with pytest.raises(ValueError, match="Invalid step type"):
            AutomationStep.new("Bad", "not_a_step_type")

    @pytest.mark.parametrize("st", [STEP_HTTP_REQUEST, STEP_TRANSFORM, STEP_FILTER, STEP_MERGE, STEP_DELAY, STEP_NOTIFY])
    def test_all_step_types_valid(self, st):
        s = AutomationStep.new("S", st)
        assert s.step_type == st

    def test_round_trip_dict(self):
        s = AutomationStep.new("Merge", STEP_MERGE, config={"key": "id"}, position=3, depends_on=["step_a", "step_b"])
        d = s.to_dict()
        s2 = AutomationStep.from_dict(d)
        assert s2.step_id == s.step_id
        assert s2.name == s.name
        assert s2.config == s.config
        assert s2.position == s.position
        assert s2.depends_on == s.depends_on


class TestAutomationWorkflow:
    def _make_trigger(self):
        return AutomationTrigger.new(TRIGGER_WEBHOOK)

    def _make_step(self, name="S1", step_type=STEP_HTTP_REQUEST):
        return AutomationStep.new(name, step_type)

    def test_new_creates_workflow(self):
        t = self._make_trigger()
        wf = AutomationWorkflow.new("Test WF", "A test workflow", t)
        assert wf.workflow_id.startswith("wf_")
        assert wf.name == "Test WF"
        assert wf.description == "A test workflow"
        assert wf.trigger == t
        assert wf.steps == []
        assert wf.active is True

    def test_new_inactive(self):
        wf = AutomationWorkflow.new("WF", "desc", self._make_trigger(), active=False)
        assert wf.active is False

    def test_round_trip_dict_with_steps(self):
        t = self._make_trigger()
        s1 = self._make_step("Fetch", STEP_HTTP_REQUEST)
        s2 = self._make_step("Filter", STEP_FILTER)
        s2.depends_on = [s1.step_id]
        wf = AutomationWorkflow.new("Full WF", "Full workflow", t, steps=[s1, s2])
        d = wf.to_dict()
        wf2 = AutomationWorkflow.from_dict(d)
        assert wf2.workflow_id == wf.workflow_id
        assert wf2.name == wf.name
        assert len(wf2.steps) == 2
        assert wf2.steps[0].step_id == s1.step_id
        assert wf2.steps[1].depends_on == [s1.step_id]
        assert wf2.trigger.trigger_id == t.trigger_id

    def test_created_at_and_updated_at_set(self):
        wf = AutomationWorkflow.new("WF", "desc", self._make_trigger())
        assert wf.created_at
        assert wf.updated_at
        assert "T" in wf.created_at  # ISO format


class TestAutomationRunPlan:
    def test_new_creates_run_plan(self):
        rp = AutomationRunPlan.new("wf_abc", ["step_1", "step_2"])
        assert rp.run_id.startswith("run_")
        assert rp.workflow_id == "wf_abc"
        assert rp.steps_to_execute == ["step_1", "step_2"]
        assert rp.status == RUN_PLANNED
        assert rp.dry_run is True

    def test_new_dry_run_false(self):
        rp = AutomationRunPlan.new("wf_x", ["step_a"], dry_run=False)
        assert rp.dry_run is False

    def test_round_trip_dict(self):
        rp = AutomationRunPlan.new("wf_1", ["s1", "s2", "s3"], dry_run=True)
        d = rp.to_dict()
        rp2 = AutomationRunPlan.from_dict(d)
        assert rp2.run_id == rp.run_id
        assert rp2.workflow_id == rp.workflow_id
        assert rp2.steps_to_execute == rp.steps_to_execute
        assert rp2.status == RUN_PLANNED

    def test_defaults_not_started(self):
        rp = AutomationRunPlan.new("wf_x", ["s1"])
        assert rp.started_at is None
        assert rp.completed_at is None


class TestConstants:
    def test_valid_triggers(self):
        assert len(VALID_TRIGGERS) == 4

    def test_valid_steps(self):
        assert len(VALID_STEPS) == 6

    def test_valid_run_statuses(self):
        assert len(VALID_RUN_STATUSES) == 4
