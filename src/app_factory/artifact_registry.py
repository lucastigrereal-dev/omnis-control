"""In-memory and JSONL artifact registry for App Factory."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class ArtifactRegistryEntry:
    idea_id: str
    artifact_type: str
    artifact_id: str
    path: str = ""
    metadata: dict | None = None

    def to_dict(self) -> dict:
        return {
            "idea_id": self.idea_id,
            "artifact_type": self.artifact_type,
            "artifact_id": self.artifact_id,
            "path": self.path,
            "metadata": self.metadata or {},
        }


class ArtifactRegistry:
    """Registry of generated artifacts. Dry-run by default avoids writes."""

    def __init__(self, path: Optional[Path] = None, dry_run: bool = True) -> None:
        self.path = Path(path) if path else Path("data/app_factory/artifacts.jsonl")
        self.dry_run = dry_run
        self._entries: list[ArtifactRegistryEntry] = []

    def register(self, entry: ArtifactRegistryEntry) -> ArtifactRegistryEntry:
        self._entries.append(entry)
        if not self.dry_run:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")
        return entry

    def list_for_idea(self, idea_id: str) -> list[ArtifactRegistryEntry]:
        entries = [entry for entry in self._load() if entry.idea_id == idea_id]
        entries.extend(entry for entry in self._entries if entry.idea_id == idea_id)
        return entries

    def latest(self, idea_id: str, artifact_type: str) -> ArtifactRegistryEntry | None:
        matches = [entry for entry in self.list_for_idea(idea_id) if entry.artifact_type == artifact_type]
        return matches[-1] if matches else None

    def _load(self) -> list[ArtifactRegistryEntry]:
        if self.dry_run or not self.path.exists():
            return []
        entries: list[ArtifactRegistryEntry] = []
        with open(self.path, "r", encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                data = json.loads(line)
                entries.append(ArtifactRegistryEntry(
                    idea_id=data["idea_id"],
                    artifact_type=data["artifact_type"],
                    artifact_id=data["artifact_id"],
                    path=data.get("path", ""),
                    metadata=data.get("metadata", {}),
                ))
        return entries
