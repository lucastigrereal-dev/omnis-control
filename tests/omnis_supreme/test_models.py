"""Tests for P20 models and errors."""
from __future__ import annotations

import pytest

from src.omnis_supreme.errors import (
    ApprovalDeniedError,
    DryRunBlockedError,
    ExecutionError,
    PlanError,
    StepAdapterError,
    SupremeError,
    UnknownIntentError,
)
from src.omnis_supreme.models import (
    VALID_SUPREME_TRANSITIONS,
    MissionReport,
    SupremeMission,
    SupremePlan,
    SupremeStatus,
    SupremeStep,
    _new_id,
    _now_iso,
)


class TestSupremeStep:
    def test_new_creates_id_with_step_prefix(self):
        step = SupremeStep.new(module_ref="P5", operation="build_campaign_brief")
        assert step.step_id.startswith("step_")
        assert len(step.step_id) == 13

    def test_new_defaults_status_pending(self):
        step = SupremeStep.new(module_ref="P8", operation="validate")
        assert step.status == "pending"

    def test_new_defaults_empty_input_output(self):
        step = SupremeStep.new(module_ref="P19", operation="orchestrate")
        assert step.input_from == []
        assert step.output_to == []

    def test_new_accepts_input_from(self):
        step = SupremeStep.new(module_ref="P19", operation="op", input_from=["step_1", "step_2"])
        assert step.input_from == ["step_1", "step_2"]

    def test_new_accepts_output_to(self):
        step = SupremeStep.new(module_ref="P19", operation="op", output_to=["step_3"])
        assert step.output_to == ["step_3"]

    def test_new_accepts_config(self):
        step = SupremeStep.new(module_ref="P5", operation="brief", config={"dry_run": True})
        assert step.config == {"dry_run": True}

    def test_to_dict_includes_all_fields(self):
        step = SupremeStep.new(module_ref="P17", operation="build")
        d = step.to_dict()
        assert d["step_id"] == step.step_id
        assert d["module_ref"] == "P17"
        assert d["operation"] == "build"
        assert d["status"] == "pending"
        assert d["retry_attempt"] == 0
        assert d["result"] is None
        assert d["started_at"] is None
        assert d["completed_at"] is None

    def test_from_dict_reconstructs_step(self):
        step = SupremeStep.new(module_ref="P19", operation="allocate_budget", input_from=["s1"])
        data = step.to_dict()
        restored = SupremeStep.from_dict(data)
        assert restored.step_id == step.step_id
        assert restored.module_ref == step.module_ref
        assert restored.operation == step.operation
        assert restored.input_from == step.input_from
        assert restored.config == step.config
        assert restored.retry_attempt == step.retry_attempt

    def test_from_dict_reconstructs_with_result(self):
        step = SupremeStep.new(module_ref="P8", operation="validate")
        step.result = {"status": "ok", "items": 5}
        step.status = "completed"
        data = step.to_dict()
        restored = SupremeStep.from_dict(data)
        assert restored.result == {"status": "ok", "items": 5}
        assert restored.status == "completed"


class TestSupremePlan:
    def test_new_creates_id_with_plan_prefix(self):
        plan = SupremePlan.new(mission_id="spr_abc123")
        assert plan.plan_id.startswith("plan_")
        assert len(plan.plan_id) == 13

    def test_new_defaults_dry_run_true(self):
        plan = SupremePlan.new(mission_id="spr_abc123")
        assert plan.dry_run is True

    def test_new_accepts_steps(self):
        s1 = SupremeStep.new(module_ref="P5", operation="brief")
        plan = SupremePlan.new(mission_id="spr_x", steps=[s1])
        assert len(plan.steps) == 1
        assert plan.steps[0].module_ref == "P5"

    def test_new_accepts_edges(self):
        plan = SupremePlan.new(mission_id="spr_x", edges=[("step_a", "step_b")])
        assert plan.edges == [("step_a", "step_b")]

    def test_new_accepts_selected_modules(self):
        plan = SupremePlan.new(mission_id="spr_x", selected_modules=["P5", "P19", "P8"])
        assert plan.selected_modules == ["P5", "P19", "P8"]

    def test_to_dict_serializes_steps(self):
        s1 = SupremeStep.new(module_ref="P5", operation="brief")
        plan = SupremePlan.new(mission_id="spr_x", steps=[s1])
        d = plan.to_dict()
        assert isinstance(d["steps"], list)
        assert d["steps"][0]["module_ref"] == "P5"

    def test_to_dict_serializes_edges_as_lists(self):
        plan = SupremePlan.new(mission_id="spr_x", edges=[("a", "b")])
        d = plan.to_dict()
        assert d["edges"] == [["a", "b"]]

    def test_from_dict_reconstructs_plan(self):
        s1 = SupremeStep.new(module_ref="P5", operation="brief")
        plan = SupremePlan.new(mission_id="spr_x", steps=[s1], edges=[("a", "b")])
        data = plan.to_dict()
        restored = SupremePlan.from_dict(data)
        assert restored.plan_id == plan.plan_id
        assert restored.mission_id == plan.mission_id
        assert len(restored.steps) == 1
        assert restored.steps[0].module_ref == "P5"
        assert restored.edges == [("a", "b")]
        assert restored.dry_run is True

    def test_from_dict_reconstructs_empty_steps(self):
        plan = SupremePlan.new(mission_id="spr_x")
        data = plan.to_dict()
        restored = SupremePlan.from_dict(data)
        assert restored.steps == []
        assert restored.edges == []


