"""P9.5 — Mission Package Auto-Fill from work order outputs.

Copies work order outputs into mission package directories.
Deterministic. No LLM. No network.
"""
from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXPORTS_ROOT = Path("exports/work_orders")
DEFAULT_PACKAGES_ROOT = Path("exports/mission_packages")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AutoFillEntry:
    """A single entry in the auto-fill result."""
    output_id: str
    work_order_id: str
    contract_id: str
    source_path: str
    target_path: str
    copied: bool
    error: str = ""


@dataclass
class AutoFillResult:
    """Report of an auto-fill operation."""
    mission_id: str
    graph_run_id: str
    work_order_count: int
    output_count: int
    filled_count: int
    skipped_count: int
    entries: list[AutoFillEntry] = field(default_factory=list)
    filled_at: str = field(default_factory=_now_iso)

    @property
    def all_copied(self) -> bool:
        return self.filled_count > 0 and self.skipped_count == 0

    def to_dict(self) -> dict:
        return {
            "mission_id": self.mission_id,
            "graph_run_id": self.graph_run_id,
            "work_order_count": self.work_order_count,
            "output_count": self.output_count,
            "filled_count": self.filled_count,
            "skipped_count": self.skipped_count,
            "entries": [
                {
                    "output_id": e.output_id,
                    "work_order_id": e.work_order_id,
                    "contract_id": e.contract_id,
                    "source_path": e.source_path,
                    "target_path": e.target_path,
                    "copied": e.copied,
                    "error": e.error,
                }
                for e in self.entries
            ],
            "filled_at": self.filled_at,
        }


def auto_fill_mission_package(
    mission_id: str,
    graph_run_id: str,
    *,
    exports_root: Path = DEFAULT_EXPORTS_ROOT,
    packages_root: Path = DEFAULT_PACKAGES_ROOT,
    dry_run: bool = False,
) -> AutoFillResult:
    """Auto-fill a mission package with work order outputs.

    Looks up all work orders for a graph run and copies their outputs
    into the mission package's 04_outputs/ directory.

    Args:
        mission_id: mission package ID (matches exports/mission_packages/<id>)
        graph_run_id: graph run that produced the work orders
        exports_root: root dir for work order outputs
        packages_root: root dir for mission packages
        dry_run: if True, compute entries but don't copy files

    Returns:
        AutoFillResult with copy report
    """
    from src.work_order.graph_integration import load_work_orders_for_run

    pkg_dir = packages_root / mission_id

    entries: list[AutoFillEntry] = []
    work_orders = load_work_orders_for_run(graph_run_id, exports_root)
    work_order_count = len(work_orders)
    output_count = 0
    filled_count = 0
    skipped_count = 0

    for wo in work_orders:
        wo_dir = exports_root / wo.work_order_id
        for out in wo.outputs:
            output_count += 1
            source = wo_dir / Path(out.file_path).name

            target_dir = pkg_dir / "04_outputs" / wo.role
            target = target_dir / Path(out.file_path).name

            entry = AutoFillEntry(
                output_id=out.output_id,
                work_order_id=wo.work_order_id,
                contract_id=out.contract_id,
                source_path=str(source),
                target_path=str(target),
                copied=False,
            )

            if not source.exists():
                entry.error = f"Source file not found: {source}"
                entries.append(entry)
                skipped_count += 1
                continue

            if not dry_run:
                try:
                    target_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
                    entry.copied = True
                    filled_count += 1
                except OSError as exc:
                    entry.error = str(exc)
                    skipped_count += 1
            else:
                entry.copied = True
                filled_count += 1

            entries.append(entry)

    result = AutoFillResult(
        mission_id=mission_id,
        graph_run_id=graph_run_id,
        work_order_count=work_order_count,
        output_count=output_count,
        filled_count=filled_count,
        skipped_count=skipped_count,
        entries=entries,
    )

    if not dry_run:
        _update_package_manifest(pkg_dir, result)

    return result


def auto_fill_from_orchestrator_run(
    orch_run,
    *,
    exports_root: Path = DEFAULT_EXPORTS_ROOT,
    packages_root: Path = DEFAULT_PACKAGES_ROOT,
    dry_run: bool = False,
) -> AutoFillResult:
    """Auto-fill a mission package from an OrchestratorRun.

    Extracts mission_id and graph_run_id from the orchestrator run.
    Falls back to the orchestrator run_id if no mission_id is set.
    """
    mission_id = orch_run.mission_id or orch_run.run_id
    graph_run_id = orch_run.graph_run_id

    if not graph_run_id:
        raise ValueError(
            f"OrchestratorRun {orch_run.run_id} has no graph_run_id. "
            "Run the graph pipeline first."
        )

    return auto_fill_mission_package(
        mission_id=mission_id,
        graph_run_id=graph_run_id,
        exports_root=exports_root,
        packages_root=packages_root,
        dry_run=dry_run,
    )


def _update_package_manifest(pkg_dir: Path, result: AutoFillResult) -> None:
    """Update the mission_manifest.json with auto-fill information."""
    manifest_path = pkg_dir / "mission_manifest.json"
    if not manifest_path.exists():
        return

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    data["auto_fill"] = {
        "graph_run_id": result.graph_run_id,
        "work_order_count": result.work_order_count,
        "filled_count": result.filled_count,
        "filled_at": result.filled_at,
    }

    # Add output files to the manifest
    output_files = []
    for entry in result.entries:
        if entry.copied:
            output_files.append(entry.target_path)

    existing = set(data.get("files", []))
    for f in output_files:
        rel = str(Path(f).relative_to(pkg_dir)) if f.startswith(str(pkg_dir)) else f
        existing.add(rel)

    data["files"] = sorted(existing)
    manifest_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
