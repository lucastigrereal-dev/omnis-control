"""Dry-run scaffold engine for App Factory."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from src.app_factory.scaffold_plan import ScaffoldPlan
from src.app_factory.storage_safety import (
    StorageSafetyPolicy,
    matches_blocked_pattern,
)


@dataclass(frozen=True)
class ScaffoldExecution:
    root: str
    planned_files: list[str]
    written_files: list[str]
    warnings: list[str]
    dry_run: bool = True
    safety_violations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = self.__dict__.copy()
        return d


def run_scaffold(
    plan: ScaffoldPlan,
    output_dir: Path,
    dry_run: bool = True,
    overwrite: bool = False,
    safety_policy: Optional[StorageSafetyPolicy] = None,
) -> ScaffoldExecution:
    if safety_policy is None:
        safety_policy = StorageSafetyPolicy()

    root = Path(output_dir).resolve()
    planned: list[str] = []
    written: list[str] = []
    warnings: list[str] = []
    safety_violations: list[str] = []

    # Safety audit on output directory
    root_str = str(root)
    if matches_blocked_pattern(root_str, safety_policy.blocked_patterns):
        safety_violations.append(f"output directory matches blocked pattern: {root_str}")

    for file in plan.files:
        target = (root / file.path).resolve()
        if not _is_relative_to(target, root):
            raise ValueError(f"Refusing path traversal: {file.path}")

        target_str = str(target)
        if matches_blocked_pattern(target_str, safety_policy.blocked_patterns):
            safety_violations.append(f"blocked path: {file.path}")
            continue

        planned.append(target_str)
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
        safety_violations=safety_violations,
    )


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _placeholder(path: str, purpose: str) -> str:
    return f"# {path}\n\n# Purpose: {purpose}\n"
