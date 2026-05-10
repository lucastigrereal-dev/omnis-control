"""Output Collector — collects, persists, and organizes work order outputs."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from src.work_order.models import OutputEntry, OutputType, WorkOrder, WorkOrderStatus
from src.work_order.output_registry import OutputRegistry, OutputRegistryEntry


DEFAULT_EXPORTS_ROOT = Path("exports/work_orders")


def _hash_content(content: str | bytes) -> str:
    if isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest()[:12]


def collect_output(
    wo: WorkOrder,
    output_type: OutputType,
    content: str | bytes | dict,
    contract_id: str,
    *,
    exports_root: Path = DEFAULT_EXPORTS_ROOT,
    registry: OutputRegistry | None = None,
) -> tuple[OutputEntry, str]:
    """Collect an output for a work order, persist to disk, and update registry.

    Returns (OutputEntry, disk_path).
    """
    from src.work_order.models import make_output_id

    wo_dir = exports_root / wo.work_order_id
    wo_dir.mkdir(parents=True, exist_ok=True)

    ext = _extension_for_type(output_type)
    file_name = f"output_{len(wo.outputs):02d}_{contract_id}.{ext}"
    disk_path = wo_dir / file_name

    ts = datetime.now(timezone.utc).isoformat()

    if isinstance(content, dict):
        content_str = json.dumps(content, ensure_ascii=False, indent=2)
    else:
        content_str = content if isinstance(content, str) else content.decode("utf-8")

    disk_path.write_text(content_str, encoding="utf-8")

    content_hash = _hash_content(content_str)

    entry = OutputEntry(
        output_id=make_output_id(),
        output_type=output_type,
        contract_id=contract_id,
        file_path=str(disk_path.relative_to(exports_root)),
        status="submitted",
        submitted_at=ts,
    )
    wo.add_output(entry)
    _persist_work_order(wo, wo_dir)

    if registry is not None:
        reg_entry = OutputRegistryEntry(
            output_id=entry.output_id,
            work_order_id=wo.work_order_id,
            output_type=entry.output_type,
            contract_id=entry.contract_id,
            status=entry.status,
            disk_path=entry.file_path,
            submitted_at=ts,
            content_hash=content_hash,
        )
        registry.add(reg_entry)

    return entry, str(disk_path)


def collect_outputs_batch(
    wo: WorkOrder,
    outputs: list[tuple[OutputType, str | bytes | dict, str]],  # (type, content, contract_id)
    *,
    exports_root: Path = DEFAULT_EXPORTS_ROOT,
    registry: OutputRegistry | None = None,
) -> list[tuple[OutputEntry, str]]:
    """Collect multiple outputs at once."""
    results: list[tuple[OutputEntry, str]] = []
    for out_type, content, contract_id in outputs:
        entry, path = collect_output(
            wo, out_type, content, contract_id,
            exports_root=exports_root, registry=registry,
        )
        results.append((entry, path))
    return results


def validate_output(
    wo: WorkOrder,
    output_id: str,
    *,
    exports_root: Path = DEFAULT_EXPORTS_ROOT,
    registry: OutputRegistry | None = None,
    notes: str = "",
) -> OutputEntry | None:
    """Mark an output as validated."""
    ts = datetime.now(timezone.utc).isoformat()
    for entry in wo.outputs:
        if entry.output_id == output_id:
            entry.status = "validated"
            entry.validated_at = ts
            if notes:
                entry.notes = notes
            wo.updated_at = ts
            _persist_work_order(wo, exports_root / wo.work_order_id)

            if registry:
                for reg_entry in registry.entries:
                    if reg_entry.output_id == output_id:
                        reg_entry.status = "validated"
                        reg_entry.validated_at = ts
                        registry._save()
                        break
            return entry
    return None


def reject_output(
    wo: WorkOrder,
    output_id: str,
    *,
    exports_root: Path = DEFAULT_EXPORTS_ROOT,
    registry: OutputRegistry | None = None,
    notes: str = "",
) -> OutputEntry | None:
    """Mark an output as rejected."""
    ts = datetime.now(timezone.utc).isoformat()
    for entry in wo.outputs:
        if entry.output_id == output_id:
            entry.status = "rejected"
            entry.notes = notes
            wo.updated_at = ts
            _persist_work_order(wo, exports_root / wo.work_order_id)

            if registry:
                for reg_entry in registry.entries:
                    if reg_entry.output_id == output_id:
                        reg_entry.status = "rejected"
                        registry._save()
                        break
            return entry
    return None


def list_collected_outputs(
    work_order_id: str,
    exports_root: Path = DEFAULT_EXPORTS_ROOT,
) -> list[OutputEntry]:
    """List all collected outputs for a work order from disk."""
    wo_dir = exports_root / work_order_id
    manifest_path = wo_dir / "work_order.json"
    if not manifest_path.exists():
        return []

    from src.work_order.models import WorkOrder
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    wo = WorkOrder.from_dict(data)
    return wo.outputs


def _persist_work_order(wo: WorkOrder, wo_dir: Path):
    wo_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = wo_dir / "work_order.json"
    manifest_path.write_text(
        json.dumps(wo.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _extension_for_type(output_type: OutputType) -> str:
    _map = {
        OutputType.MARKDOWN: "md",
        OutputType.JSON: "json",
        OutputType.HTML_PREVIEW: "html",
        OutputType.ZIP_PACKAGE: "zip",
        OutputType.IMAGE_ASSET: "png",
        OutputType.VIDEO_PLAN: "json",
        OutputType.DELIVERY_PACKAGE: "json",
        OutputType.MISSION_REPORT: "md",
        OutputType.UNKNOWN: "txt",
    }
    return _map.get(output_type, "txt")
