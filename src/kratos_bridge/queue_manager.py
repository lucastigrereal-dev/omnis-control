"""W165 — KRATOS Bridge Queue Manager: persistent payload queue with retry & replay."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .models import KratosPayload, PayloadPriority, PayloadStatus, _new_id, _now_iso

_PRIORITY_ORDER = {
    PayloadPriority.CRITICAL: 0,
    PayloadPriority.HIGH: 1,
    PayloadPriority.NORMAL: 2,
    PayloadPriority.LOW: 3,
}

_MAX_RETRIES = 3


# ---------------------------------------------------------------------------
# Queue entry
# ---------------------------------------------------------------------------

@dataclass
class QueueEntry:
    entry_id: str = field(default_factory=lambda: _new_id("qe"))
    payload: Optional[KratosPayload] = None
    attempts: int = 0
    max_retries: int = _MAX_RETRIES
    last_error: str = ""
    status: str = PayloadStatus.QUEUED.value
    enqueued_at: str = field(default_factory=_now_iso)
    next_attempt_at: str = field(default_factory=_now_iso)

    @property
    def exhausted(self) -> bool:
        return self.attempts >= self.max_retries

    @property
    def is_failed(self) -> bool:
        return self.status == PayloadStatus.FAILED.value

    @property
    def is_delivered(self) -> bool:
        return self.status == PayloadStatus.DELIVERED.value

    @property
    def is_pending(self) -> bool:
        return self.status in (PayloadStatus.QUEUED.value, "RETRY")

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "payload": self.payload.to_dict() if self.payload else None,
            "attempts": self.attempts,
            "max_retries": self.max_retries,
            "last_error": self.last_error,
            "status": self.status,
            "enqueued_at": self.enqueued_at,
            "next_attempt_at": self.next_attempt_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "QueueEntry":
        payload = KratosPayload.from_dict(data["payload"]) if data.get("payload") else None
        return cls(
            entry_id=data.get("entry_id", _new_id("qe")),
            payload=payload,
            attempts=data.get("attempts", 0),
            max_retries=data.get("max_retries", _MAX_RETRIES),
            last_error=data.get("last_error", ""),
            status=data.get("status", PayloadStatus.QUEUED.value),
            enqueued_at=data.get("enqueued_at", _now_iso()),
            next_attempt_at=data.get("next_attempt_at", _now_iso()),
        )


# ---------------------------------------------------------------------------
# Queue manager
# ---------------------------------------------------------------------------

class PayloadQueueManager:
    """Persistent FIFO/priority queue with retry logic for KratosPayloads."""

    def __init__(self, queue_path: Optional[Path] = None, max_retries: int = _MAX_RETRIES) -> None:
        self._entries: list[QueueEntry] = []
        self._queue_path = queue_path
        self._max_retries = max_retries
        if queue_path and queue_path.exists():
            self._load(queue_path)

    # ------------------------------------------------------------------
    def enqueue(self, payload: KratosPayload) -> QueueEntry:
        entry = QueueEntry(payload=payload, max_retries=self._max_retries)
        self._entries.append(entry)
        self._persist()
        return entry

    def enqueue_many(self, payloads: list[KratosPayload]) -> list[QueueEntry]:
        entries = []
        for p in payloads:
            e = QueueEntry(payload=p, max_retries=self._max_retries)
            self._entries.append(e)
            entries.append(e)
        self._persist()
        return entries

    # ------------------------------------------------------------------
    def peek(self, count: int = 1) -> list[QueueEntry]:
        """Return next N pending entries sorted by priority."""
        pending = [e for e in self._entries if e.is_pending]
        ordered = sorted(pending, key=lambda e: _PRIORITY_ORDER.get(
            e.payload.priority if e.payload else PayloadPriority.NORMAL, 99
        ))
        return ordered[:count]

    def pop(self) -> Optional[QueueEntry]:
        candidates = self.peek(1)
        return candidates[0] if candidates else None

    # ------------------------------------------------------------------
    def mark_delivered(self, entry_id: str) -> bool:
        entry = self._find(entry_id)
        if not entry:
            return False
        entry.status = PayloadStatus.DELIVERED.value
        self._persist()
        return True

    def mark_failed(self, entry_id: str, error: str = "") -> bool:
        entry = self._find(entry_id)
        if not entry:
            return False
        entry.attempts += 1
        entry.last_error = error
        if entry.exhausted:
            entry.status = PayloadStatus.FAILED.value
        else:
            entry.status = "RETRY"
        self._persist()
        return True

    def mark_dropped(self, entry_id: str, reason: str = "") -> bool:
        entry = self._find(entry_id)
        if not entry:
            return False
        entry.status = PayloadStatus.DROPPED.value
        entry.last_error = reason
        self._persist()
        return True

    # ------------------------------------------------------------------
    def pending(self) -> list[QueueEntry]:
        return [e for e in self._entries if e.is_pending]

    def failed(self) -> list[QueueEntry]:
        return [e for e in self._entries if e.is_failed]

    def delivered(self) -> list[QueueEntry]:
        return [e for e in self._entries if e.is_delivered]

    def all_entries(self) -> list[QueueEntry]:
        return list(self._entries)

    def size(self) -> int:
        return len([e for e in self._entries if e.is_pending])

    def clear_delivered(self) -> int:
        before = len(self._entries)
        self._entries = [e for e in self._entries if not e.is_delivered]
        self._persist()
        return before - len(self._entries)

    def clear_all(self) -> None:
        self._entries.clear()
        self._persist()

    # ------------------------------------------------------------------
    def stats(self) -> dict:
        total = len(self._entries)
        return {
            "total": total,
            "pending": len(self.pending()),
            "delivered": len(self.delivered()),
            "failed": len(self.failed()),
            "dropped": sum(1 for e in self._entries if e.status == PayloadStatus.DROPPED.value),
        }

    # ------------------------------------------------------------------
    def _find(self, entry_id: str) -> Optional[QueueEntry]:
        for e in self._entries:
            if e.entry_id == entry_id:
                return e
        return None

    def _persist(self) -> None:
        if not self._queue_path:
            return
        try:
            lines = [json.dumps(e.to_dict()) for e in self._entries]
            self._queue_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        except OSError:
            pass

    def _load(self, path: Path) -> None:
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line:
                    self._entries.append(QueueEntry.from_dict(json.loads(line)))
        except (OSError, json.JSONDecodeError):
            pass

    def reload(self) -> None:
        if self._queue_path and self._queue_path.exists():
            self._entries.clear()
            self._load(self._queue_path)
