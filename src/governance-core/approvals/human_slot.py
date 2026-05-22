"""Human Slot enforcement for L4-L5 actions.

L4 (PRODUCTION) and L5 (DESTRUCTIVE) actions require explicit human approval.
This module provides the Human Slot gate — pause execution, notify operator,
wait for approval or timeout.

Channels (future): Claude Code prompt, Telegram, Dashboard alert.
Current: Claude Code prompt (immediate), file-based pending queue.
"""
import json
import os
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional

PENDING_QUEUE_PATH = os.path.expanduser("~/.claude/state/human_slot_pending.json")


class SlotDecision(str, Enum):
    APPROVED = "approved"
    DENIED = "denied"
    TIMED_OUT = "timed_out"
    PENDING = "pending"


class HumanSlot:
    """Human-in-the-loop gate for L4-L5 actions.

    Usage:
        slot = HumanSlot()
        decision = slot.request(
            action="deploy to production",
            risk_level=4,
            timeout_hours=24,
        )
        if decision == SlotDecision.APPROVED:
            execute()
    """

    def __init__(self, timeout_hours: int = 24):
        self._timeout_hours = timeout_hours
        self._queue_path = Path(PENDING_QUEUE_PATH)
        self._queue_path.parent.mkdir(parents=True, exist_ok=True)

    def request(self, action: str, risk_level: int, context: dict | None = None,
                timeout_hours: int | None = None) -> SlotDecision:
        """Request human approval for a high-risk action.

        Writes to pending queue. Returns decision (currently always PENDING —
        the actual decision comes from the operator through Claude Code or
        another channel).

        In a fully automated system, this would block and wait. In the current
        architecture, it records the request and the operator decides via
        Claude Code prompt.
        """
        timeout = timeout_hours or self._timeout_hours
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "risk_level": risk_level,
            "context": context or {},
            "timeout_hours": timeout,
            "decision": "pending",
        }
        self._write_pending(entry)
        return SlotDecision.PENDING

    def approve(self, action: str) -> None:
        """Operator approves a pending action."""
        self._update_pending(action, "approved")

    def deny(self, action: str, reason: str = "") -> None:
        """Operator denies a pending action."""
        self._update_pending(action, "denied", reason)

    def list_pending(self) -> list[dict]:
        """List all pending human slot requests."""
        if not self._queue_path.exists():
            return []
        pending = []
        with open(self._queue_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    if entry.get("decision") == "pending":
                        pending.append(entry)
        return pending

    def _write_pending(self, entry: dict) -> None:
        with open(self._queue_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def _update_pending(self, action: str, decision: str, reason: str = "") -> None:
        """Update pending entry decision."""
        if not self._queue_path.exists():
            return
        entries = []
        with open(self._queue_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))
        with open(self._queue_path, "w", encoding="utf-8") as f:
            for entry in entries:
                if entry["action"] == action and entry.get("decision") == "pending":
                    entry["decision"] = decision
                    entry["decided_at"] = datetime.now(timezone.utc).isoformat()
                    if reason:
                        entry["reason"] = reason
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
