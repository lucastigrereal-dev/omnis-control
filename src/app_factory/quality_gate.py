"""Quality validation gate for generated App Factory outputs."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.app_factory.api_contract import APIContract
from src.app_factory.bundle_exporter import AppFactoryBundle
from src.app_factory.schema_planner import SchemaPlan
from src.app_factory.task_plan import ImplementationTaskPlan


@dataclass(frozen=True)
class AppFactoryQualityReport:
    blueprint_id: str
    passed: bool
    issues: list[str]
    warnings: list[str]
    dry_run: bool = True
    quality_score_pct: Optional[float] = None

    def to_dict(self) -> dict:
        d = self.__dict__.copy()
        return d


MINIMUM_QUALITY_THRESHOLD: float = 60.0


def validate_outputs(
    prd_markdown: str,
    schema_plan: SchemaPlan,
    api_contract: APIContract,
    task_plan: ImplementationTaskPlan,
    dry_run: bool = True,
    quality_score_pct: Optional[float] = None,
) -> AppFactoryQualityReport:
    issues: list[str] = []
    warnings: list[str] = []

    if not prd_markdown.strip().startswith("# PRD:"):
        issues.append("PRD must start with '# PRD:'")
    if not schema_plan.tables:
        issues.append("schema plan must contain at least one table")
    for table in schema_plan.tables:
        if not any(field.primary_key for field in table.fields):
            warnings.append(f"table {table.name} has no primary key")
    if not api_contract.endpoints:
        issues.append("API contract must contain endpoints")
    if not task_plan.tasks:
        issues.append("task plan must contain implementation tasks")
    if not all([schema_plan.dry_run, api_contract.dry_run, task_plan.dry_run]):
        warnings.append("one or more generated outputs are not marked dry_run")

    # Quality score threshold check
    if quality_score_pct is not None and quality_score_pct < MINIMUM_QUALITY_THRESHOLD:
        issues.append(
            f"quality score {quality_score_pct}% is below minimum threshold {MINIMUM_QUALITY_THRESHOLD}%"
        )

    return AppFactoryQualityReport(
        blueprint_id=schema_plan.blueprint_id,
        passed=not issues,
        issues=issues,
        warnings=warnings,
        dry_run=dry_run,
        quality_score_pct=quality_score_pct,
    )


def validate_bundle(
    bundle: AppFactoryBundle,
    dry_run: bool = True,
    quality_score_pct: Optional[float] = None,
) -> AppFactoryQualityReport:
    return validate_outputs(
        bundle.prd_markdown,
        bundle.schema_plan,
        bundle.api_contract,
        bundle.task_plan,
        dry_run=dry_run,
        quality_score_pct=quality_score_pct,
    )
