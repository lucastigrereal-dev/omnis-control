"""W171 — Circuit Breaker: protects against cascading failures with CLOSED/OPEN/HALF_OPEN states."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

from src.remote_control.models import _new_id, _now_iso


class CircuitState(str, Enum):
    CLOSED = "CLOSED"        # normal operation
    OPEN = "OPEN"            # failing, rejecting calls
    HALF_OPEN = "HALF_OPEN"  # testing recovery


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

@dataclass
class CircuitConfig:
    failure_threshold: int = 5          # failures before opening
    success_threshold: int = 2          # successes in HALF_OPEN to close
    timeout_seconds: float = 30.0       # time in OPEN before trying HALF_OPEN
    enabled: bool = True

    def to_dict(self) -> dict:
        return {
            "failure_threshold": self.failure_threshold,
            "success_threshold": self.success_threshold,
            "timeout_seconds": self.timeout_seconds,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CircuitConfig":
        return cls(
            failure_threshold=d.get("failure_threshold", 5),
            success_threshold=d.get("success_threshold", 2),
            timeout_seconds=d.get("timeout_seconds", 30.0),
            enabled=d.get("enabled", True),
        )

    @classmethod
    def strict(cls) -> "CircuitConfig":
        return cls(failure_threshold=2, success_threshold=1, timeout_seconds=10.0)

    @classmethod
    def lenient(cls) -> "CircuitConfig":
        return cls(failure_threshold=10, success_threshold=3, timeout_seconds=60.0)


# ---------------------------------------------------------------------------
# Call result
# ---------------------------------------------------------------------------

@dataclass
class CallResult:
    call_id: str = field(default_factory=lambda: _new_id("call"))
    ok: bool = False
    output: Any = None
    error: str = ""
    state_at_call: str = CircuitState.CLOSED.value
    circuit_open: bool = False
    called_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "call_id": self.call_id,
            "ok": self.ok,
            "error": self.error,
            "state_at_call": self.state_at_call,
            "circuit_open": self.circuit_open,
            "called_at": self.called_at,
        }


# ---------------------------------------------------------------------------
# Circuit Breaker
# ---------------------------------------------------------------------------

class CircuitBreaker:
    """Protects a callable with CLOSED → OPEN → HALF_OPEN state machine."""

    def __init__(self, name: str, config: Optional[CircuitConfig] = None) -> None:
        self.name = name
        self.config = config or CircuitConfig()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._opened_at: Optional[float] = None
        self._history: list[CallResult] = []

    # ------------------------------------------------------------------
    @property
    def state(self) -> CircuitState:
        return self._state

    def is_open(self) -> bool:
        return self._state == CircuitState.OPEN

    def is_closed(self) -> bool:
        return self._state == CircuitState.CLOSED

    # ------------------------------------------------------------------
    def call(self, fn: Callable, *args: Any, _now_ts: Optional[float] = None, **kwargs: Any) -> CallResult:
        import time
        now = _now_ts if _now_ts is not None else time.time()
        result = CallResult(state_at_call=self._state.value)

        if not self.config.enabled:
            result.ok = True
            result.output = fn(*args, **kwargs)
            self._history.append(result)
            return result

        # OPEN: check timeout
        if self._state == CircuitState.OPEN:
            if self._opened_at is not None and (now - self._opened_at) >= self.config.timeout_seconds:
                self._transition(CircuitState.HALF_OPEN)
            else:
                result.circuit_open = True
                result.error = f"circuit_open:{self.name}"
                self._history.append(result)
                return result

        # CLOSED or HALF_OPEN: execute
        try:
            output = fn(*args, **kwargs)
            result.ok = True
            result.output = output
            self._on_success()
        except Exception as exc:
            result.error = str(exc)
            self._on_failure(now)

        result.state_at_call = self._state.value
        self._history.append(result)
        return result

    # ------------------------------------------------------------------
    def _on_success(self) -> None:
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.config.success_threshold:
                self._transition(CircuitState.CLOSED)
        elif self._state == CircuitState.CLOSED:
            self._failure_count = 0

    def _on_failure(self, now: float) -> None:
        self._failure_count += 1
        if self._state == CircuitState.HALF_OPEN:
            self._transition(CircuitState.OPEN, now)
        elif self._state == CircuitState.CLOSED and self._failure_count >= self.config.failure_threshold:
            self._transition(CircuitState.OPEN, now)

    def _transition(self, new_state: CircuitState, now: Optional[float] = None) -> None:
        self._state = new_state
        if new_state == CircuitState.OPEN:
            self._opened_at = now
        elif new_state == CircuitState.CLOSED:
            self._failure_count = 0
            self._success_count = 0
            self._opened_at = None
        elif new_state == CircuitState.HALF_OPEN:
            self._success_count = 0

    # ------------------------------------------------------------------
    def reset(self) -> None:
        self._transition(CircuitState.CLOSED)
        self._history.clear()

    def history(self) -> list[CallResult]:
        return list(self._history)

    def stats(self) -> dict:
        total = len(self._history)
        ok = sum(1 for r in self._history if r.ok)
        return {
            "name": self.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "total_calls": total,
            "ok_calls": ok,
            "rejected_calls": sum(1 for r in self._history if r.circuit_open),
        }
