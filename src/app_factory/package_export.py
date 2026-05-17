"""Package export builder for W139."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.app_factory.api_contract import APIContract
from src.app_factory.frontend_plan import FrontendPlan
from src.app_factory.openhands_mock import OpenHandsMockResult
from src.app_factory.repo_scaffold import ScaffoldManifest
from src.app_factory.schema_planner import SchemaPlan
from src.app_factory.test_plan import AppTestPlan


@dataclass(frozen=True)
class PackageManifest:
    package_id: str
    root: str
    files: list[str]
    dry_run: bool = True
    written: bool = False

    def to_dict(self) -> dict:
        return self.__dict__


def build_package_export(
    package_id: str,
    prd_markdown: str,
    schema_plan: SchemaPlan,
    api_contract: APIContract,
    frontend_plan: FrontendPlan,
    test_plan: AppTestPlan,
    scaffold_manifest: ScaffoldManifest,
    execution_manifest: OpenHandsMockResult,
    output_dir: Path,
    dry_run: bool = True,
) -> PackageManifest:
    payloads = {
        "README.md": f"# {package_id}\n\nLocal App Factory package.\n",
        "PRD.md": prd_markdown,
        "schema_plan.json": json.dumps(schema_plan.to_dict(), ensure_ascii=False, indent=2),
        "api_contract.json": json.dumps(api_contract.to_dict(), ensure_ascii=False, indent=2),
        "frontend_plan.json": json.dumps(frontend_plan.to_dict(), ensure_ascii=False, indent=2),
        "test_plan.json": json.dumps(test_plan.to_dict(), ensure_ascii=False, indent=2),
        "scaffold_manifest.json": json.dumps(scaffold_manifest.to_dict(), ensure_ascii=False, indent=2),
        "execution_manifest.json": json.dumps(execution_manifest.to_dict(), ensure_ascii=False, indent=2),
    }
    if not dry_run:
        root = Path(output_dir)
        root.mkdir(parents=True, exist_ok=True)
        for name, content in payloads.items():
            target = root / name
            if target.exists():
                raise FileExistsError(f"Refusing to overwrite existing package file: {target}")
            target.write_text(content, encoding="utf-8")

    return PackageManifest(
        package_id=package_id,
        root=str(output_dir),
        files=sorted(payloads),
        dry_run=dry_run,
        written=not dry_run,
    )
