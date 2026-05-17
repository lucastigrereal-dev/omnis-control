"""W173 — Timeout Guard: wraps callables with timeout enforcement (dry-run/mock)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from src.remote_control.models import _new_id, _now_iso


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

@dataclass
class TimeoutConfig:
    timeout_seconds: float = 10.0
    dry_run: bool = True            # in dry_run: simulate timeout without real threading
    simulate_timeout: bool = False  # force timeout for testing

    def to_dict(self) -> dict:
        return {
            "timeout_seconds": self.timeout_seconds,
            "dry_run": self.dry_run,
            "simulate_timeout": self.simulate_timeout,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "TimeoutConfig":
        return cls(
            timeout_seconds=d.get("timeout_seconds", 10.0),
            dry_run=d.get("dry_run", True),
            simulate_timeout=d.get("simulate_timeout", False),
        )


class TimeoutError(Exception):
    pass


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------

@dataclass
class TimeoutResult:
    result_id: str = field(default_factory=lambda: _new_id("tr"))
    ok: bool = False
    timed_out: bool = False
    output: Any = None
    error: str = ""
    elapsed_ms: float = 0.0
    timeout_ms: float = 0.0
    executed_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "result_id": self.result_id,
            "ok": self.ok,
            "timed_out": self.timed_out,
            "error": self.error,
            "elapsed_ms": round(self.elapsed_ms, 2),
            "timeout_ms": self.timeout_ms,
            "executed_at": self.executed_at,
        }


# ---------------------------------------------------------------------------
# Timeout guard
# ---------------------------------------------------------------------------

class TimeoutGuard:
    """Wraps callables with timeout enforcement.

    In dry_run mode: uses a simple simulation flag (no threads/signals).
    In real mode: uses threading.Thread with join timeout.
    """

    def __init__(self, config: Optional[TimeoutConfig] = None) -> None:
        self.config = config or TimeoutConfig()
        self._history: list[TimeoutResult] = []

    def execute(self, fn: Callable, *args: Any, **kwargs: Any) -> TimeoutResult:
        import time
        result = TimeoutResult(timeout_ms=self.config.timeout_seconds * 1000)

        # Dry-run: simulate timeout without real threading
        if self.config.dry_run:
            if self.config.simulate_timeout:
                result.timed_out = True
                result.error = f"timeout_simulated:{self.config.timeout_seconds}s"
                result.elapsed_ms = self.config.timeout_seconds * 1000
                self._history.append(result)
                return result
            # Normal dry_run: just execute
            start = time.perf_counter()
            try:
                output = fn(*args, **kwargs)
                result.ok = True
                result.output = output
            except Exception as exc:
                result.error = str(exc)
            finally:
                result.elapsed_ms = (time.perf_counter() - start) * 1000
            self._history.append(result)
            return result

        # Real mode: threading
        import threading
        output_holder: list = []
        error_holder: list = []

        def _target():
            try:
                output_holder.append(fn(*args, **kwargs))
            except Exception as exc:
                error_holder.append(str(exc))

        start = time.perf_counter()
        t = threading.Thread(target=_target, daemon=True)
        t.start()
        t.join(timeout=self.config.timeout_seconds)
        result.elapsed_ms = (time.perf_counter() - start) * 1000

        if t.is_alive():
            result.timed_out = True
            result.error = f"timed_out_after:{self.config.timeout_seconds}s"
        elif error_holder:
            result.error = error_holder[0]
        else:
            result.ok = True
            result.output = output_holder[0] if output_holder else None

        self._history.append(result)
        return result

    def execute_with_fallback(self, fn: Callable, fallback: Any, *args: Any, **kwargs: Any) -> TimeoutResult:
        result = self.execute(fn, *args, **kwargs)
        if result.timed_out or not result.ok:
            result.output = fallback
        return result

    def history(self) -> list[TimeoutResult]:
        return list(self._history)

    def stats(self) -> dict:
        total = len(self._history)
        ok = sum(1 for r in self._history if r.ok)
        timed = sum(1 for r in self._history if r.timed_out)
        return {
            "total": total,
            "ok": ok,
            "timed_out": timed,
            "failed": total - ok - timed,
        }
