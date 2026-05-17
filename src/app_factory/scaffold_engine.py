"""Dry-run scaffold engine for App Factory."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.app_factory.scaffold_plan import ScaffoldPlan


@dataclass(frozen=True)
class ScaffoldExecution:
    root: str
    planned_files: list[str]
    written_files: list[str]
    warnings: list[str]
    dry_run: bool = True

    def to_dict(self) -> dict:
        return self.__dict__


def run_scaffold(
    plan: ScaffoldPlan,
    output_dir: Path,
    dry_run: bool = True,
    overwrite: bool = False,
) -> ScaffoldExecution:
    root = Path(output_dir).resolve()
    planned: list[str] = []
    written: list[str] = []
    warnings: list[str] = []

    for file in plan.files:
        target = (root / file.path).resolve()
        if not _is_relative_to(target, root):
            raise ValueError(f"Refusing path traversal: {file.path}")
        planned.append(str(target))
        if target.exists() and not overwrite:
            warnings.append(f"exists: {file.path}")
            continue
        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(_placeholder(file.path, file.purpose), encoding="utf-8")
            written.append(str(target))

    return ScaffoldExecution(
        root=str(root),
        planned_files=planned,
        written_files=written,
        warnings=warnings,
        dry_run=dry_run,
    )


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _placeholder(path: str, purpose: str) -> str:
    return f"# {path}\n\n# Purpose: {purpose}\n"
