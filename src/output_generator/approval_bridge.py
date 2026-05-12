"""Approval Submission Bridge — prepara pacotes de output para approval_center."""
from __future__ import annotations

from pathlib import Path

from src.output_generator.manifest_registry import ManifestRegistry
from src.output_generator.validator import validate_package


def prepare_submission(
    work_order_id: str,
    registry: ManifestRegistry | None = None,
    approvals_log: Path | None = None,
    dry_run: bool = True,
) -> dict:
    """Validate package and prepare approval submission for a work order.

    Returns a dict with: work_order_id, valid, checks, issues, warnings,
    approval_request (None if not submitted), dry_run.
    """
    reg = registry or ManifestRegistry()
    result = validate_package(work_order_id, registry=reg)

    entries = reg.list_by_work_order(work_order_id)
    file_list = [e["file_path"] for e in entries]
    types = list({e["output_type"] for e in entries})

    subject = f"Output Package: {work_order_id}"
    description_lines = [
        f"Work Order: {work_order_id}",
        f"Files: {len(entries)}",
        f"Output types: {', '.join(sorted(types))}",
    ]
    description = " | ".join(description_lines)

    approval_request = None
    if result.valid and not dry_run:
        from src.approval_center.service import request_approval

        req = request_approval(
            subject=subject,
            description=description,
            capability_id="output_generator",
            risk_level="low",
            approvals_log=approvals_log,
        )
        approval_request = {
            "request_id": req.request_id,
            "subject": req.subject,
            "status": req.status,
            "requested_at": req.requested_at,
        }

    return {
        "work_order_id": work_order_id,
        "valid": result.valid,
        "checks": result.checks,
        "issues": result.issues,
        "warnings": result.warnings,
        "file_count": len(entries),
        "output_types": sorted(types),
        "files": file_list,
        "approval_request": approval_request,
        "dry_run": dry_run,
    }
