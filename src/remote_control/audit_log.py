"""W159 — Command Audit Log: in-memory + JSONL-backed audit trail for remote commands."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .models import CommandStatus, _new_id, _now_iso


# ---------------------------------------------------------------------------
# Audit entry
# ---------------------------------------------------------------------------

@dataclass
class AuditEntry:
    entry_id: str = field(default_factory=lambda: _new_id("aud"))
    command_id: str = ""
    command: str = ""
    source: str = ""
    user_id: str = ""
    status: str = CommandStatus.RECEIVED.value
    risk: str = "LOW"
    dry_run: bool = True
    allowed: bool = True
    rejection_reason: str = ""
    output: str = ""
    error: str = ""
    recorded_at: str = field(default_factory=_now_iso)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "command_id": self.command_id,
            "command": self.command,
            "source": self.source,
            "user_id": self.user_id,
            "status": self.status,
            "risk": self.risk,
            "dry_run": self.dry_run,
            "allowed": self.allowed,
            "rejection_reason": self.rejection_reason,
            "output": self.output,
            "error": self.error,
            "recorded_at": self.recorded_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AuditEntry":
        return cls(
            entry_id=data.get("entry_id", _new_id("aud")),
            command_id=data.get("command_id", ""),
            command=data.get("command", ""),
            source=data.get("source", ""),
            user_id=data.get("user_id", ""),
            status=data.get("status", CommandStatus.RECEIVED.value),
            risk=data.get("risk", "LOW"),
            dry_run=data.get("dry_run", True),
            allowed=data.get("allowed", True),
            rejection_reason=data.get("rejection_reason", ""),
            output=data.get("output", ""),
            error=data.get("error", ""),
            recorded_at=data.get("recorded_at", _now_iso()),
            metadata=data.get("metadata", {}),
        )


# ---------------------------------------------------------------------------
# Filter
# ---------------------------------------------------------------------------

@dataclass
class AuditFilter:
    source: Optional[str] = None
    user_id: Optional[str] = None
    command: Optional[str] = None
    status: Optional[str] = None
    allowed_only: bool = False
    rejected_only: bool = False
    dry_run_only: Optional[bool] = None
    limit: int = 100

    def matches(self, entry: AuditEntry) -> bool:
        if self.source and entry.source != self.source:
            return False
        if self.user_id and entry.user_id != self.user_id:
            return False
        if self.command and entry.command != self.command:
            return False
        if self.status and entry.status != self.status:
            return False
        if self.allowed_only and not entry.allowed:
            return False
        if self.rejected_only and entry.allowed:
            return False
        if self.dry_run_only is not None and entry.dry_run != self.dry_run_only:
            return False
        return True


# ---------------------------------------------------------------------------
# Audit Log
# ---------------------------------------------------------------------------

class CommandAuditLog:
    """In-memory audit log with optional JSONL persistence."""

    def __init__(self, log_path: Optional[Path] = None) -> None:
        self._entries: list[AuditEntry] = []
        self._log_path = log_path
        if log_path and log_path.exists():
            self._load(log_path)

    # ------------------------------------------------------------------
    def record(self, entry: AuditEntry) -> AuditEntry:
        self._entries.append(entry)
        if self._log_path:
            self._append_line(entry)
        return entry

    def record_dict(self, data: dict) -> AuditEntry:
        return self.record(AuditEntry.from_dict(data))

    # ------------------------------------------------------------------
    def query(self, f: Optional[AuditFilter] = None) -> list[AuditEntry]:
        if f is None:
            return list(self._entries)
        results = [e for e in self._entries if f.matches(e)]
        return results[: f.limit]

    def get(self, command_id: str) -> Optional[AuditEntry]:
        for e in reversed(self._entries):
            if e.command_id == command_id:
                return e
        return None

    def get_all_for_command(self, command_id: str) -> list[AuditEntry]:
        return [e for e in self._entries if e.command_id == command_id]

    # ------------------------------------------------------------------
    def stats(self) -> dict:
        total = len(self._entries)
        allowed = sum(1 for e in self._entries if e.allowed)
        rejected = total - allowed
        dry = sum(1 for e in self._entries if e.dry_run)
        by_source: dict[str, int] = {}
        by_status: dict[str, int] = {}
        for e in self._entries:
            by_source[e.source] = by_source.get(e.source, 0) + 1
            by_status[e.status] = by_status.get(e.status, 0) + 1
        return {
            "total": total,
            "allowed": allowed,
            "rejected": rejected,
            "dry_run": dry,
            "by_source": by_source,
            "by_status": by_status,
        }

    def clear(self) -> None:
        self._entries.clear()

    # ------------------------------------------------------------------
    def _append_line(self, entry: AuditEntry) -> None:
        try:
            with self._log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry.to_dict()) + "\n")
        except OSError:
            pass

    def _load(self, path: Path) -> None:
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line:
                    self._entries.append(AuditEntry.from_dict(json.loads(line)))
        except (OSError, json.JSONDecodeError):
            pass

    def reload(self) -> None:
        if self._log_path and self._log_path.exists():
            self._entries.clear()
            self._load(self._log_path)
