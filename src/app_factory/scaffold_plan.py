"""Scaffold plan generator for App Factory."""
from __future__ import annotations

from dataclasses import dataclass

from src.app_factory.api_contract import APIContract
from src.app_factory.schema_planner import SchemaPlan
from src.app_factory.task_plan import ImplementationTaskPlan


@dataclass(frozen=True)
class ScaffoldFilePlan:
    path: str
    purpose: str
    source: str


@dataclass(frozen=True)
class ScaffoldPlan:
    blueprint_id: str
    files: list[ScaffoldFilePlan]
    dry_run: bool = True

    def to_dict(self) -> dict:
        return {
            "blueprint_id": self.blueprint_id,
            "dry_run": self.dry_run,
            "files": [file.__dict__ for file in self.files],
        }


def build_scaffold_plan(
    schema_plan: SchemaPlan,
    api_contract: APIContract,
    task_plan: ImplementationTaskPlan,
    dry_run: bool = True,
) -> ScaffoldPlan:
    files: list[ScaffoldFilePlan] = [
        ScaffoldFilePlan("README.md", "planned app overview and setup notes", "docs"),
        ScaffoldFilePlan("tests/test_smoke.py", "smoke test placeholder", "qa"),
    ]
    for table in schema_plan.tables:
        entity = table.name.removesuffix("s")
        files.append(ScaffoldFilePlan(f"backend/models/{entity}.py", f"{table.name} model", "schema"))
        files.append(ScaffoldFilePlan(f"backend/repositories/{entity}_repository.py", f"{table.name} repository", "schema"))
    for endpoint in api_contract.endpoints:
        entity = _entity_from_path(endpoint.path)
        files.append(ScaffoldFilePlan(f"backend/routes/{entity}.py", f"{entity} route contract", "api"))
    for task in task_plan.tasks:
        if task.area == "frontend":
            name = task.task_id.removeprefix("frontend_")
            files.append(ScaffoldFilePlan(f"frontend/{name}/page.tsx", task.title, "tasks"))
    return ScaffoldPlan(schema_plan.blueprint_id, _dedupe(files), dry_run=dry_run)


def _entity_from_path(path: str) -> str:
    parts = [part for part in path.split("/") if part and not part.startswith("{")]
    if len(parts) >= 2 and parts[0] == "api":
        return parts[1].removesuffix("s")
    return "health"


def _dedupe(files: list[ScaffoldFilePlan]) -> list[ScaffoldFilePlan]:
    seen: set[str] = set()
    result: list[ScaffoldFilePlan] = []
    for file in files:
        if file.path not in seen:
            seen.add(file.path)
            result.append(file)
    return result
