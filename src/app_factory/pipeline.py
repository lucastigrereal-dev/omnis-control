"""End-to-end planning pipeline for App Factory."""
from __future__ import annotations

from dataclasses import dataclass

from src.app_factory.api_contract import build_api_contract
from src.app_factory.bundle_exporter import AppFactoryBundle, build_bundle
from src.app_factory.docs_generator import GeneratedAppDocs, build_generated_docs
from src.app_factory.errors import PRDGenerationError
from src.app_factory.idea_store import IdeaStore
from src.app_factory.models import AppBlueprint, AppRequirement
from src.app_factory.quality_gate import AppFactoryQualityReport, validate_bundle
from src.app_factory.schema_planner import build_schema_plan
from src.app_factory.task_plan import build_task_plan
from src.app_factory.prd_service import StoredIdeaPRDGenerator


@dataclass(frozen=True)
class AppFactoryPipelineResult:
    idea_id: str
    bundle: AppFactoryBundle
    quality_report: AppFactoryQualityReport
    docs: GeneratedAppDocs
    dry_run: bool = True

    def to_dict(self) -> dict:
        return {
            "idea_id": self.idea_id,
            "dry_run": self.dry_run,
            "bundle": self.bundle.to_dict(),
            "quality_report": self.quality_report.to_dict(),
            "docs": self.docs.to_dict(),
        }


def build_planning_pipeline(
    idea_id: str,
    store: IdeaStore | None = None,
    dry_run: bool = True,
) -> AppFactoryPipelineResult:
    active_store = store or IdeaStore(dry_run=True)
    idea = active_store.get(idea_id)
    if idea is None:
        raise PRDGenerationError(f"Idea not found: {idea_id}")

    prd = StoredIdeaPRDGenerator(store=active_store).generate(idea_id, dry_run=True)
    requirement = AppRequirement.from_idea(idea)
    blueprint = AppBlueprint.from_requirement(requirement)
    schema = build_schema_plan(blueprint, dry_run=dry_run)
    api = build_api_contract(blueprint, schema, dry_run=dry_run)
    tasks = build_task_plan(blueprint, schema, api, dry_run=dry_run)
    bundle = build_bundle(prd.artifact, schema, api, tasks, dry_run=dry_run)
    quality = validate_bundle(bundle, dry_run=dry_run)
    docs = build_generated_docs(bundle, dry_run=dry_run)

    if not quality.passed:
        raise PRDGenerationError(f"App Factory quality gate failed: {quality.issues}")

    return AppFactoryPipelineResult(
        idea_id=idea_id,
        bundle=bundle,
        quality_report=quality,
        docs=docs,
        dry_run=dry_run,
    )
