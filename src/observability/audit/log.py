"""Audit module — append-only audit log, immutable record of all system actions.

Every significant action in OMNIS produces an audit entry.
Audit entries are append-only, immutable, and structured.

Contracts:
    - Never delete or modify audit entries
    - Every entry has a timestamp, actor, action, and outcome
    - Entries are serializable to JSONL for long-term storage
    - Audit log is replayable for compliance verification
"""

import json
import logging
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AuditAction(str, Enum):
    """Categorizes the type of audited action."""
    MISSION_START = "mission_start"
    MISSION_COMPLETE = "mission_complete"
    DECISION = "decision"
    EXECUTION = "execution"
    ROLLBACK = "rollback"
    APPROVAL = "approval"
    ERROR = "error"
    CONFIG_CHANGE = "config_change"
    DEPLOY = "deploy"
    ACCESS = "access"


class AuditEntry(BaseModel):
    """A single immutable audit entry.

    Written once, never modified. Stored as JSONL.
    """

    model_config = {"frozen": True}

    entry_id: str = Field(..., description="UUID for this entry")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    actor: str = Field(..., description="Who/what performed the action")
    action: AuditAction
    resource: str = Field(..., description="What was acted upon")
    outcome: str = Field(..., description="Result of the action")
    detail: dict[str, Any] = Field(default_factory=dict)
    mission_id: str | None = None
    trace_id: str | None = None
    sequence: int = Field(..., ge=0)

    def to_jsonl(self) -> str:
        return self.model_dump_json()


class AuditLog:
    """Append-only audit log backed by JSONL files.

    Writes to data/audit/YYYYMMDD.jsonl by default.
    Rotation at midnight UTC.

    Usage:
        audit = AuditLog()
        audit.record(
            actor="mission_orchestrator",
            action=AuditAction.MISSION_START,
            resource="mission_123",
            outcome="started",
            detail={"plan": "..."},
        )
    """

    def __init__(self, base_dir: str | None = None):
        self._base_dir = Path(base_dir or "data/audit")
        self._base_dir.mkdir(parents=True, exist_ok=True)
        self._sequence = 0
        self._current_file: Path | None = None

    def record(
        self,
        actor: str,
        action: AuditAction,
        resource: str,
        outcome: str,
        detail: dict[str, Any] | None = None,
        mission_id: str | None = None,
        trace_id: str | None = None,
    ) -> AuditEntry:
        from uuid import uuid4

        self._sequence += 1
        entry = AuditEntry(
            entry_id=str(uuid4()),
            actor=actor,
            action=action,
            resource=resource,
            outcome=outcome,
            detail=detail or {},
            mission_id=mission_id,
            trace_id=trace_id,
            sequence=self._sequence,
        )

        filepath = self._get_filepath()
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(entry.to_jsonl() + "\n")

        logger.debug("Audit: %s %s → %s", action.value, resource, outcome)
        return entry

    def _get_filepath(self) -> Path:
        today = datetime.now(timezone.utc).strftime("%Y%m%d")
        filepath = self._base_dir / f"{today}.jsonl"
        return filepath

    def read_range(
        self, start: datetime, end: datetime, action: AuditAction | None = None
    ) -> list[AuditEntry]:
        """Read audit entries in a time range, optionally filtered by action."""
        entries: list[AuditEntry] = []
        current = start
        while current <= end:
            filepath = self._base_dir / f"{current.strftime('%Y%m%d')}.jsonl"
            if filepath.exists():
                for line in filepath.read_text(encoding="utf-8").splitlines():
                    if not line.strip():
                        continue
                    try:
                        entry = AuditEntry.model_validate_json(line)
                        ts = entry.timestamp
                        if start <= ts <= end:
                            if action is None or entry.action == action:
                                entries.append(entry)
                    except Exception:
                        logger.warning("Corrupt audit entry in %s", filepath)
            current = datetime(current.year, current.month, current.day)
            from datetime import timedelta
            current += timedelta(days=1)

        return entries

    def get_mission_audit_trail(self, mission_id: str) -> list[AuditEntry]:
        """Get all audit entries for a specific mission."""
        entries: list[AuditEntry] = []
        for filepath in sorted(self._base_dir.glob("*.jsonl")):
            for line in filepath.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    entry = AuditEntry.model_validate_json(line)
                    if entry.mission_id == mission_id:
                        entries.append(entry)
                except Exception:
                    continue
        return entries


_audit_log: AuditLog | None = None


def get_audit_log(base_dir: str | None = None) -> AuditLog:
    global _audit_log
    if _audit_log is None:
        _audit_log = AuditLog(base_dir)
    return _audit_log
