"""W172 — Tests for RetryManager."""
import pytest
from src.production_hardening.retry_manager import RetryConfig, RetryManager, RetryResult


def _ok():
    return "success"


class _FailThenOk:
    def __init__(self, fail_count: int):
        self.calls = 0
        self.fail_count = fail_count

    def __call__(self):
        self.calls += 1
        if self.calls <= self.fail_count:
            raise RuntimeError(f"fail #{self.calls}")
        return "ok"


# ---------------------------------------------------------------------------
# RetryConfig
# ---------------------------------------------------------------------------

def test_config_defaults():
    cfg = RetryConfig()
    assert cfg.max_attempts == 3
    assert cfg.dry_run is True


def test_config_fast():
    cfg = RetryConfig.fast()
    assert cfg.max_attempts == 3
    assert cfg.jitter is False


def test_config_aggressive():
    cfg = RetryConfig.aggressive()
    assert cfg.max_attempts == 5


def test_config_round_trip():
    cfg = RetryConfig(max_attempts=4, base_delay_seconds=0.5)
    cfg2 = RetryConfig.from_dict(cfg.to_dict())
    assert cfg2.max_attempts == 4
    assert cfg2.base_delay_seconds == 0.5


def test_delay_for_increases():
    cfg = RetryConfig(base_delay_seconds=1.0, backoff_factor=2.0, jitter=False)
    d0 = cfg.delay_for(0)
    d1 = cfg.delay_for(1)
    d2 = cfg.delay_for(2)
    assert d0 < d1 < d2


def test_delay_caps_at_max():
    cfg = RetryConfig(base_delay_seconds=1.0, backoff_factor=10.0, max_delay_seconds=5.0, jitter=False)
    assert cfg.delay_for(5) <= 5.0


def test_jitter_varies_delay():
    cfg = RetryConfig(base_delay_seconds=1.0, backoff_factor=1.0, jitter=True)
    delays = [cfg.delay_for(0) for _ in range(20)]
    assert len(set(round(d, 3) for d in delays)) > 1  # should vary


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_success_on_first_try():
    mgr = RetryManager(RetryConfig.fast())
    result = mgr.execute(_ok)
    assert result.ok
    assert result.total_attempts == 1
    assert not result.exhausted


def test_result_output():
    mgr = RetryManager(RetryConfig.fast())
    result = mgr.execute(_ok)
    assert result.output == "success"


# ---------------------------------------------------------------------------
# Retry after failures
# ---------------------------------------------------------------------------

def test_retry_succeeds_after_failures():
    mgr = RetryManager(RetryConfig.fast())
    fn = _FailThenOk(2)
    result = mgr.execute(fn)
    assert result.ok
    assert result.total_attempts == 3


def test_retry_records_attempts():
    mgr = RetryManager(RetryConfig.fast())
    fn = _FailThenOk(1)
    result = mgr.execute(fn)
    assert len(result.attempts) == 2
    assert not result.attempts[0].ok
    assert result.attempts[1].ok


# ---------------------------------------------------------------------------
# Exhaustion
# ---------------------------------------------------------------------------

def test_exhausted_after_max_attempts():
    mgr = RetryManager(RetryConfig(max_attempts=3, dry_run=True, jitter=False))
    result = mgr.execute(lambda: (_ for _ in ()).throw(RuntimeError("always fails")))
    assert not result.ok
    assert result.exhausted
    assert result.total_attempts == 3


def test_exhausted_has_last_error():
    def always_fail():
        raise ValueError("permanent error")

    mgr = RetryManager(RetryConfig(max_attempts=2, dry_run=True, jitter=False))
    result = mgr.execute(always_fail)
    assert "permanent error" in result.last_error


# ---------------------------------------------------------------------------
# to_dict
# ---------------------------------------------------------------------------

def test_result_to_dict():
    mgr = RetryManager(RetryConfig.fast())
    result = mgr.execute(_ok)
    d = result.to_dict()
    assert d["ok"] is True
    assert "result_id" in d
    assert "attempts" in d


def test_attempt_record_to_dict():
    mgr = RetryManager(RetryConfig.fast())
    fn = _FailThenOk(1)
    result = mgr.execute(fn)
    a = result.attempts[0].to_dict()
    assert "attempt_n" in a
    assert "error" in a


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def test_stats_empty():
    mgr = RetryManager(RetryConfig.fast())
    s = mgr.stats()
    assert s["total_executions"] == 0


def test_stats_after_executions():
    mgr = RetryManager(RetryConfig.fast())
    mgr.execute(_ok)
    mgr.execute(_ok)

    def fail():
        raise RuntimeError("x")

    mgr.execute(fail)
    s = mgr.stats()
    assert s["total_executions"] == 3
    assert s["ok"] == 2
    assert s["exhausted"] == 1


def test_stats_avg_attempts():
    mgr = RetryManager(RetryConfig(max_attempts=3, dry_run=True, jitter=False))
    mgr.execute(_ok)
    fn = _FailThenOk(2)
    mgr.execute(fn)
    s = mgr.stats()
    assert s["avg_attempts"] > 1.0


# ---------------------------------------------------------------------------
# Dry run doesn't sleep
# ---------------------------------------------------------------------------

def test_dry_run_completes_quickly():
    import time
    mgr = RetryManager(RetryConfig(max_attempts=3, base_delay_seconds=10.0, dry_run=True, jitter=False))
    fn = _FailThenOk(2)
    start = time.time()
    mgr.execute(fn)
    elapsed = time.time() - start
    assert elapsed < 1.0  # dry_run: no real sleep
