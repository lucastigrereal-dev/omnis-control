"""Tests for recovery module."""
from __future__ import annotations

import pytest

from src.app_factory.recovery import (
    StageStatus,
    StageResult,
    PipelineState,
    RecoveryPlan,
    init_pipeline_state,
    build_recovery_plan,
    rollback_to_stage,
    STAGE_ORDER,
    STAGE_INDEX,
)


class TestStageResult:
    def test_to_dict_from_dict_round_trip(self):
        sr = StageResult(
            stage="build_schema",
            status=StageStatus.COMPLETED,
            started_at="2026-01-01T00:00:00Z",
            artifact_refs=["art_001"],
        )
        d = sr.to_dict()
        restored = StageResult.from_dict(d)
        assert restored.stage == sr.stage
        assert restored.status == sr.status
        assert restored.artifact_refs == sr.artifact_refs

    def test_default_values(self):
        sr = StageResult(stage="test", status=StageStatus.PENDING)
        assert sr.started_at == ""
        assert sr.error_message == ""
        assert sr.artifact_refs == []


class TestPipelineState:
    def test_init_pipeline_state_creates_all_stages(self):
        state = init_pipeline_state("idea_001")
        assert state.idea_id == "idea_001"
        assert len(state.stages) == len(STAGE_ORDER)
        for stage in STAGE_ORDER:
            assert stage in state.stages
            assert state.stages[stage].status == StageStatus.PENDING

    def test_mark_started(self):
        state = init_pipeline_state("idea_001")
        state.mark_started("validate_idea")
        assert state.stages["validate_idea"].status == StageStatus.RUNNING
        assert state.overall_status == StageStatus.RUNNING

    def test_mark_completed(self):
        state = init_pipeline_state("idea_001")
        state.mark_completed("validate_idea", ["art_ref"])
        assert state.stages["validate_idea"].status == StageStatus.COMPLETED
        assert "art_ref" in state.stages["validate_idea"].artifact_refs

    def test_mark_failed_updates_overall_status(self):
        state = init_pipeline_state("idea_001")
        state.mark_started("generate_prd")
        state.mark_failed("generate_prd", "Missing data")
        assert state.stages["generate_prd"].status == StageStatus.FAILED
        assert state.overall_status == StageStatus.FAILED

    def test_last_completed_stage(self):
        state = init_pipeline_state("idea_001")
        state.mark_completed("validate_idea")
        state.mark_completed("extract_requirements")
        state.mark_completed("design_blueprint")
        assert state.last_completed_stage == "design_blueprint"

    def test_first_failed_stage(self):
        state = init_pipeline_state("idea_001")
        state.mark_completed("validate_idea")
        state.mark_failed("extract_requirements", "error")
        assert state.first_failed_stage == "extract_requirements"

    def test_next_pending_stage(self):
        state = init_pipeline_state("idea_001")
        assert state.next_pending_stage == "validate_idea"
        state.mark_completed("validate_idea")
        assert state.next_pending_stage == "extract_requirements"

    def test_progress_pct(self):
        state = init_pipeline_state("idea_001")
        assert state.progress_pct == 0.0
        state.mark_completed("validate_idea")
        assert state.progress_pct > 0

    def test_is_complete(self):
        state = init_pipeline_state("idea_001")
        assert state.is_complete is False
        state.finish()
        assert state.is_complete is True

    def test_finish_sets_timestamp(self):
        state = init_pipeline_state("idea_001")
        state.finish()
        assert state.completed_at != ""
        assert state.overall_status == StageStatus.COMPLETED

    def test_to_dict_from_dict_round_trip(self):
        state = init_pipeline_state("idea_001")
        state.mark_started("validate_idea")
        state.mark_completed("validate_idea")
        state.mark_failed("extract_requirements", "test error")
        d = state.to_dict()
        restored = PipelineState.from_dict(d)
        assert restored.idea_id == "idea_001"
        assert restored.stages["validate_idea"].status == StageStatus.COMPLETED
        assert restored.stages["extract_requirements"].status == StageStatus.FAILED
        assert restored.overall_status == StageStatus.FAILED


class TestBuildRecoveryPlan:
    def test_cannot_resume_non_failed_state(self):
        state = init_pipeline_state("idea_001")
        plan = build_recovery_plan(state)
        assert plan.can_resume is False

    def test_can_resume_failed_state(self):
        state = init_pipeline_state("idea_001")
        state.mark_completed("validate_idea")
        state.mark_completed("extract_requirements")
        state.mark_failed("design_blueprint", "error")
        plan = build_recovery_plan(state)
        assert plan.can_resume is True
        assert plan.resume_from_stage == "design_blueprint"

    def test_resets_failed_stages_to_pending(self):
        state = init_pipeline_state("idea_001")
        state.mark_completed("validate_idea")
        state.mark_failed("extract_requirements", "error")
        plan = build_recovery_plan(state)
        assert plan.state.stages["extract_requirements"].status == StageStatus.PENDING
        assert plan.state.stages["extract_requirements"].error_message == ""

    def test_force_retry_enables_resume(self):
        state = init_pipeline_state("idea_001")
        state.mark_completed("validate_idea")
        plan = build_recovery_plan(state, force_retry=True)
        assert plan.can_resume is True

    def test_multiple_failures_all_reset(self):
        state = init_pipeline_state("idea_001")
        state.mark_completed("validate_idea")
        state.mark_failed("extract_requirements", "e1")
        state.mark_failed("design_blueprint", "e2")
        plan = build_recovery_plan(state)
        assert len(plan.failed_stages) == 2


class TestRollback:
    def test_rollback_clears_later_stages(self):
        state = init_pipeline_state("idea_001")
        state.mark_completed("validate_idea")
        state.mark_completed("extract_requirements")
        state.mark_completed("design_blueprint")
        state = rollback_to_stage(state, "validate_idea")
        assert state.stages["validate_idea"].status == StageStatus.COMPLETED
        assert state.stages["extract_requirements"].status == StageStatus.PENDING
        assert state.stages["design_blueprint"].status == StageStatus.PENDING
        assert state.overall_status == StageStatus.PENDING

    def test_rollback_unknown_stage_raises(self):
        state = init_pipeline_state("idea_001")
        with pytest.raises(ValueError):
            rollback_to_stage(state, "nonexistent_stage")


class TestRecoveryPlan:
    def test_to_dict(self):
        state = init_pipeline_state("idea_001")
        state.mark_failed("design_blueprint", "error")
        plan = build_recovery_plan(state)
        d = plan.to_dict()
        assert "state" in d
        assert "resume_from_stage" in d
        assert "can_resume" in d
