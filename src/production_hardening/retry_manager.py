"""W172 — Retry Manager: exponential backoff with jitter for transient failures."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Type

from src.remote_control.models import _new_id, _now_iso


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

@dataclass
class RetryConfig:
    max_attempts: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 30.0
    backoff_factor: float = 2.0
    jitter: bool = True                              # add random jitter
    retryable_exceptions: tuple = (Exception,)      # which exceptions to retry
    dry_run: bool = True                             # if True: compute but don't sleep

    def delay_for(self, attempt: int) -> float:
        """Compute delay (seconds) for attempt N (0-indexed)."""
        delay = self.base_delay_seconds * (self.backoff_factor ** attempt)
        delay = min(delay, self.max_delay_seconds)
        if self.jitter:
            delay *= (0.5 + random.random() * 0.5)  # 50-100% of computed delay
        return delay

    def to_dict(self) -> dict:
        return {
            "max_attempts": self.max_attempts,
            "base_delay_seconds": self.base_delay_seconds,
            "max_delay_seconds": self.max_delay_seconds,
            "backoff_factor": self.backoff_factor,
            "jitter": self.jitter,
            "dry_run": self.dry_run,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "RetryConfig":
        return cls(
            max_attempts=d.get("max_attempts", 3),
            base_delay_seconds=d.get("base_delay_seconds", 1.0),
            max_delay_seconds=d.get("max_delay_seconds", 30.0),
            backoff_factor=d.get("backoff_factor", 2.0),
            jitter=d.get("jitter", True),
            dry_run=d.get("dry_run", True),
        )

    @classmethod
    def fast(cls) -> "RetryConfig":
        return cls(max_attempts=3, base_delay_seconds=0.1, max_delay_seconds=1.0, jitter=False)

    @classmethod
    def aggressive(cls) -> "RetryConfig":
        return cls(max_attempts=5, base_delay_seconds=2.0, max_delay_seconds=60.0)


# ---------------------------------------------------------------------------
# Attempt record
# ---------------------------------------------------------------------------

@dataclass
class AttemptRecord:
    attempt_n: int = 0
    ok: bool = False
    output: Any = None
    error: str = ""
    delay_before_ms: float = 0.0
    attempted_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "attempt_n": self.attempt_n,
            "ok": self.ok,
            "error": self.error,
            "delay_before_ms": round(self.delay_before_ms, 2),
            "attempted_at": self.attempted_at,
        }


# ---------------------------------------------------------------------------
# Retry result
# ---------------------------------------------------------------------------

@dataclass
class RetryResult:
    result_id: str = field(default_factory=lambda: _new_id("rr"))
    ok: bool = False
    output: Any = None
    attempts: list[AttemptRecord] = field(default_factory=list)
    total_attempts: int = 0
    exhausted: bool = False
    last_error: str = ""
    completed_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "result_id": self.result_id,
            "ok": self.ok,
            "total_attempts": self.total_attempts,
            "exhausted": self.exhausted,
            "last_error": self.last_error,
            "attempts": [a.to_dict() for a in self.attempts],
            "completed_at": self.completed_at,
        }


# ---------------------------------------------------------------------------
# Retry manager
# ---------------------------------------------------------------------------

class RetryManager:
    """Executes a callable with retry logic (exponential backoff, dry-run)."""

    def __init__(self, config: Optional[RetryConfig] = None) -> None:
        self.config = config or RetryConfig()
        self._results: list[RetryResult] = []

    def execute(self, fn: Callable, *args: Any, **kwargs: Any) -> RetryResult:
        import time
        result = RetryResult()
        last_exc: Optional[Exception] = None

        for attempt_n in range(self.config.max_attempts):
            delay_s = 0.0
            if attempt_n > 0:
                delay_s = self.config.delay_for(attempt_n - 1)
                if not self.config.dry_run:
                    time.sleep(delay_s)

            record = AttemptRecord(attempt_n=attempt_n, delay_before_ms=delay_s * 1000)
            try:
                output = fn(*args, **kwargs)
                record.ok = True
                record.output = output
                result.attempts.append(record)
                result.ok = True
                result.output = output
                result.total_attempts = attempt_n + 1
                self._results.append(result)
                return result
            except Exception as exc:
                if not isinstance(exc, self.config.retryable_exceptions):
                    record.error = str(exc)
                    result.attempts.append(record)
                    result.last_error = str(exc)
                    result.total_attempts = attempt_n + 1
                    result.exhausted = True
                    self._results.append(result)
                    return result
                record.error = str(exc)
                last_exc = exc
                result.attempts.append(record)

        result.exhausted = True
        result.total_attempts = self.config.max_attempts
        result.last_error = str(last_exc) if last_exc else "unknown"
        self._results.append(result)
        return result

    def stats(self) -> dict:
        total = len(self._results)
        ok = sum(1 for r in self._results if r.ok)
        exhausted = sum(1 for r in self._results if r.exhausted)
        avg_attempts = (
            sum(r.total_attempts for r in self._results) / total if total else 0
        )
        return {
            "total_executions": total,
            "ok": ok,
            "exhausted": exhausted,
            "avg_attempts": round(avg_attempts, 2),
        }
