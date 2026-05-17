"""W158 — Tests for RateLimiter & ThrottleGuard."""
import pytest
from src.remote_control.rate_limiter import RateLimiter, RateLimitConfig, ThrottleResult


def _ts(offset: float = 0.0) -> float:
    return 1000.0 + offset


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def test_config_defaults():
    cfg = RateLimitConfig()
    assert cfg.max_requests == 10
    assert cfg.window_seconds == 60.0
    assert cfg.enabled is True


def test_config_strict():
    cfg = RateLimitConfig.strict()
    assert cfg.max_requests == 5
    assert cfg.burst_max == 2


def test_config_permissive():
    cfg = RateLimitConfig.permissive()
    assert cfg.max_requests == 100


def test_config_round_trip():
    cfg = RateLimitConfig(max_requests=7, window_seconds=30.0)
    cfg2 = RateLimitConfig.from_dict(cfg.to_dict())
    assert cfg2.max_requests == 7
    assert cfg2.window_seconds == 30.0


# ---------------------------------------------------------------------------
# ThrottleResult
# ---------------------------------------------------------------------------

def test_throttle_result_to_dict():
    r = ThrottleResult(user_id="u1", allowed=True, reason="ok")
    d = r.to_dict()
    assert d["allowed"] is True
    assert d["user_id"] == "u1"
    assert "result_id" in d


# ---------------------------------------------------------------------------
# Basic allow
# ---------------------------------------------------------------------------

def test_first_request_allowed():
    rl = RateLimiter(RateLimitConfig(max_requests=5, window_seconds=60.0, burst_max=10))
    result = rl.check("user1", _ts(0))
    assert result.allowed
    assert result.reason == "ok"
    assert result.requests_in_window == 1


def test_multiple_requests_within_limit():
    rl = RateLimiter(RateLimitConfig(max_requests=5, window_seconds=60.0, burst_max=10))
    for i in range(5):
        result = rl.check("user1", _ts(i * 2))
    assert result.allowed
    assert result.requests_in_window == 5


# ---------------------------------------------------------------------------
# Window limit
# ---------------------------------------------------------------------------

def test_exceeds_window_limit():
    rl = RateLimiter(RateLimitConfig(max_requests=3, window_seconds=60.0, burst_max=10))
    for i in range(3):
        rl.check("user1", _ts(i * 2))
    result = rl.check("user1", _ts(10))
    assert not result.allowed
    assert result.reason == "rate_limit_exceeded"


def test_window_resets_after_expiry():
    rl = RateLimiter(RateLimitConfig(max_requests=3, window_seconds=10.0, burst_max=10))
    for i in range(3):
        rl.check("user1", _ts(i))
    # Advance past window
    result = rl.check("user1", _ts(15))
    assert result.allowed


def test_window_resets_in_populated():
    rl = RateLimiter(RateLimitConfig(max_requests=2, window_seconds=60.0, burst_max=10))
    rl.check("user1", _ts(0))
    rl.check("user1", _ts(1))
    result = rl.check("user1", _ts(2))
    assert not result.allowed
    assert result.window_resets_in > 0


# ---------------------------------------------------------------------------
# Burst detection
# ---------------------------------------------------------------------------

def test_burst_detected_rapid_requests():
    rl = RateLimiter(RateLimitConfig(max_requests=20, window_seconds=60.0, burst_max=3, burst_cooldown_seconds=5.0))
    # 3 rapid-fire requests (sub-second gap)
    rl.check("u", _ts(0))
    rl.check("u", _ts(0.1))
    rl.check("u", _ts(0.2))
    result = rl.check("u", _ts(0.3))
    assert not result.allowed
    assert result.reason == "burst_detected"


def test_burst_cooldown_blocks():
    rl = RateLimiter(RateLimitConfig(max_requests=20, window_seconds=60.0, burst_max=3, burst_cooldown_seconds=10.0))
    rl.check("u", _ts(0))
    rl.check("u", _ts(0.1))
    rl.check("u", _ts(0.2))
    rl.check("u", _ts(0.3))  # triggers burst block
    # Immediately after — still in cooldown
    result = rl.check("u", _ts(1.0))
    assert not result.allowed
    assert result.reason == "burst_cooldown"


def test_burst_cooldown_expires():
    rl = RateLimiter(RateLimitConfig(max_requests=20, window_seconds=60.0, burst_max=3, burst_cooldown_seconds=5.0))
    rl.check("u", _ts(0))
    rl.check("u", _ts(0.1))
    rl.check("u", _ts(0.2))
    rl.check("u", _ts(0.3))  # burst block
    # After cooldown
    result = rl.check("u", _ts(10.0))
    assert result.allowed


# ---------------------------------------------------------------------------
# Disabled limiter
# ---------------------------------------------------------------------------

def test_disabled_always_allows():
    rl = RateLimiter(RateLimitConfig(max_requests=1, window_seconds=60.0, enabled=False))
    for _ in range(20):
        result = rl.check("user1")
    assert result.allowed
    assert result.reason == "rate_limiting_disabled"


# ---------------------------------------------------------------------------
# Per-user isolation
# ---------------------------------------------------------------------------

def test_users_are_isolated():
    rl = RateLimiter(RateLimitConfig(max_requests=2, window_seconds=60.0, burst_max=10))
    rl.check("alice", _ts(0))
    rl.check("alice", _ts(1))
    rl.check("alice", _ts(2))  # alice blocked
    result_bob = rl.check("bob", _ts(3))
    assert result_bob.allowed


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------

def test_reset_user():
    rl = RateLimiter(RateLimitConfig(max_requests=2, window_seconds=60.0, burst_max=10))
    rl.check("u", _ts(0))
    rl.check("u", _ts(1))
    rl.check("u", _ts(2))  # blocked
    rl.reset("u")
    result = rl.check("u", _ts(3))
    assert result.allowed


def test_reset_all():
    rl = RateLimiter(RateLimitConfig(max_requests=1, window_seconds=60.0, burst_max=10))
    rl.check("a", _ts(0))
    rl.check("b", _ts(0))
    rl.reset_all()
    assert rl.check("a", _ts(1)).allowed
    assert rl.check("b", _ts(1)).allowed


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def test_stats_returns_info():
    rl = RateLimiter(RateLimitConfig(max_requests=10, window_seconds=60.0, burst_max=5))
    rl.check("u", _ts(0))
    rl.check("u", _ts(5))
    stats = rl.stats("u", _ts(10))
    assert stats["requests_in_window"] == 2
    assert stats["max_requests"] == 10
    assert stats["window_seconds"] == 60.0


def test_stats_prunes_expired():
    rl = RateLimiter(RateLimitConfig(max_requests=10, window_seconds=5.0, burst_max=10))
    rl.check("u", _ts(0))
    stats = rl.stats("u", _ts(10))
    assert stats["requests_in_window"] == 0
