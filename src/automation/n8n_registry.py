"""W144 — n8n Workflow Registry (in-memory, JSONL-backed)."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .models import AutomationWorkflow, _now_iso, _new_id
from .n8n_bridge import N8nBridge, N8nWorkflowExport


@dataclass
class N8nRegistryEntry:
    entry_id: str
    workflow_id: str
    workflow_name: str
    export: N8nWorkflowExport
    registered_at: str = field(default_factory=_now_iso)
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "export": self.export.to_dict(),
            "registered_at": self.registered_at,
            "tags": self.tags,
        }


class N8nWorkflowRegistry:
    """In-memory registry of exported n8n workflows."""

    def __init__(self) -> None:
        self._entries: dict[str, N8nRegistryEntry] = {}
        self._bridge = N8nBridge()

    def register(self, workflow: AutomationWorkflow, tags: Optional[list[str]] = None, dry_run: bool = True) -> N8nRegistryEntry:
        export = self._bridge.export_workflow(workflow, dry_run=dry_run)
        entry = N8nRegistryEntry(
            entry_id=_new_id("reg"),
            workflow_id=workflow.workflow_id,
            workflow_name=workflow.name,
            export=export,
            tags=tags or [],
        )
        self._entries[entry.entry_id] = entry
        return entry

    def get(self, entry_id: str) -> Optional[N8nRegistryEntry]:
        return self._entries.get(entry_id)

    def list_all(self) -> list[N8nRegistryEntry]:
        return list(self._entries.values())

    def find_by_workflow_id(self, workflow_id: str) -> Optional[N8nRegistryEntry]:
        for e in self._entries.values():
            if e.workflow_id == workflow_id:
                return e
        return None

    def find_by_tag(self, tag: str) -> list[N8nRegistryEntry]:
        return [e for e in self._entries.values() if tag in e.tags]

    def count(self) -> int:
        return len(self._entries)

    def export_jsonl(self, path: str) -> int:
        """Export registry to JSONL (dry-run: only if path in /tmp or test paths)."""
        p = Path(path)
        if not any(part in str(p) for part in ["tmp", "temp", "test", ".pytest_tmp"]):
            raise ValueError(f"Export path not in safe zone: {path!r}")
        lines = [json.dumps(e.to_dict()) for e in self._entries.values()]
        p.write_text("\n".join(lines), encoding="utf-8")
        return len(lines)
