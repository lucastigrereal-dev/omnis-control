"""W173 — Tests for TimeoutGuard."""
import pytest
from src.production_hardening.timeout_guard import TimeoutConfig, TimeoutGuard, TimeoutResult


def _ok():
    return "done"


def _fail():
    raise ValueError("oops")


def _guard(simulate_timeout: bool = False, timeout: float = 1.0) -> TimeoutGuard:
    return TimeoutGuard(TimeoutConfig(timeout_seconds=timeout, dry_run=True, simulate_timeout=simulate_timeout))


# ---------------------------------------------------------------------------
# TimeoutConfig
# ---------------------------------------------------------------------------

def test_config_defaults():
    cfg = TimeoutConfig()
    assert cfg.timeout_seconds == 10.0
    assert cfg.dry_run is True
    assert cfg.simulate_timeout is False


def test_config_round_trip():
    cfg = TimeoutConfig(timeout_seconds=5.0, simulate_timeout=True)
    cfg2 = TimeoutConfig.from_dict(cfg.to_dict())
    assert cfg2.timeout_seconds == 5.0
    assert cfg2.simulate_timeout is True


# ---------------------------------------------------------------------------
# TimeoutResult
# ---------------------------------------------------------------------------

def test_result_to_dict():
    r = TimeoutResult(ok=True, elapsed_ms=10.5)
    d = r.to_dict()
    assert d["ok"] is True
    assert d["elapsed_ms"] == 10.5
    assert "result_id" in d


# ---------------------------------------------------------------------------
# Dry-run execution
# ---------------------------------------------------------------------------

def test_dry_run_success():
    guard = _guard()
    result = guard.execute(_ok)
    assert result.ok
    assert result.output == "done"
    assert not result.timed_out


def test_dry_run_elapsed_recorded():
    guard = _guard()
    result = guard.execute(_ok)
    assert result.elapsed_ms >= 0


def test_dry_run_function_error():
    guard = _guard()
    result = guard.execute(_fail)
    assert not result.ok
    assert "oops" in result.error
    assert not result.timed_out


def test_dry_run_with_args():
    guard = _guard()
    result = guard.execute(lambda x, y: x + y, 3, 4)
    assert result.ok
    assert result.output == 7


# ---------------------------------------------------------------------------
# Simulated timeout
# ---------------------------------------------------------------------------

def test_simulated_timeout():
    guard = _guard(simulate_timeout=True)
    result = guard.execute(_ok)
    assert result.timed_out
    assert not result.ok
    assert "timeout_simulated" in result.error


def test_simulated_timeout_elapsed_equals_timeout():
    guard = _guard(simulate_timeout=True, timeout=5.0)
    result = guard.execute(_ok)
    assert result.elapsed_ms == pytest.approx(5000.0)
    assert result.timeout_ms == 5000.0


# ---------------------------------------------------------------------------
# Fallback
# ---------------------------------------------------------------------------

def test_fallback_on_success_not_used():
    guard = _guard()
    result = guard.execute_with_fallback(_ok, "fallback")
    assert result.output == "done"


def test_fallback_on_timeout():
    guard = _guard(simulate_timeout=True)
    result = guard.execute_with_fallback(_ok, "fallback_value")
    assert result.output == "fallback_value"
    assert result.timed_out


def test_fallback_on_error():
    guard = _guard()
    result = guard.execute_with_fallback(_fail, "default")
    assert result.output == "default"
    assert not result.ok


# ---------------------------------------------------------------------------
# History and stats
# ---------------------------------------------------------------------------

def test_history_recorded():
    guard = _guard()
    guard.execute(_ok)
    guard.execute(_fail)
    assert len(guard.history()) == 2


def test_stats_empty():
    guard = _guard()
    s = guard.stats()
    assert s["total"] == 0


def test_stats_after_executions():
    guard = TimeoutGuard(TimeoutConfig(dry_run=True, simulate_timeout=False))
    guard.execute(_ok)
    guard.execute(_fail)
    s = guard.stats()
    assert s["total"] == 2
    assert s["ok"] == 1
    assert s["failed"] == 1
    assert s["timed_out"] == 0


def test_stats_timed_out():
    guard = _guard(simulate_timeout=True)
    guard.execute(_ok)
    s = guard.stats()
    assert s["timed_out"] == 1
    assert s["ok"] == 0


# ---------------------------------------------------------------------------
# Real threading (non-dry-run)
# ---------------------------------------------------------------------------

def test_real_mode_success():
    guard = TimeoutGuard(TimeoutConfig(timeout_seconds=1.0, dry_run=False))
    result = guard.execute(lambda: "real_ok")
    assert result.ok
    assert result.output == "real_ok"


def test_real_mode_timeout():
    import time
    guard = TimeoutGuard(TimeoutConfig(timeout_seconds=0.05, dry_run=False))
    result = guard.execute(lambda: time.sleep(1.0))
    assert result.timed_out


def test_real_mode_exception():
    guard = TimeoutGuard(TimeoutConfig(timeout_seconds=1.0, dry_run=False))
    result = guard.execute(lambda: (_ for _ in ()).throw(RuntimeError("real error")))
    assert not result.ok
    assert "real error" in result.error
