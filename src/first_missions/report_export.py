"""W194+W195 — Failure taxonomy + Mission Report Export (Markdown/JSON)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from src.first_missions.models import Mission, FailureCategory, MissionStatus, _now_iso
from src.first_missions.result_store import StoredResult


def classify_failure(error: str) -> FailureCategory:
    """Classify a failure error message into a category."""
    if not error:
        return FailureCategory.NONE
    el = error.lower()
    if any(k in el for k in ("validation", "invalid", "required", "missing")):
        return FailureCategory.VALIDATION
    if any(k in el for k in ("timeout", "timed out", "deadline")):
        return FailureCategory.TIMEOUT
    if any(k in el for k in ("storage", "io error", "permission", "write", "disk")):
        return FailureCategory.STORAGE
    if any(k in el for k in ("runtime", "exception", "error", "traceback")):
        return FailureCategory.RUNTIME
    return FailureCategory.UNKNOWN


def export_mission_json(mission: Mission, results: list[StoredResult]) -> dict:
    """Build a JSON-exportable mission report."""
    return {
        "mission": mission.to_dict(),
        "results": [r.to_dict() for r in results],
        "exported_at": _now_iso(),
    }


def export_mission_markdown(mission: Mission, results: list[StoredResult]) -> str:
    """Build a Markdown mission report."""
    lines = [
        f"# Mission Report: {mission.name}",
        "",
        f"- **ID:** `{mission.mission_id}`",
        f"- **Type:** {mission.mission_type.value}",
        f"- **Priority:** {mission.priority.value}",
        f"- **Status:** {mission.status.value}",
        f"- **Dry-run:** {'Yes' if mission.dry_run else 'No (LIVE)'}",
        f"- **Created:** {mission.created_at}",
    ]
    if mission.started_at:
        lines.append(f"- **Started:** {mission.started_at}")
    if mission.completed_at:
        lines.append(f"- **Completed:** {mission.completed_at}")
    if mission.error:
        cat = classify_failure(mission.error)
        lines.append(f"- **Error:** {mission.error}")
        lines.append(f"- **Failure Category:** {cat.value}")

    if mission.tags:
        lines.append(f"- **Tags:** {', '.join(mission.tags)}")

    lines.append("")
    lines.append("## Results")
    lines.append("")
    lines.append(f"| Result ID | Status | Duration | Stored At |")
    lines.append(f"|---|---|---|---|")
    for r in results:
        lines.append(f"| {r.result_id[:12]} | {r.status} | {r.duration_ms:.0f}ms | {r.stored_at[:16]} |")

    return "\n".join(lines)


def write_export(content: str, path: Path) -> None:
    """Safely write export content to a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    # Safety: only allow writing within allowed paths
    resolved = path.resolve()
    if not str(resolved).startswith(str(Path.home())):
        raise PermissionError(f"Export path must be under home directory: {resolved}")
    path.write_text(content, encoding="utf-8")
