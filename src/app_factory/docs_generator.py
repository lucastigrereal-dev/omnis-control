"""Technical documentation generator for planned apps."""
from __future__ import annotations

from dataclasses import dataclass

from src.app_factory.bundle_exporter import AppFactoryBundle


@dataclass(frozen=True)
class GeneratedAppDocs:
    artifact_id: str
    documents: dict[str, str]
    dry_run: bool = True

    def to_dict(self) -> dict:
        return self.__dict__


def build_generated_docs(bundle: AppFactoryBundle, dry_run: bool = True) -> GeneratedAppDocs:
    schema_lines = [f"- {table.name}" for table in bundle.schema_plan.tables]
    api_lines = [f"- {endpoint.method} {endpoint.path}" for endpoint in bundle.api_contract.endpoints]
    task_lines = [f"- {task.title}" for task in bundle.task_plan.tasks]
    docs = {
        "ARCHITECTURE.md": "# Architecture\n\n## Data\n" + "\n".join(schema_lines) + "\n\n## Tasks\n" + "\n".join(task_lines) + "\n",
        "API.md": "# API\n\n" + "\n".join(api_lines) + "\n",
        "DATA.md": "# Data Model\n\n" + "\n".join(schema_lines) + "\n",
        "README.md": f"# Planned App\n\nGenerated from artifact `{bundle.artifact_id}`.\n\nDry-run package; no app was created.\n",
    }
    return GeneratedAppDocs(bundle.artifact_id, docs, dry_run=dry_run)
