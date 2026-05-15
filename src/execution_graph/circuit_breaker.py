"""Circuit breaker for execution graph steps."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class CircuitState(str, Enum):
    CLOSED = "closed"        # Normal — requests pass through
    OPEN = "open"            # Tripped — requests are blocked
    HALF_OPEN = "half_open"  # Recovery probe — limited requests allowed


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class CircuitBreaker:
    failure_threshold: int = 5
    cooldown_seconds: float = 30.0
    half_open_max_probes: int = 1
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: str = ""
    tripped_at: str = ""
    half_open_probe_count: int = 0

    def before_call(self) -> bool:
        """Check if a call is allowed. Returns True if call may proceed."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if self._cooldown_elapsed():
                self._transition_to_half_open()
                self.half_open_probe_count = 1  # this call counts as the probe
                return True
            return False

        # HALF_OPEN — allow limited probes
        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_probe_count < self.half_open_max_probes:
                self.half_open_probe_count += 1
                return True
            return False

        return False

    def on_success(self) -> None:
        """Report a successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self._transition_to_closed()
        # In CLOSED, reset failure count on success
        self.failure_count = 0

    def on_failure(self) -> None:
        """Report a failed call."""
        self.failure_count += 1
        self.last_failure_time = _utc_now()

        if self.state == CircuitState.HALF_OPEN:
            self._transition_to_open()
        elif self.state == CircuitState.CLOSED and self.failure_count >= self.failure_threshold:
            self._transition_to_open()

    def is_open(self) -> bool:
        return self.state == CircuitState.OPEN

    def _cooldown_elapsed(self) -> bool:
        if not self.tripped_at:
            return True
        now = datetime.now(timezone.utc)
        tripped = datetime.fromisoformat(self.tripped_at)
        elapsed = (now - tripped).total_seconds()
        return elapsed >= self.cooldown_seconds

    def _transition_to_open(self) -> None:
        self.state = CircuitState.OPEN
        self.tripped_at = _utc_now()

    def _transition_to_half_open(self) -> None:
        self.state = CircuitState.HALF_OPEN
        self.half_open_probe_count = 0

    def _transition_to_closed(self) -> None:
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.half_open_probe_count = 0
        self.tripped_at = ""

    def reset(self) -> None:
        self._transition_to_closed()

    def to_dict(self) -> dict:
        return {
            "failure_threshold": self.failure_threshold,
            "cooldown_seconds": self.cooldown_seconds,
            "half_open_max_probes": self.half_open_max_probes,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time,
            "tripped_at": self.tripped_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CircuitBreaker":
        return cls(
            failure_threshold=d.get("failure_threshold", 5),
            cooldown_seconds=d.get("cooldown_seconds", 30.0),
            half_open_max_probes=d.get("half_open_max_probes", 1),
            state=CircuitState(d.get("state", "closed")),
            failure_count=d.get("failure_count", 0),
            last_failure_time=d.get("last_failure_time", ""),
            tripped_at=d.get("tripped_at", ""),
        )


@dataclass
class CircuitBreakerRegistry:
    """Registry of circuit breakers keyed by step_id or role_id."""
    breakers: dict[str, CircuitBreaker] = field(default_factory=dict)
    default_config: CircuitBreaker = field(default_factory=CircuitBreaker)

    def get(self, key: str) -> CircuitBreaker:
        if key not in self.breakers:
            self.breakers[key] = CircuitBreaker(
                failure_threshold=self.default_config.failure_threshold,
                cooldown_seconds=self.default_config.cooldown_seconds,
                half_open_max_probes=self.default_config.half_open_max_probes,
            )
        return self.breakers[key]

    def before_step(self, step_id: str) -> bool:
        return self.get(step_id).before_call()

    def on_step_success(self, step_id: str) -> None:
        self.get(step_id).on_success()

    def on_step_failure(self, step_id: str) -> None:
        self.get(step_id).on_failure()

    def reset_all(self) -> None:
        for breaker in self.breakers.values():
            breaker.reset()

    def to_dict(self) -> dict:
        return {
            "breakers": {k: v.to_dict() for k, v in self.breakers.items()},
            "default_config": self.default_config.to_dict(),
        }
