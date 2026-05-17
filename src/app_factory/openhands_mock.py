"""Local OpenHands mock adapter for W138."""
from __future__ import annotations

from dataclasses import dataclass

from src.app_factory.repo_scaffold import ScaffoldManifest


@dataclass(frozen=True)
class OpenHandsMockResult:
    status: str
    dry_run: bool
    planned_steps: list[str]
    errors: list[str]

    def to_dict(self) -> dict:
        return self.__dict__


class OpenHandsMockAdapter:
    """Mock executor; never calls an external service."""

    def execute(self, manifest: ScaffoldManifest, dry_run: bool = True, fail: bool = False) -> OpenHandsMockResult:
        if fail:
            return OpenHandsMockResult(
                status="failed",
                dry_run=dry_run,
                planned_steps=[],
                errors=["mock failure requested"],
            )
        steps = [
            "inspect scaffold manifest",
            f"review {len(manifest.files)} generated files",
            "run local tests in dry-run mode",
        ]
        return OpenHandsMockResult(status="dry_run" if dry_run else "success", dry_run=dry_run, planned_steps=steps, errors=[])
