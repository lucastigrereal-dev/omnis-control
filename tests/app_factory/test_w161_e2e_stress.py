"""W161 — E2E stress tests for complete App Factory pipeline."""
from __future__ import annotations

import pytest

from src.app_factory.bundle_exporter import build_bundle
from src.app_factory.diff_engine import diff_ideas
from src.app_factory.idea_store import IdeaStore
from src.app_factory.models import AppIdea, AppBlueprint, AppRequirement, AppArtifact
from src.app_factory.pipeline import build_planning_pipeline
from src.app_factory.prd_service import StoredIdeaPRDGenerator
from src.app_factory.quality_gate import validate_bundle
from src.app_factory.quality_score import compute_quality_score
from src.app_factory.recovery import init_pipeline_state, build_recovery_plan, StageStatus
from src.app_factory.schema_planner import build_schema_plan
from src.app_factory.api_contract import build_api_contract
from src.app_factory.task_plan import build_task_plan
from src.app_factory.scaffold_plan import build_scaffold_plan
from src.app_factory.scaffold_engine import run_scaffold, ScaffoldExecution
from src.app_factory.storage_safety import audit_directory, StorageSafetyPolicy


class TestE2ECompleteFlow:
    """Full pipeline: idea -> PRD -> schema -> API -> tasks -> bundle -> scaffold -> quality."""

    def test_complete_flow_api_app(self, app_factory_tmp_dir, tmp_path):
        store = IdeaStore(data_dir=app_factory_tmp_dir, dry_run=False)
        idea = AppIdea.new(
            title="E2E API Service",
            description="Microservice for order management with REST API",
            features=["crud", "api", "search", "pagination"],
            domain="ecommerce",
        )
        store.save(idea)

        result = build_planning_pipeline(
            idea.idea_id, store=store, dry_run=True,
            with_quality_score=True, with_recovery=True,
            with_storage_safety=True, safety_target_dir=str(tmp_path),
        )

        assert result.quality_report.passed is True
        assert result.quality_score is not None
        assert result.pipeline_state is not None
        assert result.pipeline_state["overall_status"] == "completed"
        assert result.quality_score["overall"]["percentage"] >= 50.0

    def test_complete_flow_cli_app(self, app_factory_tmp_dir):
        store = IdeaStore(data_dir=app_factory_tmp_dir, dry_run=False)
        idea = AppIdea.new(
            title="E2E CLI Tool",
            description="Command-line data processing utility",
            features=["cli", "batch processing"],
        )
        store.save(idea)

        result = build_planning_pipeline(
            idea.idea_id, store=store, dry_run=True,
            with_quality_score=True, with_recovery=True,
        )
        assert result.quality_report.passed is True
        assert result.docs is not None


class TestMultipleIdeasPipeline:
    """Multiple ideas flowing through pipeline simultaneously."""

    def test_three_ideas_through_pipeline(self, app_factory_tmp_dir):
        store = IdeaStore(data_dir=app_factory_tmp_dir, dry_run=False)
        ideas = []
        for i, (title, desc) in enumerate([
            ("App Alpha", "Content management system"),
            ("App Beta", "Analytics dashboard"),
            ("App Gamma", "Notification service"),
        ]):
            idea = AppIdea.new(title=title, description=desc, features=["crud"] if i == 0 else ["search"])
            store.save(idea)
            ideas.append(idea)

        results = []
        for idea in ideas:
            result = build_planning_pipeline(
                idea.idea_id, store=store, dry_run=True,
                with_quality_score=True, with_recovery=True,
            )
            results.append(result)

        assert len(results) == 3
        assert all(r.quality_report.passed for r in results)


class TestRecoveryEndToEnd:
    """Recovery from simulated failure during pipeline."""

    def test_simulate_failure_and_recover(self, app_factory_tmp_dir):
        store = IdeaStore(data_dir=app_factory_tmp_dir, dry_run=False)
        idea = AppIdea.new(title="Recovery E2E", description="Test recovery flow")
        store.save(idea)

        # Build a pipeline up to the failure point manually
        requirement = AppRequirement.from_idea(idea)
        blueprint = AppBlueprint.from_requirement(requirement)
        schema = build_schema_plan(blueprint, dry_run=True)
        api = build_api_contract(blueprint, schema, dry_run=True)

        # Simulate pipeline state with a failure
        state = init_pipeline_state(idea.idea_id)
        state.mark_completed("validate_idea")
        state.mark_completed("extract_requirements")
        state.mark_completed("design_blueprint")
        state.mark_completed("generate_prd")
        state.mark_completed("build_schema")
        state.mark_failed("build_api_contract", "api generation failure")

        # Build recovery plan
        plan = build_recovery_plan(state)
        assert plan.can_resume is True
        assert plan.resume_from_stage == "build_api_contract"

        # Simulate continuing after recovery
        tasks = build_task_plan(blueprint, schema, api, dry_run=True)
        generator = StoredIdeaPRDGenerator(store=store)
        prd = generator.generate(idea.idea_id, dry_run=True)
        bundle = build_bundle(prd.artifact, schema, api, tasks, dry_run=True)
        quality = validate_bundle(bundle, dry_run=True)
        assert quality.passed is True


