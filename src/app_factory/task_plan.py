"""Implementation task planner for App Factory."""
from __future__ import annotations

from dataclasses import dataclass

from src.app_factory.api_contract import APIContract
from src.app_factory.models import AppBlueprint
from src.app_factory.schema_planner import SchemaPlan


@dataclass(frozen=True)
class ImplementationTask:
    task_id: str
    title: str
    area: str
    depends_on: list[str]
    acceptance: list[str]


@dataclass(frozen=True)
class ImplementationTaskPlan:
    blueprint_id: str
    tasks: list[ImplementationTask]
    dry_run: bool = True

    def to_dict(self) -> dict:
        return {
            "blueprint_id": self.blueprint_id,
            "dry_run": self.dry_run,
            "tasks": [task.__dict__ for task in self.tasks],
        }


def build_task_plan(
    blueprint: AppBlueprint,
    schema_plan: SchemaPlan,
    api_contract: APIContract,
    dry_run: bool = True,
) -> ImplementationTaskPlan:
    tasks: list[ImplementationTask] = []

    for table in schema_plan.tables:
        task_id = f"data_{table.name}"
        tasks.append(ImplementationTask(
            task_id=task_id,
            title=f"Define {table.name} data model and repository",
            area="data",
            depends_on=[],
            acceptance=["fields match schema plan", "no real migration is executed"],
        ))

    for endpoint in api_contract.endpoints:
        entity = _entity_from_path(endpoint.path)
        depends = [f"data_{entity}s"] if f"data_{entity}s" in {task.task_id for task in tasks} else []
        tasks.append(ImplementationTask(
            task_id=f"api_{endpoint.method.lower()}_{_slug(endpoint.path)}",
            title=f"Implement contract for {endpoint.method} {endpoint.path}",
            area="backend",
            depends_on=depends,
            acceptance=["request and response shape follow API contract", "errors are explicit"],
        ))

    for module in blueprint.modules:
        name = module.get("name", "module")
        if name in {"core", "tests"}:
            continue
        tasks.append(ImplementationTask(
            task_id=f"frontend_{name}",
            title=f"Build UI flow for {name}",
            area="frontend",
            depends_on=[],
            acceptance=["route renders loading, empty and error states", "uses planned API contract only"],
        ))

    tasks.append(ImplementationTask(
        task_id="qa_contracts",
        title="Add contract and smoke tests for generated plan",
        area="qa",
        depends_on=[task.task_id for task in tasks if task.area in {"backend", "frontend"}][:8],
        acceptance=["happy path covered", "missing resource and validation errors covered"],
    ))

    return ImplementationTaskPlan(blueprint_id=blueprint.blueprint_id, tasks=tasks, dry_run=dry_run)


def _entity_from_path(path: str) -> str:
    parts = [part for part in path.split("/") if part and not part.startswith("{")]
    if len(parts) >= 2 and parts[0] == "api":
        return parts[1].removesuffix("s")
    return "resource"


def _slug(path: str) -> str:
    return path.strip("/").replace("/", "_").replace("{", "").replace("}", "") or "health"
