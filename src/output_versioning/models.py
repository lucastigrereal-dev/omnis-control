"""Output Versioning data models."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional


@dataclass
class VersionEntry:
    version: int
    path: str
    size: int
    hash: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
    changelog: str = ""
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "VersionEntry":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class VersionedOutput:
    output_id: str
    name: str
    current_version: int = 1
    versions: list[VersionEntry] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
    status: str = "active"  # active, archived, rolled_back

    @property
    def latest(self) -> Optional[VersionEntry]:
        return self.versions[-1] if self.versions else None

    @property
    def version_count(self) -> int:
        return len(self.versions)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["versions"] = [v.to_dict() for v in self.versions]
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "VersionedOutput":
        versions = [VersionEntry.from_dict(v) for v in d.pop("versions", [])]
        output = cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})
        output.versions = versions
        return output


@dataclass
class DiffResult:
    output_id: str
    version_a: int
    version_b: int
    same_hash: bool = False
    size_delta: int = 0
    lines_added: int = 0
    lines_removed: int = 0
    summary: str = ""

    @property
    def is_identical(self) -> bool:
        return self.same_hash and self.size_delta == 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Changelog:
    output_id: str
    entries: list[dict] = field(default_factory=list)

    def add(self, version: int, message: str) -> None:
        self.entries.append({
            "version": version,
            "message": message,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        })

    def to_dict(self) -> dict:
        return asdict(self)
