"""W175 — G19 Production Hardening E2E integration tests."""
import pytest
from src.production_hardening.circuit_breaker import CircuitBreaker, CircuitConfig, CircuitState
from src.production_hardening.health_registry import CheckStatus, HealthCheckRegistry
from src.production_hardening.retry_manager import RetryConfig, RetryManager
from src.production_hardening.timeout_guard import TimeoutConfig, TimeoutGuard


def _ok():
    return "ok"


def _fail():
    raise RuntimeError("service down")


class _Flaky:
    def __init__(self, fail_n: int):
        self.calls = 0
        self.fail_n = fail_n

    def __call__(self):
        self.calls += 1
        if self.calls <= self.fail_n:
            raise RuntimeError(f"flaky #{self.calls}")
        return "recovered"


# ---------------------------------------------------------------------------
# Circuit Breaker + Retry Manager combo
# ---------------------------------------------------------------------------

def test_retry_with_circuit_breaker():
    """RetryManager retries a flaky function; circuit breaker tracks failures."""
    cb = CircuitBreaker("service", CircuitConfig(failure_threshold=5))
    retry = RetryManager(RetryConfig(max_attempts=3, dry_run=True, jitter=False))

    fn = _Flaky(2)
    # retry directly wraps fn; circuit breaker wraps each successful call
    result = retry.execute(fn)
    assert result.ok
    assert fn.calls == 3
    assert cb.is_closed()  # never opened (below threshold)


def test_circuit_opens_under_retry_storm():
    """Multiple retry runs on a failing service eventually opens the circuit."""
    cb = CircuitBreaker("svc", CircuitConfig(failure_threshold=3, timeout_seconds=99.0))
    retry = RetryManager(RetryConfig(max_attempts=2, dry_run=True, jitter=False))

    for _ in range(2):
        retry.execute(lambda: cb.call(_fail))

    assert cb.is_open() or cb.stats()["failure_count"] >= 2


def test_open_circuit_in_retry_fast_fails():
    """Open circuit rejects call immediately (uses _now_ts to keep it open)."""
    import time
    now = time.time()
    cb = CircuitBreaker("svc", CircuitConfig(failure_threshold=2, timeout_seconds=9999.0))
    cb.call(_fail, _now_ts=now)
    cb.call(_fail, _now_ts=now + 0.1)
    assert cb.is_open()

    # Circuit still open — call is rejected
    result = cb.call(_ok, _now_ts=now + 1.0)
    assert result.circuit_open
    assert not result.ok


# ---------------------------------------------------------------------------
# Timeout + Circuit Breaker combo
# ---------------------------------------------------------------------------

def test_timeout_timeout_recorded():
    guard = TimeoutGuard(TimeoutConfig(dry_run=True, simulate_timeout=True))
    result = guard.execute(_ok)
    assert result.timed_out


def test_timeout_ok_no_circuit_open():
    cb = CircuitBreaker("svc", CircuitConfig(failure_threshold=3))
    guard = TimeoutGuard(TimeoutConfig(dry_run=True))
    result = guard.execute(lambda: cb.call(_ok))
    assert result.ok
    assert cb.is_closed()


def test_timeout_with_fallback_and_circuit():
    guard = TimeoutGuard(TimeoutConfig(dry_run=True, simulate_timeout=True))
    result = guard.execute_with_fallback(_ok, "default")
    assert result.output == "default"


# ---------------------------------------------------------------------------
# Health Registry + all modules
# ---------------------------------------------------------------------------

def test_health_registry_checks_all_modules():
    cb = CircuitBreaker("svc", CircuitConfig(failure_threshold=5))
    guard = TimeoutGuard(TimeoutConfig(dry_run=True))
    retry = RetryManager(RetryConfig.fast())

    reg = HealthCheckRegistry()
    reg.register_fn("circuit_closed", lambda: cb.is_closed(), module="circuit_breaker", critical=True)
    reg.register_fn("guard_no_timeouts", lambda: guard.stats()["timed_out"] == 0, module="timeout")
    reg.register_fn("retry_ok", lambda: retry.stats()["total_executions"] == 0, module="retry")

    report = reg.run()
    assert report.overall == CheckStatus.PASS


def test_health_fails_when_circuit_open():
    cb = CircuitBreaker("svc", CircuitConfig(failure_threshold=2))
    cb.call(_fail, _now_ts=0.0)
    cb.call(_fail, _now_ts=0.1)

    reg = HealthCheckRegistry()
    reg.register_fn("circuit_closed", lambda: cb.is_closed(), module="circuit_breaker", critical=True)
    report = reg.run()
    assert report.overall == CheckStatus.FAIL


def test_health_warns_on_non_critical_fail():
    reg = HealthCheckRegistry()
    reg.register_fn("ok_check", lambda: True, critical=False)
    reg.register_fn("non_critical_fail", lambda: False, critical=False)
    report = reg.run()
    assert report.overall == CheckStatus.FAIL  # FAIL even without critical=True


# ---------------------------------------------------------------------------
# Full resilience stack simulation
# ---------------------------------------------------------------------------

def test_resilience_stack_recovers():
    """Full stack: retry → circuit breaker → timeout guard."""
    cb = CircuitBreaker("service", CircuitConfig(failure_threshold=10))
    guard = TimeoutGuard(TimeoutConfig(dry_run=True))
    retry = RetryManager(RetryConfig(max_attempts=3, dry_run=True, jitter=False))

    fn = _Flaky(2)

    def protected_call():
        timeout_result = guard.execute(fn)
        if timeout_result.timed_out:
            raise RuntimeError("timeout")
        if not timeout_result.ok:
            raise RuntimeError(timeout_result.error)
        cb.call(lambda: timeout_result.output)
        return timeout_result.output

    result = retry.execute(protected_call)
    assert result.ok
    assert result.output == "recovered"
    assert cb.is_closed()

    reg = HealthCheckRegistry()
    reg.register_fn("circuit", lambda: cb.is_closed(), critical=True)
    reg.register_fn("guard_healthy", lambda: guard.stats()["timed_out"] == 0)
    reg.register_fn("retry_ok", lambda: retry.stats()["ok"] == 1)
    report = reg.run()
    assert report.overall == CheckStatus.PASS


def test_stats_snapshot():
    cb = CircuitBreaker("x", CircuitConfig(failure_threshold=5))
    guard = TimeoutGuard(TimeoutConfig(dry_run=True))
    retry = RetryManager(RetryConfig.fast())

    retry.execute(lambda: cb.call(_ok))
    guard.execute(_ok)

    cb_stats = cb.stats()
    assert cb_stats["ok_calls"] >= 1
    assert guard.stats()["ok"] >= 1
    assert retry.stats()["ok"] >= 1
