"""Execution Plan Manifest — persists structured plan for audit and replay."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.mission_orchestrator.models import OrchestratorRun


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_manifest(run: OrchestratorRun) -> dict:
    """Build an execution plan manifest dict from an OrchestratorRun.

    No secrets. No raw file paths outside the run folder.
    """
    risks = []
    if run.approval_required:
        risks.append("approval_required")
    if run.suggested_gap_ids:
        risks.append("capability_gaps_detected")
    if not run.matched_capabilities:
        risks.append("no_capability_matched")

    next_actions = _derive_next_actions(run)

    return {
        "run_id": run.run_id,
        "request": run.request_text,
        "sector": run.sector_id or "unknown",
        "intent": run.intent,
        "capabilities": run.matched_capabilities,
        "gaps": run.suggested_gap_ids,
        "approval_required": run.approval_required,
        "approval_id": run.approval_id,
        "status": run.status,
        "steps": [s.to_dict() for s in run.steps],
        "risks": risks,
        "next_actions": next_actions,
        "created_at": run.created_at,
        "manifest_generated_at": _now_iso(),
    }


def _derive_next_actions(run: OrchestratorRun) -> list[str]:
    actions = []
    if run.status == "blocked_pending_approval":
        if run.approval_id:
            actions.append(f"jarvis approvals-center approve {run.approval_id}")
        actions.append("jarvis approvals-center list --status pending")
    elif run.status == "blocked":
        actions.append("Check blockers in run manifest")
    elif run.status in ("planned", "dry_run"):
        if run.suggested_gap_ids:
            actions.append(f"jarvis capability-gap show {run.suggested_gap_ids[0]}")
            actions.append(f"jarvis capability-gap request-approval {run.suggested_gap_ids[0]}")
        if run.mission_id:
            actions.append(f"jarvis mission-report close {run.mission_id} completed")
    return actions


def write_manifest(run: OrchestratorRun, run_dir: Path) -> Path:
    """Write execution_plan_manifest.json to run_dir. Returns path."""
    manifest = build_manifest(run)
    out = run_dir / "execution_plan_manifest.json"
    run_dir.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def no_secrets_in_manifest(manifest: dict) -> bool:
    """Sanity check: no secret-like keys in the manifest."""
    forbidden_prefixes = ("meta_", "instagram_", "secret", "token", "password", "key", "auth")
    text = json.dumps(manifest).lower()
    for prefix in forbidden_prefixes:
        if f'"{prefix}' in text:
            return False
    return True