class TestDiffPipeline:
    """Diff comparison across ideas in pipeline."""

    def test_diff_across_ideas(self, app_factory_tmp_dir):
        store = IdeaStore(data_dir=app_factory_tmp_dir, dry_run=False)
        idea1 = AppIdea.new(title="Old App", description="Legacy system", features=["auth"])
        idea2 = AppIdea.new(title="New App", description="Modernized system", features=["auth", "api", "search"])
        store.save(idea1)
        store.save(idea2)

        report = diff_ideas(idea1.to_dict(), idea2.to_dict(), left_label="old", right_label="new")
        assert report.has_differences is True
        assert report.change_count >= 1


class TestScaffoldSafetyIntegration:
    """Scaffold with storage safety integration."""

    def test_scaffold_with_safety_safe_dir(self, tmp_path):
        from src.app_factory.scaffold_plan import build_scaffold_plan
        from src.app_factory.models import AppIdea, AppBlueprint, AppRequirement
        from src.app_factory.schema_planner import build_schema_plan
        from src.app_factory.api_contract import build_api_contract
        from src.app_factory.task_plan import build_task_plan

        idea = AppIdea.new(title="Safe Scaffold", description="Scaffold test with safety")
        requirement = AppRequirement.from_idea(idea)
        blueprint = AppBlueprint.from_requirement(requirement)
        schema = build_schema_plan(blueprint, dry_run=True)
        api = build_api_contract(blueprint, schema, dry_run=True)
        tasks = build_task_plan(blueprint, schema, api, dry_run=True)

        plan = build_scaffold_plan(schema, api, tasks, dry_run=True)
        safe_dir = tmp_path / "safe_output"
        safe_dir.mkdir()

        result = run_scaffold(plan, output_dir=safe_dir, dry_run=True)
        assert len(result.safety_violations) == 0

    def test_scaffold_dry_run_default(self, tmp_path):
        from src.app_factory.scaffold_plan import build_scaffold_plan
        from src.app_factory.models import AppIdea, AppBlueprint, AppRequirement
        from src.app_factory.schema_planner import build_schema_plan
        from src.app_factory.api_contract import build_api_contract
        from src.app_factory.task_plan import build_task_plan

        idea = AppIdea.new(title="Dry Default", description="Verify dry-run default")
        requirement = AppRequirement.from_idea(idea)
        blueprint = AppBlueprint.from_requirement(requirement)
        schema = build_schema_plan(blueprint, dry_run=True)
        api = build_api_contract(blueprint, schema, dry_run=True)
        tasks = build_task_plan(blueprint, schema, api, dry_run=True)

        plan = build_scaffold_plan(schema, api, tasks, dry_run=True)
        output = tmp_path / "dry_output"

        result = run_scaffold(plan, output_dir=output, dry_run=True)
        assert result.dry_run is True
        assert len(result.written_files) == 0


class TestStatusTrackerE2E:
    """Status tracker through full lifecycle."""

    def test_full_lifecycle_tracking(self, tmp_path):
        from src.app_factory.status_tracker import StatusTracker

        tracker = StatusTracker()
        tracker.register_idea("lifecycle_1", "Lifecycle App")
        tracker.mark_stage("lifecycle_1", "validate_idea", "started")
        tracker.mark_stage("lifecycle_1", "validate_idea", "completed")
        tracker.mark_stage("lifecycle_1", "extract_requirements", "started")
        tracker.mark_stage("lifecycle_1", "extract_requirements", "completed")
        tracker.mark_stage("lifecycle_1", "design_blueprint", "started")
        tracker.mark_stage("lifecycle_1", "design_blueprint", "failed", "design error")

        assert tracker.idea_count == 1

        # Save and reload
        filepath = tmp_path / "status.jsonl"
        tracker.save(str(filepath))

        tracker2 = StatusTracker()
        tracker2.load(str(filepath))
        status = tracker2.get_status("lifecycle_1")
        assert status.overall_status == "failed"

        # Recover and continue
        state = tracker2.get_state("lifecycle_1")
        plan = build_recovery_plan(state)
        assert plan.can_resume is True
