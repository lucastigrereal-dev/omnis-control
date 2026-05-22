"""Single canonical decision log for the OMNIS ecosystem.

JSONL-backed audit trail for every governance decision.
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DEFAULT_LOG_PATH = os.path.expanduser("~/.claude/logs/governance_audit.jsonl")


class DecisionLog:
    """Append-only JSONL audit log for governance decisions."""

    def __init__(self, log_path: str | None = None):
        self._path = Path(log_path or DEFAULT_LOG_PATH)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, request, result, override: bool = False) -> dict:
        """Log an approval decision to the audit trail."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": request.request_id,
            "action": request.action,
            "context": request.context,
            "risk_level": result.risk_level,
            "risk_name": result.risk_name,
            "decision": result.decision.value,
            "reason": result.reason,
            "requires_human": result.requires_human,
            "override": override,
        }
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry

    def read(self, limit: int = 100) -> list[dict]:
        """Read recent audit entries."""
        if not self._path.exists():
            return []
        entries = []
        with open(self._path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))
        return entries[-limit:]

    def query(self, decision: str | None = None, risk_level: int | None = None) -> list[dict]:
        """Filter audit entries by decision and/or risk level."""
        entries = self.read(limit=0)
        if decision:
            entries = [e for e in entries if e["decision"] == decision]
        if risk_level is not None:
            entries = [e for e in entries if e["risk_level"] == risk_level]
        return entries
