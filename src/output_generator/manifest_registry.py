"""Manifest Registry — local JSONL log of all generated outputs."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


class ManifestRegistry:
    """Append-only JSONL registry of output manifests."""

    def __init__(self, registry_path: Path | None = None):
        self.registry_path = registry_path or Path("exports/generated_outputs/output_registry.jsonl")
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

    def register(self, output_id: str, work_order_id: str, output_type: str, file_path: str, generator_id: str, fingerprint: str = "") -> dict:
        entry = {
            "output_id": output_id,
            "work_order_id": work_order_id,
            "output_type": output_type,
            "file_path": file_path,
            "generator_id": generator_id,
            "fingerprint": fingerprint,
            "registered_at": datetime.now(timezone.utc).isoformat(),
        }
        with open(self.registry_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry

    def list_all(self) -> list[dict]:
        if not self.registry_path.exists():
            return []
        entries: list[dict] = []
        for line in self.registry_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                entries.append(json.loads(line))
        return entries

    def show(self, output_id: str) -> dict | None:
        for entry in self.list_all():
            if entry["output_id"] == output_id:
                return entry
        return None

    def list_by_work_order(self, work_order_id: str) -> list[dict]:
        return [e for e in self.list_all() if e["work_order_id"] == work_order_id]

    def count(self) -> int:
        return len(self.list_all())
