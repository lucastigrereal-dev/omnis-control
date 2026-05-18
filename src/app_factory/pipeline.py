"""End-to-end planning pipeline for App Factory."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from src.app_factory.api_contract import build_api_contract
from src.app_factory.bundle_exporter import AppFactoryBundle, build_bundle
from src.app_factory.docs_generator import GeneratedAppDocs, build_generated_docs
from src.app_factory.errors import PRDGenerationError
from src.app_factory.idea_store import IdeaStore
from src.app_factory.models import AppBlueprint, AppRequirement
from src.app_factory.quality_gate import AppFactoryQualityReport, validate_bundle
from src.app_factory.quality_score import QualityScore, compute_quality_score
from src.app_factory.recovery import PipelineState, init_pipeline_state, StageStatus
from src.app_factory.schema_planner import build_schema_plan
from src.app_factory.storage_safety import StorageSafetyPolicy, audit_directory
from src.app_factory.task_plan import build_task_plan
from src.app_factory.prd_service import StoredIdeaPRDGenerator


@dataclass(frozen=True)
class AppFactoryPipelineResult:
    idea_id: str
    bundle: AppFactoryBundle
    quality_report: AppFactoryQualityReport
    docs: GeneratedAppDocs
    dry_run: bool = True
    quality_score: Optional[dict] = None
    pipeline_state: Optional[dict] = None
    storage_safety: Optional[dict] = None

    def to_dict(self) -> dict:
        result = {
            "idea_id": self.idea_id,
            "dry_run": self.dry_run,
            "bundle": self.bundle.to_dict(),
            "quality_report": self.quality_report.to_dict(),
            "docs": self.docs.to_dict(),
        }
        if self.quality_score is not None:
            result["quality_score"] = self.quality_score
        if self.pipeline_state is not None:
            result["pipeline_state"] = self.pipeline_state
        if self.storage_safety is not None:
            result["storage_safety"] = self.storage_safety
        return result


def build_planning_pipeline(
    idea_id: str,
    store: IdeaStore | None = None,
    dry_run: bool = True,
    with_quality_score: bool = True,
    with_recovery: bool = True,
    with_storage_safety: bool = False,
    safety_target_dir: Optional[str] = None,
) -> AppFactoryPipelineResult:
    active_store = store or IdeaStore(dry_run=True)
    idea = active_store.get(idea_id)
    if idea is None:
        raise PRDGenerationError(f"Idea not found: {idea_id}")

    pipeline_state = None
    if with_recovery:
        pipeline_state = init_pipeline_state(idea_id)

    def _advance(stage: str):
        if pipeline_state:
            pipeline_state.mark_started(stage)

    def _complete(stage: str, refs: Optional[list[str]] = None):
        if pipeline_state:
            pipeline_state.mark_completed(stage, refs)

    def _fail(stage: str, error: str):
        if pipeline_state:
            pipeline_state.mark_failed(stage, error)

    try:
        _advance("validate_idea")
        _complete("validate_idea")

        _advance("extract_requirements")
        requirement = AppRequirement.from_idea(idea)
        _complete("extract_requirements", [requirement.requirement_id])

        _advance("design_blueprint")
        blueprint = AppBlueprint.from_requirement(requirement)
        _complete("design_blueprint", [blueprint.blueprint_id])

        _advance("generate_prd")
        prd = StoredIdeaPRDGenerator(store=active_store).generate(idea_id, dry_run=True)
        _complete("generate_prd", [prd.artifact.artifact_id])

        _advance("build_schema")
        schema = build_schema_plan(blueprint, dry_run=dry_run)
        _complete("build_schema")

        _advance("build_api_contract")
        api = build_api_contract(blueprint, schema, dry_run=dry_run)
        _complete("build_api_contract")

        _advance("build_tasks")
        tasks = build_task_plan(blueprint, schema, api, dry_run=dry_run)
        _complete("build_tasks")

        _advance("bundle_export")
        bundle = build_bundle(prd.artifact, schema, api, tasks, dry_run=dry_run)
        _complete("bundle_export")

        # Quality score computed before gate
        _advance("quality_gate")
        quality_score_pct = None
        if with_quality_score:
            schema_tables = [
                {"name": t.name, "fields": [f.__dict__ for f in t.fields],
                 "relationships": t.relationships, "indexes": t.indexes}
                for t in schema.tables
            ]
            qs_pre = compute_quality_score(
                bundle.artifact_id,
                bundle.prd_markdown,
                schema_tables,
                [e.__dict__ for e in api.endpoints],
                [t.__dict__ for t in tasks.tasks],
            )
            quality_score_pct = qs_pre.overall.percentage

        quality = validate_bundle(bundle, dry_run=dry_run, quality_score_pct=quality_score_pct)
        if not quality.passed:
            _fail("quality_gate", f"Quality gate failed: {quality.issues}")
            raise PRDGenerationError(f"App Factory quality gate failed: {quality.issues}")
        _complete("quality_gate")

        _advance("generate_docs")
        docs = build_generated_docs(bundle, dry_run=dry_run)
        _complete("generate_docs")

    except PRDGenerationError:
        raise
    except Exception as exc:
        if pipeline_state:
            pipeline_state.mark_failed(pipeline_state.next_pending_stage or "unknown", str(exc))
        raise PRDGenerationError(f"Pipeline failed: {exc}") from exc

    if pipeline_state and pipeline_state.overall_status != StageStatus.FAILED:
        pipeline_state.finish()

    # Optional quality score
    quality_score = None
    if with_quality_score:
        schema_tables = [
            {"name": t.name, "fields": [f.__dict__ for f in t.fields],
             "relationships": t.relationships, "indexes": t.indexes}
            for t in schema.tables
        ]
        qs = compute_quality_score(
            bundle.artifact_id,
            bundle.prd_markdown,
            schema_tables,
            [e.__dict__ for e in api.endpoints],
            [t.__dict__ for t in tasks.tasks],
        )
        quality_score = qs.to_dict()

    # Optional storage safety audit
    storage_safety = None
    if with_storage_safety and safety_target_dir:
        policy = StorageSafetyPolicy()
        report = audit_directory(safety_target_dir, policy)
        storage_safety = report.to_dict()

    return AppFactoryPipelineResult(
        idea_id=idea_id,
        bundle=bundle,
        quality_report=quality,
        docs=docs,
        dry_run=dry_run,
        quality_score=quality_score,
        pipeline_state=pipeline_state.to_dict() if pipeline_state else None,
        storage_safety=storage_safety,
    )
