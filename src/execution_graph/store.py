"""Execution Graph Store — JSONL append-only persistence for graph runs."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

BASE = Path(__file__).resolve().parent.parent.parent
DEFAULT_STORE_ROOT = BASE / "exports" / "graph_runs"


def append_event(run_dir: Path, event: dict) -> Path:
    """Append a single JSONL line event to a run's events file."""
    run_dir.mkdir(parents=True, exist_ok=True)
    events_file = run_dir / "events.jsonl"
    with open(events_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    return events_file


def read_events(run_dir: Path) -> list[dict]:
    """Read all events from a run's JSONL file."""
    events_file = run_dir / "events.jsonl"
    if not events_file.exists():
        return []
    events: list[dict] = []
    with open(events_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events


def get_step_state(run_dir: Path) -> dict[str, str]:
    """Rebuild current step status map from JSONL events."""
    events = read_events(run_dir)
    state: dict[str, str] = {}
    for e in events:
        if "step_id" in e and "status" in e:
            state[e["step_id"]] = e["status"]
    return state


def write_manifest(run_dir: Path, manifest: dict) -> Path:
    """Write the run manifest JSON."""
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest_file = run_dir / "manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    return manifest_file


def read_manifest(run_dir: Path) -> Optional[dict]:
    """Read the run manifest JSON."""
    manifest_file = run_dir / "manifest.json"
    if not manifest_file.exists():
        return None
    with open(manifest_file, "r", encoding="utf-8") as f:
        return json.load(f)
