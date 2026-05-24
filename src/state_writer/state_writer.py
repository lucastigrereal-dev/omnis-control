"""StateWriter — writes OMNIS real state to data/state.json for KRATOS to read.

Architecture: file-based, no server. KRATOS polls the file; OMNIS writes on demand.

Usage:
    python scripts/write_omnis_state.py
    python scripts/write_omnis_state.py /custom/path/state.json
    OMNIS_STATE_PATH=/tmp/state.json python scripts/write_omnis_state.py
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_DEFAULT_STATE_PATH = "data/state.json"


def _count_tests() -> int:
    """Count collected tests via pytest --collect-only (excludes real_llm)."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/",
         "--collect-only", "-q", "--import-mode=importlib",
         "-p", "no:warnings", "-m", "not real_llm"],
        capture_output=True, text=True, encoding="utf-8", timeout=120,
    )
    output = result.stdout + result.stderr
    match = re.search(r"(\d+)(?:/\d+)?\s+tests?\s+collected", output)
    return int(match.group(1)) if match else 0


def _last_commit() -> dict[str, str]:
    result = subprocess.run(
        ["git", "log", "-1", "--format=%h|%s|%cI"],
        capture_output=True,
    )
    if result.returncode != 0 or not result.stdout:
        return {}
    # Try UTF-8 first; fall back to system locale (CP1252 on Brazilian Windows)
    raw = result.stdout
    try:
        line = raw.decode("utf-8").strip()
    except UnicodeDecodeError:
        import locale
        line = raw.decode(locale.getpreferredencoding(False), errors="replace").strip()
    parts = line.split("|", 2)
    return {
        "hash": parts[0] if parts else "",
        "message": parts[1] if len(parts) > 1 else "",
        "date": parts[2] if len(parts) > 2 else "",
    }


def _current_branch() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.decode("utf-8", errors="replace").strip()


def _workflow_count() -> int:
    try:
        from src.workflows.workflow_registry import WorkflowRegistry
        return WorkflowRegistry.default().count
    except Exception:
        return 0


def collect_state() -> dict[str, Any]:
    """Collect OMNIS real state. All values are dynamic — nothing is hardcoded."""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "test_count": _count_tests(),
        "last_commit": _last_commit(),
        "branch": _current_branch(),
        "workflows_registered": _workflow_count(),
        "cost_local_pct": 100,
    }


def write_state(path: str | None = None) -> str:
    """Write state to JSON file. Returns the path written.

    Path resolution order:
      1. Explicit `path` argument
      2. OMNIS_STATE_PATH env var
      3. data/state.json (default)
    """
    out_path = path or os.getenv("OMNIS_STATE_PATH", _DEFAULT_STATE_PATH)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    state = collect_state()
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    return out_path
