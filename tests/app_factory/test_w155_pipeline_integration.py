"""W155 — Integration tests for enhanced pipeline with quality score, recovery, storage safety."""
from __future__ import annotations

import pytest

from src.app_factory.idea_store import IdeaStore
from src.app_factory.models import AppIdea
from src.app_factory.pipeline import AppFactoryPipelineResult, build_planning_pipeline
from src.app_factory.quality_score import QualityScore, compute_quality_score
from src.app_factory.recovery import PipelineState, StageStatus, init_pipeline_state, build_recovery_plan
from src.app_factory.status_tracker import StatusTracker
from src.app_factory.storage_safety import StorageSafetyPolicy, audit_directory


class TestPipelineWithQualityScore:
    def test_pipeline_produces_quality_score(self, app_factory_tmp_dir):
        store = IdeaStore(data_dir=app_factory_tmp_dir, dry_run=False)
        idea = AppIdea.new(title="Quality Pipeline", description="Test quality scoring in pipeline", features=["auth", "search"])
        store.save(idea)

        result = build_planning_pipeline(
            idea.idea_id, store=store, dry_run=True,
            with_quality_score=True, with_recovery=False,
        )
        assert result.quality_score is not None
        qs = result.quality_score
        assert "overall" in qs
        assert "prd_score" in qs
        assert "schema_score" in qs
        assert "api_score" in qs
        assert "tasks_score" in qs
        assert qs["overall"]["percentage"] >= 0

    def test_pipeline_without_quality_score(self, app_factory_tmp_dir):
        store = IdeaStore(data_dir=app_factory_tmp_dir, dry_run=False)
        idea = AppIdea.new(title="No QS", description="Pipeline without quality score")
        store.save(idea)

        result = build_planning_pipeline(
            idea.idea_id, store=store, dry_run=True,
            with_quality_score=False, with_recovery=False,
        )
        assert result.quality_score is None


class TestPipelineWithRecovery:
    def test_pipeline_tracks_stages(self, app_factory_tmp_dir):
        store = IdeaStore(data_dir=app_factory_tmp_dir, dry_run=False)
        idea = AppIdea.new(title="Recovery Track", description="Pipeline with recovery tracking")
        store.save(idea)

        result = build_planning_pipeline(
            idea.idea_id, store=store, dry_run=True,
            with_quality_score=False, with_recovery=True,
        )
        assert result.pipeline_state is not None
        ps = result.pipeline_state
        assert ps["overall_status"] == "completed"
        # Pipeline covers 10 of 12 STAGE_ORDER stages (excludes scaffold, package_export)
        assert ps["progress_pct"] > 80.0

    def test_pipeline_without_recovery(self, app_factory_tmp_dir):
        store = IdeaStore(data_dir=app_factory_tmp_dir, dry_run=False)
        idea = AppIdea.new(title="No Recovery", description="Pipeline without state tracking")
        store.save(idea)

        result = build_planning_pipeline(
            idea.idea_id, store=store, dry_run=True,
            with_quality_score=False, with_recovery=False,
        )
        assert result.pipeline_state is None

    def test_recovery_from_partial_state(self):
        state = init_pipeline_state("idea_test")
        state.mark_completed("validate_idea")
        state.mark_completed("extract_requirements")
        state.mark_completed("design_blueprint")
        state.mark_completed("generate_prd")
        state.mark_failed("build_schema", "schema generation error")

        plan = build_recovery_plan(state)
        assert plan.can_resume is True
        assert plan.resume_from_stage == "build_schema"
        assert "build_schema" in plan.failed_stages
        assert plan.state.stages["build_schema"].status == StageStatus.PENDING


class TestPipelineWithStorageSafety:
    def test_safety_audit_on_dir(self, tmp_path):
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("print('safe')")
        policy = StorageSafetyPolicy()
        report = audit_directory(str(tmp_path), policy)
        assert report.passed is True

    def test_safety_audit_detects_blocked(self, tmp_path):
        (tmp_path / ".env").write_text("SECRET=blocked")
        policy = StorageSafetyPolicy()
        report = audit_directory(str(tmp_path), policy)
        assert report.passed is False


