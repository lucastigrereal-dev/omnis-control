"""P29 OMNIS OS Layer — EventBus.

In-process pub/sub for module-to-module communication.
All OMNIS modules communicate exclusively through OmnisEvents on this bus.
"""
from collections import defaultdict
from typing import Callable, Optional

from src.omnis_os.models import OmnisEvent


Handler = Callable[[OmnisEvent], None]


class EventBus:
    """In-process pub/sub event bus."""

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self._subscribers: dict[str, list[Handler]] = defaultdict(list)
        self._history: list[OmnisEvent] = []
        self._history_limit: int = 1000

    # ── Subscribe / Unsubscribe ───────────────────────────────────

    def subscribe(self, event_type: str, handler: Handler) -> None:
        self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: Handler) -> None:
        subs = self._subscribers.get(event_type, [])
        if handler in subs:
            subs.remove(handler)

    def unsubscribe_all(self) -> None:
        self._subscribers.clear()

    # ── Emit ──────────────────────────────────────────────────────

    def emit(self, event: OmnisEvent) -> None:
        self._history.append(event)
        if len(self._history) > self._history_limit:
            self._history = self._history[-self._history_limit:]

        if self.dry_run:
            return

        for handler in self._subscribers.get(event.event_type, []):
            try:
                handler(event)
            except Exception:
                # Swallow handler errors — don't crash the bus
                pass

    def emit_new(self, event_type: str, source_module: str,
                 data: Optional[dict] = None) -> OmnisEvent:
        event = OmnisEvent.new(event_type, source_module, data=data)
        self.emit(event)
        return event

    # ── Query ─────────────────────────────────────────────────────

    def history(self, event_type: str = "", limit: int = 100) -> list[OmnisEvent]:
        events = self._history
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return events[-limit:]

    def subscriber_count(self, event_type: str) -> int:
        return len(self._subscribers.get(event_type, []))

    @property
    def total_subscribers(self) -> int:
        return sum(len(v) for v in self._subscribers.values())

    @property
    def event_types(self) -> list[str]:
        return list(self._subscribers.keys())

    @property
    def history_size(self) -> int:
        return len(self._history)
