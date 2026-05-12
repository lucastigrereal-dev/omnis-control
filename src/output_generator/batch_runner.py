"""Batch Output Generator — process multiple work orders in batch (dry-run by default)."""
from __future__ import annotations

import json
from pathlib import Path

from src.output_generator.manifest_registry import ManifestRegistry
from src.output_generator.writer_service import OutputWriterService


def run_batch(
    work_orders_root: Path | None = None,
    outputs_root: Path | None = None,
    status_filter: str | None = None,
    dry_run: bool = True,
    limit: int = 100,
) -> dict:
    """Process multiple work orders in batch.

    Args:
        work_orders_root: Root directory containing work order subdirectories.
        outputs_root: Where to write generated outputs.
        status_filter: Only process WOs with this status (e.g. 'approved').
        dry_run: If True, only validate and report without writing outputs.
        limit: Maximum number of WOs to process.

    Returns a dict with summary + per-WO results.
    """
    wo_root = work_orders_root or Path("exports/work_orders")
    out_root = outputs_root or Path("exports/generated_outputs")

    if not wo_root.exists():
        return {
            "total_candidates": 0,
            "processed": 0,
            "skipped": 0,
            "failed": 0,
            "registered": 0,
            "dry_run": dry_run,
            "results": [],
            "warnings": [f"Work orders root not found: {wo_root}"],
        }

    manifest_registry = ManifestRegistry()
    service = OutputWriterService(
        work_orders_root=wo_root,
        outputs_root=out_root,
        manifest_registry=manifest_registry,
    )

    # Discover work order IDs
    wo_ids: list[str] = []
    for wo_dir in sorted(wo_root.iterdir()):
        if not wo_dir.is_dir():
            continue
        manifest = wo_dir / "work_order.json"
        if not manifest.exists():
            continue
        wo_ids.append(wo_dir.name)

    # Apply status filter
    if status_filter:
        filtered: list[str] = []
        for wid in wo_ids:
            try:
                wo = service._load_work_order(wid)
                if wo.status.value == status_filter:
                    filtered.append(wid)
            except Exception:
                continue
        wo_ids = filtered

    wo_ids = wo_ids[:limit]

    results: list[dict] = []
    processed = 0
    skipped = 0
    failed = 0
    total_registered = 0

    for wid in wo_ids:
        if dry_run:
            # Dry-run: validate only, don't write
            from src.output_generator.validator import validate_package
            validation = validate_package(wid, registry=manifest_registry, output_root=out_root)
            entries = manifest_registry.list_by_work_order(wid)
            results.append({
                "work_order_id": wid,
                "valid": validation.valid,
                "issues": validation.issues,
                "warnings": validation.warnings,
                "dry_run": True,
            })
            processed += 1
        else:
            try:
                orch_result = service.orchestrate(wid)
                results.append({
                    "work_order_id": wid,
                    "valid": orch_result["valid"],
                    "package_dir": orch_result["package_dir"],
                    "registered": orch_result["registered"],
                    "issues": orch_result["validation_issues"],
                    "warnings": orch_result["validation_warnings"],
                    "dry_run": False,
                })
                total_registered += orch_result["registered"]
                processed += 1
            except Exception as exc:
                results.append({
                    "work_order_id": wid,
                    "valid": False,
                    "error": str(exc),
                    "dry_run": False,
                })
                failed += 1

    return {
        "total_candidates": len(wo_ids),
        "processed": processed,
        "skipped": skipped,
        "failed": failed,
        "registered": total_registered,
        "dry_run": dry_run,
        "status_filter": status_filter,
        "results": results,
    }
