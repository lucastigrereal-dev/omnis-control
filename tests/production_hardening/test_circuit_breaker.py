"""W171 — Tests for CircuitBreaker."""
import pytest
from src.production_hardening.circuit_breaker import (
    CircuitBreaker,
    CircuitConfig,
    CircuitState,
    CallResult,
)


def _ok():
    return "ok"


def _fail():
    raise RuntimeError("service down")


def _cb(failure_threshold=3, success_threshold=2, timeout=10.0) -> CircuitBreaker:
    cfg = CircuitConfig(failure_threshold=failure_threshold, success_threshold=success_threshold, timeout_seconds=timeout)
    return CircuitBreaker("test", cfg)


# ---------------------------------------------------------------------------
# CircuitConfig
# ---------------------------------------------------------------------------

def test_config_defaults():
    cfg = CircuitConfig()
    assert cfg.failure_threshold == 5
    assert cfg.enabled is True


def test_config_strict():
    cfg = CircuitConfig.strict()
    assert cfg.failure_threshold == 2


def test_config_lenient():
    cfg = CircuitConfig.lenient()
    assert cfg.failure_threshold == 10


def test_config_round_trip():
    cfg = CircuitConfig(failure_threshold=3, success_threshold=1)
    cfg2 = CircuitConfig.from_dict(cfg.to_dict())
    assert cfg2.failure_threshold == 3


# ---------------------------------------------------------------------------
# CLOSED state
# ---------------------------------------------------------------------------

def test_starts_closed():
    cb = _cb()
    assert cb.is_closed()
    assert cb.state == CircuitState.CLOSED


def test_successful_call_in_closed():
    cb = _cb()
    result = cb.call(_ok)
    assert result.ok
    assert not result.circuit_open


def test_failures_below_threshold_stay_closed():
    cb = _cb(failure_threshold=3)
    cb.call(_fail)
    cb.call(_fail)
    assert cb.is_closed()


def test_failures_at_threshold_opens():
    cb = _cb(failure_threshold=3)
    for _ in range(3):
        cb.call(_fail)
    assert cb.is_open()


# ---------------------------------------------------------------------------
# OPEN state
# ---------------------------------------------------------------------------

def test_open_rejects_calls():
    cb = _cb(failure_threshold=2)
    cb.call(_fail)
    cb.call(_fail)
    result = cb.call(_ok)
    assert not result.ok
    assert result.circuit_open
    assert "circuit_open" in result.error


def test_open_transitions_to_half_open_after_timeout():
    cb = _cb(failure_threshold=2, timeout=5.0)
    cb.call(_fail, _now_ts=0.0)
    cb.call(_fail, _now_ts=0.1)
    assert cb.is_open()
    # After timeout
    result = cb.call(_ok, _now_ts=10.0)
    assert cb.state == CircuitState.HALF_OPEN or result.ok


def test_open_before_timeout_still_rejects():
    cb = _cb(failure_threshold=2, timeout=30.0)
    cb.call(_fail, _now_ts=0.0)
    cb.call(_fail, _now_ts=0.1)
    result = cb.call(_ok, _now_ts=10.0)
    assert result.circuit_open


# ---------------------------------------------------------------------------
# HALF_OPEN state
# ---------------------------------------------------------------------------

def test_half_open_success_closes():
    cb = _cb(failure_threshold=2, success_threshold=2, timeout=5.0)
    cb.call(_fail, _now_ts=0.0)
    cb.call(_fail, _now_ts=0.1)
    # Trigger HALF_OPEN
    cb.call(_ok, _now_ts=10.0)
    cb.call(_ok, _now_ts=10.1)
    assert cb.is_closed()


def test_half_open_failure_reopens():
    cb = _cb(failure_threshold=2, success_threshold=2, timeout=5.0)
    cb.call(_fail, _now_ts=0.0)
    cb.call(_fail, _now_ts=0.1)
    # Move to HALF_OPEN
    cb.call(_ok, _now_ts=10.0)
    # Fail in HALF_OPEN → back to OPEN
    cb.call(_fail, _now_ts=10.1)
    assert cb.is_open()


# ---------------------------------------------------------------------------
# Success resets failure count
# ---------------------------------------------------------------------------

def test_success_resets_failure_count():
    cb = _cb(failure_threshold=3)
    cb.call(_fail)
    cb.call(_fail)
    cb.call(_ok)   # success resets
    cb.call(_fail)
    cb.call(_fail)
    # Only 2 failures after reset
    assert cb.is_closed()


# ---------------------------------------------------------------------------
# Disabled
# ---------------------------------------------------------------------------

def test_disabled_always_calls():
    cfg = CircuitConfig(enabled=False)
    cb = CircuitBreaker("x", cfg)
    # Disabled: state machine bypassed; exceptions propagate; state stays CLOSED
    with pytest.raises(RuntimeError):
        cb.call(_fail)
    assert not cb.is_open()


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------

def test_reset():
    cb = _cb(failure_threshold=2)
    cb.call(_fail)
    cb.call(_fail)
    assert cb.is_open()
    cb.reset()
    assert cb.is_closed()
    result = cb.call(_ok)
    assert result.ok


# ---------------------------------------------------------------------------
# History and stats
# ---------------------------------------------------------------------------

def test_history_recorded():
    cb = _cb()
    cb.call(_ok)
    cb.call(_fail)
    assert len(cb.history()) == 2


def test_stats():
    cb = _cb(failure_threshold=3)
    cb.call(_ok)
    cb.call(_fail)
    s = cb.stats()
    assert s["name"] == "test"
    assert s["total_calls"] == 2
    assert s["ok_calls"] == 1
    assert s["state"] == "CLOSED"


def test_stats_rejected_counted():
    cb = _cb(failure_threshold=2)
    cb.call(_fail, _now_ts=0.0)
    cb.call(_fail, _now_ts=0.1)
    cb.call(_ok, _now_ts=1.0)  # rejected
    s = cb.stats()
    assert s["rejected_calls"] == 1


# ---------------------------------------------------------------------------
# CallResult
# ---------------------------------------------------------------------------

def test_call_result_to_dict():
    r = CallResult(ok=True)
    d = r.to_dict()
    assert d["ok"] is True
    assert "call_id" in d
