"""Blueprint bundle exporter for App Factory."""
from __future__ import annotations

import json
from dataclasses import dataclass

from src.app_factory.api_contract import APIContract
from src.app_factory.models import AppArtifact
from src.app_factory.schema_planner import SchemaPlan
from src.app_factory.task_plan import ImplementationTaskPlan


@dataclass(frozen=True)
class AppFactoryBundle:
    artifact_id: str
    prd_markdown: str
    schema_plan: SchemaPlan
    api_contract: APIContract
    task_plan: ImplementationTaskPlan
    dry_run: bool = True

    def to_dict(self) -> dict:
        return {
            "artifact_id": self.artifact_id,
            "dry_run": self.dry_run,
            "prd_markdown": self.prd_markdown,
            "schema_plan": self.schema_plan.to_dict(),
            "api_contract": self.api_contract.to_dict(),
            "task_plan": self.task_plan.to_dict(),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def to_markdown(self) -> str:
        lines = [
            f"# App Factory Bundle {self.artifact_id}",
            "",
            "## PRD",
            self.prd_markdown,
            "## Schema",
        ]
        for table in self.schema_plan.tables:
            lines.append(f"- {table.name}: {', '.join(field.name for field in table.fields)}")
        lines.append("")
        lines.append("## API")
        for endpoint in self.api_contract.endpoints:
            lines.append(f"- {endpoint.method} {endpoint.path}")
        lines.append("")
        lines.append("## Tasks")
        for task in self.task_plan.tasks:
            lines.append(f"- [{task.area}] {task.title}")
        return "\n".join(lines) + "\n"


def build_bundle(
    artifact: AppArtifact,
    schema_plan: SchemaPlan,
    api_contract: APIContract,
    task_plan: ImplementationTaskPlan,
    dry_run: bool = True,
) -> AppFactoryBundle:
    return AppFactoryBundle(
        artifact_id=artifact.artifact_id,
        prd_markdown=artifact.prd_markdown,
        schema_plan=schema_plan,
        api_contract=api_contract,
        task_plan=task_plan,
        dry_run=dry_run,
    )
