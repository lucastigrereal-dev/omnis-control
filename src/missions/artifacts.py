"""Artifact Registry — enriched artifact tracking with path traversal prevention."""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ArtifactKind(str, Enum):
    REPORT = "report"
    IMAGE = "image"
    VIDEO = "video"
    CAPTION = "caption"
    CONTRACT = "contract"
    LOG = "log"
    CHECKPOINT = "checkpoint"
    PACKAGE = "package"
    OTHER = "other"


class ArtifactStatus(str, Enum):
    CREATED = "created"
    LINKED = "linked"
    VERIFIED = "verified"
    CORRUPTED = "corrupted"
    DELETED = "deleted"


class Artifact(BaseModel):
    """Enriched artifact — path, kind, hash, metadata."""

    model_config = ConfigDict(frozen=True)

    path: str
    kind: ArtifactKind = ArtifactKind.OTHER
    sha256: str = ""
    size_bytes: int = 0
    status: ArtifactStatus = ArtifactStatus.CREATED
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    verified_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    source_step: str = ""
    content_type: str = ""

    def compute_hash(self) -> str:
        raw = json.dumps(
            {"path": self.path, "kind": self.kind.value, "size_bytes": self.size_bytes, "created_at": self.created_at.isoformat()},
            sort_keys=True, ensure_ascii=True, separators=(",", ":"),
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Artifact":
        return cls(**data)


class PathTraversalError(Exception):
    """Tentativa de path traversal detectada."""


class ArtifactRegistry:
    """File-backed artifact registry stored within the mission folder."""

    def __init__(self, mission_dir: str) -> None:
        self.mission_dir = Path(mission_dir)
        self.registry_path = self.mission_dir / "artifacts.jsonl"
        self._safe_base = self.mission_dir.resolve()

    @staticmethod
    def _prevent_traversal(base: Path, target: str) -> Path:
        resolved = (base / target).resolve()
        if not str(resolved).startswith(str(base)):
            raise PathTraversalError(f"Path traversal blocked: {target}")
        return resolved

    def register(self, artifact: Artifact) -> Artifact:
        if not artifact.sha256:
            artifact = artifact.model_copy(update={"sha256": artifact.compute_hash()})

        self._prevent_traversal(self._safe_base, artifact.path)

        entry = artifact.to_dict()
        with open(self.registry_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=True, separators=(",", ":")) + "\n")

        return artifact

    def register_file(self, relative_path: str, kind: ArtifactKind = ArtifactKind.OTHER) -> Artifact:
        self._prevent_traversal(self._safe_base, relative_path)
        full_path = self.mission_dir / relative_path

        sha256 = ""
        size_bytes = 0
        if full_path.exists() and full_path.is_file():
            content = full_path.read_bytes()
            sha256 = hashlib.sha256(content).hexdigest()
            size_bytes = len(content)

        artifact = Artifact(
            path=relative_path,
            kind=kind,
            sha256=sha256,
            size_bytes=size_bytes,
            status=ArtifactStatus.CREATED,
        )
        return self.register(artifact)

    def list_all(self) -> List[Artifact]:
        if not self.registry_path.exists():
            return []
        artifacts: List[Artifact] = []
        with open(self.registry_path, encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    artifacts.append(Artifact.from_dict(json.loads(stripped)))
                except (json.JSONDecodeError, Exception):
                    continue
        return artifacts

    def list_by_kind(self, kind: ArtifactKind) -> List[Artifact]:
        return [a for a in self.list_all() if a.kind == kind]

    def find_by_path(self, relative_path: str) -> Optional[Artifact]:
        for a in self.list_all():
            if a.path == relative_path:
                return a
        return None

    def verify_all(self) -> Dict[str, List[str]]:
        result: Dict[str, List[str]] = {"verified": [], "corrupted": [], "missing": []}
        for a in self.list_all():
            full_path = self.mission_dir / a.path
            if not full_path.exists():
                result["missing"].append(a.path)
                continue
            actual = hashlib.sha256(full_path.read_bytes()).hexdigest()
            if actual != a.sha256:
                result["corrupted"].append(a.path)
            else:
                result["verified"].append(a.path)
        return result

    def count(self) -> int:
        return len(self.list_all())
