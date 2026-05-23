"""Filesystem Health Bridge — OMNIS Control ↔ KRATOS health contract via JSON file.

Writes to ~/.claude/state/omnis_health.json so KRATOS can read OMNIS health
without needing a live HTTP endpoint. This is the canonical health bridge
between the two systems when the OMNIS Control API is not running.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_HEALTH_PATH = Path(os.getenv("CLAUDE_DIR", str(Path.home() / ".claude"))) / "state" / "omnis_health.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_health_file(
    components: dict[str, dict[str, Any]],
    path: Path | None = None,
) -> Path:
    """Write a health snapshot to the filesystem bridge.

    Args:
        components: Dict of component_name → {status, score, message, ...}
        path: Optional override path. Defaults to ~/.claude/state/omnis_health.json

    Returns the path written to.
    """
    target = path or DEFAULT_HEALTH_PATH
    target.parent.mkdir(parents=True, exist_ok=True)

    overall = _compute_overall(components)

    report = {
        "timestamp": _now(),
        "overall_status": overall["status"],
        "overall_score": overall["score"],
        "component_count": len(components),
        "healthy_count": sum(1 for c in components.values() if c.get("status") == "healthy"),
        "degraded_count": sum(1 for c in components.values() if c.get("status") == "degraded"),
        "unhealthy_count": sum(1 for c in components.values() if c.get("status") == "unhealthy"),
        "components": components,
    }

    target.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    return target


def read_health_file(path: Path | None = None) -> dict[str, Any] | None:
    """Read the health snapshot from the filesystem bridge.

    Returns None if the file doesn't exist or is unreadable.
    """
    target = path or DEFAULT_HEALTH_PATH
    if not target.exists():
        return None
    try:
        return json.loads(target.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def _compute_overall(components: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Compute overall health from component statuses."""
    if not components:
        return {"status": "unknown", "score": 0.0}

    statuses = [c.get("status", "unknown") for c in components.values()]
    scores = [c.get("score", 0.0) for c in components.values()]

    avg_score = sum(scores) / len(scores) if scores else 0.0

    if "unhealthy" in statuses:
        overall = "unhealthy"
    elif "degraded" in statuses:
        overall = "degraded"
    elif all(s == "healthy" for s in statuses):
        overall = "healthy"
    else:
        overall = "unknown"

    return {"status": overall, "score": round(avg_score, 4)}
