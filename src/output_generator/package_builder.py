"""Package Builder — multi-file output package per work order."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from src.output_generator.csv_writer import write_csv_output
from src.output_generator.json_writer import write_json_output, write_spec_output
from src.output_generator.markdown_writer import write_markdown_output
from src.output_generator.models import GeneratedOutput, GeneratedOutputStatus
from src.work_order.models import WorkOrder


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def build_package(
    work_order: WorkOrder,
    output_root: Path,
) -> tuple[Path, list[GeneratedOutput], list[str]]:
    """Generate all applicable outputs for a work order into a single package directory.

    Returns (package_dir, outputs, blockers).
    """
    from src.work_order.models import make_output_id

    package_id = make_output_id()
    pkg_dir = output_root / package_id
    pkg_dir.mkdir(parents=True, exist_ok=True)

    outputs: list[GeneratedOutput] = []
    blockers: list[str] = []

    # Determine what to generate based on contracts
    for contract in work_order.contracts:
        otype = contract.output_type.value
        try:
            if otype == "markdown":
                out = write_markdown_output(work_order, pkg_dir)
                outputs.append(out)
            elif otype == "json":
                out = write_json_output(work_order, pkg_dir)
                outputs.append(out)
            elif otype in ("technical_spec", "app_spec", "data_model"):
                out = write_spec_output(work_order, pkg_dir)
                outputs.append(out)
            elif otype == "csv":
                out = write_csv_output(work_order, pkg_dir, table_type="list")
                outputs.append(out)
        except Exception as exc:
            blockers.append(f"Failed to generate {otype}: {exc}")

    # Always generate markdown if no contracts matched anything
    if not outputs:
        out = write_markdown_output(work_order, pkg_dir)
        outputs.append(out)

    # Write package manifest
    ts = datetime.now(timezone.utc).isoformat()
    manifest = {
        "package_id": package_id,
        "work_order_id": work_order.work_order_id,
        "created_at": ts,
        "outputs": [o.to_dict() for o in outputs],
        "blockers": blockers,
        "file_count": len(outputs),
    }
    manifest_path = pkg_dir / "package_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    return pkg_dir, outputs, blockers
