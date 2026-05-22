"""ReplayBuffer -- pure in-memory event replay with filtering by type, source, and time window.

No persistent infra. No disk writes. Caps at configurable ring size (default 100).
"""

from collections import deque
from datetime import datetime, timezone


class ReplayBuffer:
    """Ring-buffer event store with replay and filter capabilities.

    Wraps a collections.deque with maxlen cap. Supports retrieval by:
    - Simple count (replay last N)
    - Event type filter
    - Source service filter
    - Time window (events within last N seconds)
    """

    def __init__(self, maxlen: int = 100):
        self._ring: deque = deque(maxlen=maxlen)

    # ------------------------------------------------------------------
    # Mutate
    # ------------------------------------------------------------------
    def append(self, event: dict) -> None:
        self._ring.append(event)

    def clear(self) -> None:
        self._ring.clear()

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------
    def replay(self, n: int = 10) -> list[dict]:
        """Replay the last N events from the ring buffer."""
        events = list(self._ring)
        return events[-n:]

    def replay_by_type(self, event_type: str, n: int = 10) -> list[dict]:
        """Replay the last N events matching a specific event_type."""
        events = [e for e in self._ring if e.get("event_type") == event_type]
        return events[-n:]

    def replay_by_source(self, source: str, n: int = 10) -> list[dict]:
        """Replay the last N events from a specific source service."""
        events = [e for e in self._ring if e.get("source", {}).get("service") == source]
        return events[-n:]

    def replay_by_timewindow(self, window_seconds: float) -> list[dict]:
        """Replay all events received within the last N seconds.

        Uses internal `_received_at` field if present, otherwise checks
        the envelope `timestamp` field.
        """
        now = datetime.now(timezone.utc)
        result: list[dict] = []
        for event in self._ring:
            ts_str = event.get("_received_at") or event.get("timestamp")
            if ts_str is None:
                continue
            try:
                ts_str_clean = ts_str.replace("Z", "+00:00")
                event_time = datetime.fromisoformat(ts_str_clean)
                delta = (now - event_time).total_seconds()
                if 0 <= delta <= window_seconds:
                    result.append(event)
            except (ValueError, TypeError):
                continue
        return result

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------
    @property
    def capacity(self) -> int:
        return self._ring.maxlen if self._ring.maxlen is not None else 0

    @property
    def size(self) -> int:
        return len(self._ring)

    def get_status(self) -> dict:
        return {
            "size": len(self._ring),
            "capacity": self._ring.maxlen,
            "is_empty": len(self._ring) == 0,
        }
