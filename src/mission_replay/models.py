"""Mission Replay data models."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class ReplaySession:
    session_id: str
    original_mission_id: str
    variant_name: str
    status: str = "created"  # created, running, completed, failed
    original_path: Optional[str] = None
    replay_path: Optional[str] = None
    variant_changes: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
    completed_at: Optional[str] = None
    output_count: int = 0
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "ReplaySession":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class DiffEntry:
    """Single difference between original and replay."""
    file_path: str
    change_type: str  # added, removed, modified, unchanged
    original_size: int = 0
    replay_size: int = 0
    original_hash: Optional[str] = None
    replay_hash: Optional[str] = None
    lines_added: int = 0
    lines_removed: int = 0
    summary: str = ""


@dataclass
class DiffReport:
    session_id: str
    original_mission_id: str
    variant_name: str
    entries: list[DiffEntry] = field(default_factory=list)
    total_files: int = 0
    files_added: int = 0
    files_removed: int = 0
    files_modified: int = 0
    files_unchanged: int = 0
    total_lines_added: int = 0
    total_lines_removed: int = 0
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"))

    @property
    def has_changes(self) -> bool:
        return self.files_added + self.files_removed + self.files_modified > 0

    def to_dict(self) -> dict:
        d = asdict(self)
        d["entries"] = [asdict(e) for e in self.entries]
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "DiffReport":
        entries = [DiffEntry(**e) for e in d.pop("entries", [])]
        report = cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})
        report.entries = entries
        return report