class TestMissionReport:
    def test_new_creates_id_with_rpt_prefix(self):
        report = MissionReport.new(mission_id="spr_abc123")
        assert report.report_id.startswith("rpt_")

    def test_new_defaults_empty_collections(self):
        report = MissionReport.new(mission_id="spr_x")
        assert report.summary == ""
        assert report.steps_summary == []
        assert report.metrics == {}
        assert report.learnings == []
        assert report.warnings == []

    def test_new_accepts_summary(self):
        report = MissionReport.new(mission_id="spr_x", summary="All steps passed")
        assert report.summary == "All steps passed"

    def test_to_dict_includes_all_fields(self):
        report = MissionReport.new(mission_id="spr_x", warnings=["low memory"])
        d = report.to_dict()
        assert d["report_id"] == report.report_id
        assert d["mission_id"] == "spr_x"
        assert d["summary"] == ""
        assert d["warnings"] == ["low memory"]
        assert "generated_at" in d

    def test_from_dict_reconstructs(self):
        report = MissionReport.new(
            mission_id="spr_x",
            summary="Done",
            learnings=[{"key": "use retry on P8"}],
            warnings=["timeout"],
        )
        data = report.to_dict()
        restored = MissionReport.from_dict(data)
        assert restored.report_id == report.report_id
        assert restored.mission_id == report.mission_id
        assert restored.summary == "Done"
        assert restored.learnings == [{"key": "use retry on P8"}]
        assert restored.warnings == ["timeout"]


class TestSupremeMission:
    def test_new_creates_id_with_spr_prefix(self):
        mission = SupremeMission.new(request_text="Create campaign for hotel X")
        assert mission.mission_id.startswith("spr_")
        assert len(mission.mission_id) == 12

    def test_new_defaults_status_intake(self):
        mission = SupremeMission.new(request_text="Publish content")
        assert mission.status == SupremeStatus.INTAKE

    def test_new_defaults_dry_run_true(self):
        mission = SupremeMission.new(request_text="Test")
        assert mission.dry_run is True

    def test_new_defaults_approval_required_true(self):
        mission = SupremeMission.new(request_text="Test")
        assert mission.approval_required is True

    def test_new_accepts_intent_and_sector(self):
        mission = SupremeMission.new(
            request_text="Create campaign",
            intent="create_campaign",
            sector="commercial",
        )
        assert mission.intent == "create_campaign"
        assert mission.sector == "commercial"

    def test_new_defaults_empty_collections(self):
        mission = SupremeMission.new(request_text="Test")
        assert mission.context == {}
        assert mission.plan == {}
        assert mission.execution == {}
        assert mission.delivery is None
        assert mission.report is None
        assert mission.trace_events == []
        assert mission.approval_decisions == []
        assert mission.warnings == []
        assert mission.blockers == []

    def test_transition_valid_path(self):
        mission = SupremeMission.new(request_text="Test")
        assert mission.transition_to(SupremeStatus.CONTEXT_BUILDING) is True
        assert mission.status == SupremeStatus.CONTEXT_BUILDING

    def test_transition_invalid_path(self):
        mission = SupremeMission.new(request_text="Test")
        assert mission.transition_to(SupremeStatus.EXECUTING) is False
        assert mission.status == SupremeStatus.INTAKE

    def test_transition_completed_is_terminal(self):
        mission = SupremeMission.new(request_text="Test")
        mission.status = SupremeStatus.COMPLETED
        assert mission.transition_to(SupremeStatus.INTAKE) is False
        assert mission.status == SupremeStatus.COMPLETED

    def test_transition_cancelled_is_terminal(self):
        mission = SupremeMission.new(request_text="Test")
        mission.status = SupremeStatus.CANCELLED
        assert mission.transition_to(SupremeStatus.PLANNING) is False

    def test_to_dict_serializes_status_as_string(self):
        mission = SupremeMission.new(request_text="Test")
        mission.status = SupremeStatus.PLANNING
        d = mission.to_dict()
        assert d["status"] == "planning"

    def test_to_dict_serializes_plan_dict(self):
        mission = SupremeMission.new(request_text="Test")
        mission.plan = {"steps": 3, "modules": ["P5"]}
        d = mission.to_dict()
        assert d["plan"] == {"steps": 3, "modules": ["P5"]}

    def test_to_dict_serializes_plan_object(self):
        s1 = SupremeStep.new(module_ref="P5", operation="brief")
        plan = SupremePlan.new(mission_id="spr_x", steps=[s1])
        mission = SupremeMission.new(request_text="Test")
        mission.plan = plan
        d = mission.to_dict()
        assert isinstance(d["plan"], dict)
        assert "plan_id" in d["plan"]

    def test_from_dict_reconstructs_status(self):
        mission = SupremeMission.new(request_text="Test")
        mission.status = SupremeStatus.EXECUTING
        data = mission.to_dict()
        restored = SupremeMission.from_dict(data)
        assert restored.status == SupremeStatus.EXECUTING

    def test_from_dict_reconstructs_optional_fields(self):
        mission = SupremeMission.new(request_text="Test")
        mission.delivery = {"package_id": "pkg_1"}
        mission.report = {"report_id": "rpt_1"}
        data = mission.to_dict()
        restored = SupremeMission.from_dict(data)
        assert restored.delivery == {"package_id": "pkg_1"}
        assert restored.report == {"report_id": "rpt_1"}

    def test_from_dict_preserves_approval_required(self):
        mission = SupremeMission.new(request_text="Test", approval_required=True)
        data = mission.to_dict()
        restored = SupremeMission.from_dict(data)
        assert restored.approval_required is True

    def test_timestamps_set(self):
        mission = SupremeMission.new(request_text="Test")
        assert mission.created_at != ""
        assert mission.started_at is None
        assert mission.completed_at is None

    def test_full_lifecycle_transitions(self):
        mission = SupremeMission.new(request_text="Full flow")
        assert mission.transition_to(SupremeStatus.CONTEXT_BUILDING)
        assert mission.transition_to(SupremeStatus.PLANNING)
        assert mission.transition_to(SupremeStatus.DRY_RUN)
        assert mission.transition_to(SupremeStatus.AWAITING_APPROVAL)
        assert mission.transition_to(SupremeStatus.EXECUTING)
        assert mission.transition_to(SupremeStatus.COMPLETED)
        assert mission.status == SupremeStatus.COMPLETED


