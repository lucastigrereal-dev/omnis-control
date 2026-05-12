"""JSON / Spec Output Writers — deterministic generators for json and spec outputs."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from src.output_generator.models import GeneratedOutput, GeneratedOutputStatus
from src.work_order.models import WorkOrder


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def _build_json_content(wo: WorkOrder) -> dict:
    return {
        "work_order": {
            "work_order_id": wo.work_order_id,
            "graph_step_id": wo.graph_step_id,
            "graph_run_id": wo.graph_run_id,
            "role": wo.role,
            "step_label": wo.step_label,
            "status": wo.status.value,
            "created_at": wo.created_at,
        },
        "contracts": [c.to_dict() for c in wo.contracts],
        "metadata": wo.metadata,
        "draft_output": {
            "title": wo.step_label or "Untitled Output",
            "role": wo.role,
            "expected_output": wo.metadata.get("expected_output", ""),
            "deliverables": [
                {"contract_id": c.contract_id, "type": c.output_type.value, "description": c.description}
                for c in wo.contracts
            ],
        },
    }


def _build_spec_content(wo: WorkOrder) -> dict:
    spec_type = wo.metadata.get("spec_type", "technical_spec")
    return {
        "spec": {
            "spec_id": wo.work_order_id,
            "spec_type": spec_type,
            "title": wo.step_label or "Untitled Spec",
            "role": wo.role,
            "status": "draft",
            "created_at": wo.created_at,
        },
        "requirements": [
            {
                "id": c.contract_id,
                "type": c.output_type.value,
                "description": c.description,
                "required": c.required,
            }
            for c in wo.contracts
        ],
        "metadata": wo.metadata,
        "sections": {
            "overview": wo.metadata.get("expected_output", ""),
            "scope": f"Auto-generated spec from work order {wo.work_order_id}",
            "acceptance_criteria": [c.description for c in wo.contracts],
        },
    }


def write_json_output(
    work_order: WorkOrder,
    output_root: Path,
    *,
    generator_id: str = "json_basic_writer",
) -> GeneratedOutput:
    ts = datetime.now(timezone.utc).isoformat()

    json_contracts = [c for c in work_order.contracts if c.output_type.value == "json"]
    warnings = [] if json_contracts else ["No json contract found — generating anyway"]

    from src.work_order.models import make_output_id

    output_id = make_output_id()
    out_dir = output_root / output_id
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / "generated_output.json"
    content = _build_json_content(work_order)
    json_path.write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")

    fingerprint = _hash_file(json_path)

    manifest = {
        "output_id": output_id,
        "work_order_id": work_order.work_order_id,
        "output_type": "json",
        "generator_id": generator_id,
        "file": "generated_output.json",
        "fingerprint": fingerprint,
        "created_at": ts,
    }
    manifest_path = out_dir / "output_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    return GeneratedOutput(
        output_id=output_id,
        work_order_id=work_order.work_order_id,
        output_type="json",
        generator_id=generator_id,
        file_path=str(json_path),
        status=GeneratedOutputStatus.GENERATED,
        fingerprint=fingerprint,
        created_at=ts,
        warnings=warnings,
        blockers=[],
    )


def write_spec_output(
    work_order: WorkOrder,
    output_root: Path,
    *,
    generator_id: str = "spec_basic_writer",
) -> GeneratedOutput:
    ts = datetime.now(timezone.utc).isoformat()

    valid_spec_types = {"technical_spec", "app_spec", "data_model"}
    spec_contracts = [c for c in work_order.contracts if c.output_type.value in valid_spec_types]
    warnings = [] if spec_contracts else ["No spec contract found — generating as technical_spec"]

    from src.work_order.models import make_output_id

    output_id = make_output_id()
    out_dir = output_root / output_id
    out_dir.mkdir(parents=True, exist_ok=True)

    spec_path = out_dir / "generated_spec.json"
    content = _build_spec_content(work_order)
    spec_path.write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")

    fingerprint = _hash_file(spec_path)

    spec_type = spec_contracts[0].output_type.value if spec_contracts else "technical_spec"

    manifest = {
        "output_id": output_id,
        "work_order_id": work_order.work_order_id,
        "output_type": spec_type,
        "generator_id": generator_id,
        "file": "generated_spec.json",
        "fingerprint": fingerprint,
        "created_at": ts,
    }
    manifest_path = out_dir / "output_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    return GeneratedOutput(
        output_id=output_id,
        work_order_id=work_order.work_order_id,
        output_type=spec_type,
        generator_id=generator_id,
        file_path=str(spec_path),
        status=GeneratedOutputStatus.GENERATED,
        fingerprint=fingerprint,
        created_at=ts,
        warnings=warnings,
        blockers=[],
    )
