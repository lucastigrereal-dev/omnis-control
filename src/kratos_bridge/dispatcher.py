"""W161 — KRATOS Bridge Dispatcher: queues and dispatches cockpit payloads (dry-run)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

from .models import KratosPayload, PayloadPriority, PayloadStatus, PayloadType, _new_id, _now_iso

# Payload handler signature: (payload) -> dict with ok/output
HandlerFn = Callable[[KratosPayload], dict]

# Priority order (lower = higher priority)
_PRIORITY_ORDER = {
    PayloadPriority.CRITICAL: 0,
    PayloadPriority.HIGH: 1,
    PayloadPriority.NORMAL: 2,
    PayloadPriority.LOW: 3,
}


@dataclass
class DispatchResult:
    result_id: str = field(default_factory=lambda: _new_id("kdr"))
    payload_id: str = ""
    ok: bool = False
    status: str = PayloadStatus.QUEUED.value
    output: dict = field(default_factory=dict)
    error: str = ""
    dry_run: bool = True
    dispatched_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "result_id": self.result_id,
            "payload_id": self.payload_id,
            "ok": self.ok,
            "status": self.status,
            "output": self.output,
            "error": self.error,
            "dry_run": self.dry_run,
            "dispatched_at": self.dispatched_at,
        }


class KratosDispatcher:
    """Queues KratosPayloads and dispatches them to registered view handlers."""

    def __init__(self, dry_run: bool = True) -> None:
        self.dry_run = dry_run
        self._queue: list[KratosPayload] = []
        self._handlers: dict[str, HandlerFn] = {}
        self._history: list[DispatchResult] = []

    # ------------------------------------------------------------------
    def register(self, payload_type: PayloadType, handler: HandlerFn) -> None:
        self._handlers[payload_type.value] = handler

    def enqueue(self, payload: KratosPayload) -> KratosPayload:
        payload.dry_run = self.dry_run
        payload.status = PayloadStatus.QUEUED
        self._queue.append(payload)
        return payload

    # ------------------------------------------------------------------
    def flush(self) -> list[DispatchResult]:
        """Dispatch all queued payloads, highest priority first."""
        ordered = sorted(self._queue, key=lambda p: _PRIORITY_ORDER.get(p.priority, 99))
        self._queue.clear()
        results = []
        for payload in ordered:
            result = self._dispatch_one(payload)
            results.append(result)
        return results

    def dispatch_one(self, payload: KratosPayload) -> DispatchResult:
        """Dispatch a single payload immediately (bypasses queue)."""
        return self._dispatch_one(payload)

    # ------------------------------------------------------------------
    def _dispatch_one(self, payload: KratosPayload) -> DispatchResult:
        result = DispatchResult(payload_id=payload.payload_id, dry_run=self.dry_run)
        handler = self._handlers.get(payload.payload_type.value)

        if self.dry_run:
            payload.status = PayloadStatus.SENT
            payload.sent_at = _now_iso()
            result.ok = True
            result.status = PayloadStatus.SENT.value
            result.output = {"dry_run": True, "payload_type": payload.payload_type.value, "title": payload.title}
            self._history.append(result)
            return result

        if not handler:
            payload.status = PayloadStatus.DROPPED
            result.status = PayloadStatus.DROPPED.value
            result.error = f"no_handler_for:{payload.payload_type.value}"
            self._history.append(result)
            return result

        try:
            out = handler(payload)
            payload.status = PayloadStatus.DELIVERED
            payload.sent_at = _now_iso()
            result.ok = out.get("ok", True)
            result.status = PayloadStatus.DELIVERED.value
            result.output = out
        except Exception as exc:
            payload.status = PayloadStatus.FAILED
            result.status = PayloadStatus.FAILED.value
            result.error = str(exc)

        self._history.append(result)
        return result

    # ------------------------------------------------------------------
    def queue_size(self) -> int:
        return len(self._queue)

    def history(self) -> list[DispatchResult]:
        return list(self._history)

    def stats(self) -> dict:
        total = len(self._history)
        ok = sum(1 for r in self._history if r.ok)
        return {"total_dispatched": total, "ok": ok, "failed": total - ok, "queued": len(self._queue)}
