"""Markdown Output Writer — deterministic generator for markdown outputs."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from src.output_generator.models import GeneratedOutput, GeneratedOutputStatus
from src.work_order.models import WorkOrder


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def _build_markdown_content(wo: WorkOrder) -> str:
    title = wo.step_label or "Untitled Output"
    role = wo.role or "unknown"
    expected = wo.metadata.get("expected_output", "No expected output specified")
    risk = wo.metadata.get("estimated_duration", "not specified")
    brief = wo.metadata.get("request", wo.metadata.get("expected_output", ""))

    lines = [
        f"# Output: {title}",
        "",
        "## Work Order",
        f"- **ID:** {wo.work_order_id}",
        f"- **Role:** {role}",
        f"- **Expected output:** {expected}",
        f"- **Risk:** {risk}",
        "",
        "## Brief",
        f"{brief}",
        "",
        "## Draft Output",
        f"<!-- Conteudo deterministico baseado no work order {wo.work_order_id} -->",
        "",
        f"_Output gerado automaticamente pelo {role} — revisar manualmente antes de submeter._",
        "",
        "## Acceptance Criteria",
    ]

    for contract in wo.contracts:
        lines.append(f"- [{contract.output_type.value}] {contract.description}")

    lines.extend([
        "",
        "## Next Actions",
        "- Review manually",
        "- Submit to work-order collector",
    ])

    return "\n".join(lines) + "\n"


def write_markdown_output(
    work_order: WorkOrder,
    output_root: Path,
    *,
    generator_id: str = "markdown_basic_writer",
) -> GeneratedOutput:
    ts = datetime.now(timezone.utc).isoformat()

    md_contracts = [c for c in work_order.contracts if c.output_type.value == "markdown"]
    if not md_contracts:
        warnings = ["No markdown contract found — generating anyway"]

    from src.work_order.models import make_output_id

    output_id = make_output_id()
    out_dir = output_root / output_id
    out_dir.mkdir(parents=True, exist_ok=True)

    md_path = out_dir / "generated_output.md"
    content = _build_markdown_content(work_order)
    md_path.write_text(content, encoding="utf-8")

    fingerprint = _hash_file(md_path)

    manifest = {
        "output_id": output_id,
        "work_order_id": work_order.work_order_id,
        "output_type": "markdown",
        "generator_id": generator_id,
        "file": "generated_output.md",
        "fingerprint": fingerprint,
        "created_at": ts,
    }
    manifest_path = out_dir / "output_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    return GeneratedOutput(
        output_id=output_id,
        work_order_id=work_order.work_order_id,
        output_type="markdown",
        generator_id=generator_id,
        file_path=str(md_path),
        status=GeneratedOutputStatus.GENERATED,
        fingerprint=fingerprint,
        created_at=ts,
        warnings=(["No markdown contract found — generating anyway"] if not md_contracts else []),
        blockers=[],
    )