class TestSupremeStatusEnum:
    def test_nine_states(self):
        states = list(SupremeStatus)
        assert len(states) == 9

    def test_all_expected_states_present(self):
        expected = {
            "intake", "context_building", "planning", "dry_run",
            "awaiting_approval", "executing", "completed", "failed", "cancelled",
        }
        actual = {s.value for s in SupremeStatus}
        assert actual == expected

    def test_valid_transitions_has_all_states(self):
        for state in SupremeStatus:
            assert state in VALID_SUPREME_TRANSITIONS

    def test_completed_has_no_transitions(self):
        assert VALID_SUPREME_TRANSITIONS[SupremeStatus.COMPLETED] == set()

    def test_failed_can_retry_planning(self):
        assert SupremeStatus.PLANNING in VALID_SUPREME_TRANSITIONS[SupremeStatus.FAILED]

    def test_failed_can_be_cancelled(self):
        assert SupremeStatus.CANCELLED in VALID_SUPREME_TRANSITIONS[SupremeStatus.FAILED]


class TestErrors:
    def test_supreme_error_is_base(self):
        with pytest.raises(SupremeError):
            raise SupremeError("base")

    def test_plan_error_inherits(self):
        with pytest.raises(SupremeError):
            raise PlanError("plan failed")
        with pytest.raises(PlanError):
            raise PlanError("plan failed")

    def test_execution_error_inherits(self):
        with pytest.raises(SupremeError):
            raise ExecutionError("exec failed")

    def test_approval_denied_error_inherits(self):
        with pytest.raises(SupremeError):
            raise ApprovalDeniedError("denied")

    def test_unknown_intent_error_inherits(self):
        with pytest.raises(SupremeError):
            raise UnknownIntentError("unknown")

    def test_step_adapter_error_inherits(self):
        with pytest.raises(SupremeError):
            raise StepAdapterError("no adapter")

    def test_dry_run_blocked_error_inherits(self):
        with pytest.raises(SupremeError):
            raise DryRunBlockedError("blocked")

    def test_each_error_has_message(self):
        for err_cls in [
            PlanError, ExecutionError, ApprovalDeniedError,
            UnknownIntentError, StepAdapterError, DryRunBlockedError,
        ]:
            e = err_cls("test message")
            assert str(e) == "test message"


class TestHelpers:
    def test_new_id_returns_prefixed(self):
        result = _new_id("spr_")
        assert result.startswith("spr_")
        assert result[4:].isalnum()
        assert len(result) == 12

    def test_new_id_is_unique(self):
        ids = {_new_id("plan_") for _ in range(100)}
        assert len(ids) == 100

    def test_now_iso_is_iso_format(self):
        ts = _now_iso()
        assert "T" in ts
        assert ts.endswith("Z")
        assert len(ts) == 20


class TestApprovalDefaults:
    def test_mission_approval_required_default(self):
        m = SupremeMission.new(request_text="X")
        assert m.approval_required is True

    def test_plan_dry_run_default(self):
        p = SupremePlan.new(mission_id="spr_x")
        assert p.dry_run is True

    def test_mission_dry_run_default(self):
        m = SupremeMission.new(request_text="X")
        assert m.dry_run is True
