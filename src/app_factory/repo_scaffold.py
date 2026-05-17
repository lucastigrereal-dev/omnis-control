"""Safe repo scaffold generator for W137."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.app_factory.models import AppArtifact


@dataclass(frozen=True)
class ScaffoldManifest:
    artifact_id: str
    root: str
    files: list[dict]
    dry_run: bool = True
    written: bool = False

    def to_dict(self) -> dict:
        return self.__dict__


def generate_repo_scaffold(
    artifact: AppArtifact,
    output_dir: Path,
    dry_run: bool = True,
) -> ScaffoldManifest:
    files = _flatten_structure(artifact.project_structure)
    if not dry_run:
        root = Path(output_dir)
        for item in files:
            path = root / item["path"]
            if path.exists():
                raise FileExistsError(f"Refusing to overwrite existing file: {path}")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(item["content"], encoding="utf-8")

    return ScaffoldManifest(
        artifact_id=artifact.artifact_id,
        root=str(output_dir),
        files=files,
        dry_run=dry_run,
        written=not dry_run,
    )


def _flatten_structure(structure: dict, prefix: str = "") -> list[dict]:
    files: list[dict] = []
    for name, value in sorted(structure.items()):
        path = f"{prefix}{name}"
        if isinstance(value, dict):
            files.extend(_flatten_structure(value, prefix=f"{path}/"))
        else:
            files.append({"path": path, "content": "" if value is None else str(value)})
    return files
