"""CSV / Table Output Writers — deterministic generators for csv and table outputs."""
from __future__ import annotations

import csv
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path

from src.output_generator.models import GeneratedOutput, GeneratedOutputStatus
from src.work_order.models import WorkOrder


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def _build_csv_rows(wo: WorkOrder, table_type: str) -> list[list[str]]:
    if table_type == "calendar":
        rows = [["date", "title", "description", "role", "status"]]
        for i, contract in enumerate(wo.contracts):
            rows.append([
                f"2026-05-{(i + 1):02d}",
                contract.description[:50],
                contract.description,
                wo.role,
                "planned",
            ])
    elif table_type == "list":
        rows = [["index", "contract_id", "output_type", "description", "required"]]
        for i, contract in enumerate(wo.contracts, 1):
            rows.append([
                str(i),
                contract.contract_id,
                contract.output_type.value,
                contract.description,
                str(contract.required),
            ])
    elif table_type == "queue":
        rows = [["position", "contract_id", "description", "priority", "status"]]
        for i, contract in enumerate(wo.contracts, 1):
            priority = "high" if contract.required else "low"
            rows.append([
                str(i),
                contract.contract_id,
                contract.description,
                priority,
                "pending",
            ])
    else:
        rows = [["contract_id", "output_type", "description", "required"]]
        for contract in wo.contracts:
            rows.append([
                contract.contract_id,
                contract.output_type.value,
                contract.description,
                str(contract.required),
            ])

    return rows


def _write_csv(rows: list[list[str]], path: Path) -> None:
    content = io.StringIO()
    writer = csv.writer(content, lineterminator="\n")
    writer.writerows(rows)
    path.write_text(content.getvalue(), encoding="utf-8")


def write_csv_output(
    work_order: WorkOrder,
    output_root: Path,
    *,
    generator_id: str = "csv_basic_writer",
    table_type: str = "list",
) -> GeneratedOutput:
    ts = datetime.now(timezone.utc).isoformat()

    csv_contracts = [c for c in work_order.contracts if c.output_type.value == "csv"]
    warnings = [] if csv_contracts else ["No csv contract found — generating anyway"]

    from src.work_order.models import make_output_id

    output_id = make_output_id()
    out_dir = output_root / output_id
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_path = out_dir / "generated_output.csv"
    rows = _build_csv_rows(work_order, table_type)
    _write_csv(rows, csv_path)

    fingerprint = _hash_file(csv_path)

    manifest = {
        "output_id": output_id,
        "work_order_id": work_order.work_order_id,
        "output_type": "csv",
        "generator_id": generator_id,
        "file": "generated_output.csv",
        "fingerprint": fingerprint,
        "created_at": ts,
        "table_type": table_type,
    }
    manifest_path = out_dir / "output_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    return GeneratedOutput(
        output_id=output_id,
        work_order_id=work_order.work_order_id,
        output_type="csv",
        generator_id=generator_id,
        file_path=str(csv_path),
        status=GeneratedOutputStatus.GENERATED,
        fingerprint=fingerprint,
        created_at=ts,
        warnings=warnings,
        blockers=[],
    )