class TestPipelineFullIntegration:
    def test_full_pipeline_all_options(self, app_factory_tmp_dir, tmp_path):
        store = IdeaStore(data_dir=app_factory_tmp_dir, dry_run=False)
        idea = AppIdea.new(
            title="Full Integration",
            description="Complete pipeline test with all options",
            features=["auth", "dashboard", "crud"],
        )
        store.save(idea)

        (tmp_path / "safe_src").mkdir()
        (tmp_path / "safe_src" / "app.py").write_text("# safe")

        result = build_planning_pipeline(
            idea.idea_id, store=store, dry_run=True,
            with_quality_score=True, with_recovery=True,
            with_storage_safety=True,
            safety_target_dir=str(tmp_path / "safe_src"),
        )
        assert isinstance(result, AppFactoryPipelineResult)
        assert result.quality_score is not None
        assert result.pipeline_state is not None
        assert result.storage_safety is not None
        assert result.storage_safety.get("passed") is True

    def test_pipeline_result_to_dict(self, app_factory_tmp_dir, tmp_path):
        store = IdeaStore(data_dir=app_factory_tmp_dir, dry_run=False)
        idea = AppIdea.new(title="Dict Test", description="Testing to_dict output")
        store.save(idea)

        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "app.py").write_text("# ok")

        result = build_planning_pipeline(
            idea.idea_id, store=store, dry_run=True,
            with_quality_score=True, with_recovery=True,
            with_storage_safety=True, safety_target_dir=str(tmp_path / "src"),
        )
        d = result.to_dict()
        assert d["idea_id"] == idea.idea_id
        assert "quality_score" in d
        assert "pipeline_state" in d
        assert "storage_safety" in d

    def test_pipeline_idea_not_found(self, app_factory_tmp_dir):
        store = IdeaStore(data_dir=app_factory_tmp_dir, dry_run=False)
        from src.app_factory.errors import PRDGenerationError
        with pytest.raises(PRDGenerationError, match="not found"):
            build_planning_pipeline("nonexistent_id", store=store, dry_run=True)


class TestStatusTrackerPersistence:
    def test_tracker_save_load_cycle(self, tmp_path):
        tracker = StatusTracker()
        tracker.register_idea("idea_a", "Alpha")
        tracker.mark_stage("idea_a", "validate_idea", "started")
        tracker.mark_stage("idea_a", "validate_idea", "completed")
        tracker.mark_stage("idea_a", "extract_requirements", "started")
        tracker.mark_stage("idea_a", "extract_requirements", "completed")
        tracker.mark_stage("idea_a", "design_blueprint", "started")
        tracker.mark_stage("idea_a", "design_blueprint", "completed")
        tracker.register_idea("idea_b", "Beta")
        tracker.mark_stage("idea_b", "validate_idea", "started")
        tracker.mark_stage("idea_b", "validate_idea", "completed")
        tracker.mark_stage("idea_b", "extract_requirements", "started")
        tracker.mark_stage("idea_b", "extract_requirements", "failed", "bad data")

        filepath = tmp_path / "pipeline_status.jsonl"
        saved = tracker.save(str(filepath))
        assert saved == 2

        tracker2 = StatusTracker()
        loaded = tracker2.load(str(filepath))
        assert loaded == 2
        assert tracker2.idea_count == 2

        s_a = tracker2.get_status("idea_a")
        assert s_a.overall_status in ("running", "pending")  # not all stages complete
        assert s_a.progress_pct > 0

        s_b = tracker2.get_status("idea_b")
        assert s_b.overall_status == "failed"
        assert s_b.failed_stage == "extract_requirements"

    def test_load_corrupt_file_handled(self, tmp_path):
        filepath = tmp_path / "corrupt.jsonl"
        filepath.write_text('{"bad": "json\n', encoding="utf-8")
        tracker = StatusTracker()
        count = tracker.load(str(filepath))
        assert count == 0
