"""W158 — Rate Limiter & Throttle Guard for remote commands."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from .models import _new_id, _now_iso


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _utcnow_ts() -> float:
    return _utcnow().timestamp()


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

@dataclass
class RateLimitConfig:
    max_requests: int = 10          # max allowed in the window
    window_seconds: float = 60.0    # rolling window size
    burst_max: int = 3              # max consecutive requests before burst block
    burst_cooldown_seconds: float = 10.0
    enabled: bool = True

    def to_dict(self) -> dict:
        return {
            "max_requests": self.max_requests,
            "window_seconds": self.window_seconds,
            "burst_max": self.burst_max,
            "burst_cooldown_seconds": self.burst_cooldown_seconds,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RateLimitConfig":
        return cls(
            max_requests=data.get("max_requests", 10),
            window_seconds=data.get("window_seconds", 60.0),
            burst_max=data.get("burst_max", 3),
            burst_cooldown_seconds=data.get("burst_cooldown_seconds", 10.0),
            enabled=data.get("enabled", True),
        )

    @classmethod
    def strict(cls) -> "RateLimitConfig":
        return cls(max_requests=5, window_seconds=60.0, burst_max=2, burst_cooldown_seconds=15.0)

    @classmethod
    def permissive(cls) -> "RateLimitConfig":
        return cls(max_requests=100, window_seconds=60.0, burst_max=20, burst_cooldown_seconds=2.0)


# ---------------------------------------------------------------------------
# Per-user bucket
# ---------------------------------------------------------------------------

@dataclass
class _UserBucket:
    user_id: str
    timestamps: list[float] = field(default_factory=list)
    burst_streak: int = 0
    last_burst_block_at: Optional[float] = None

    def prune(self, window_seconds: float, now: float) -> None:
        cutoff = now - window_seconds
        self.timestamps = [t for t in self.timestamps if t >= cutoff]

    def in_burst_cooldown(self, cooldown: float, now: float) -> bool:
        if self.last_burst_block_at is None:
            return False
        return (now - self.last_burst_block_at) < cooldown


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------

@dataclass
class ThrottleResult:
    result_id: str = field(default_factory=lambda: _new_id("thr"))
    user_id: str = ""
    allowed: bool = True
    reason: str = ""
    requests_in_window: int = 0
    window_resets_in: float = 0.0
    checked_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "result_id": self.result_id,
            "user_id": self.user_id,
            "allowed": self.allowed,
            "reason": self.reason,
            "requests_in_window": self.requests_in_window,
            "window_resets_in": round(self.window_resets_in, 2),
            "checked_at": self.checked_at,
        }


# ---------------------------------------------------------------------------
# Rate Limiter
# ---------------------------------------------------------------------------

class RateLimiter:
    """Sliding-window rate limiter with burst detection per user."""

    def __init__(self, config: Optional[RateLimitConfig] = None) -> None:
        self.config = config or RateLimitConfig()
        self._buckets: dict[str, _UserBucket] = {}

    def _bucket(self, user_id: str) -> _UserBucket:
        if user_id not in self._buckets:
            self._buckets[user_id] = _UserBucket(user_id=user_id)
        return self._buckets[user_id]

    def check(self, user_id: str, _now_ts: Optional[float] = None) -> ThrottleResult:
        now = _now_ts if _now_ts is not None else _utcnow_ts()
        result = ThrottleResult(user_id=user_id)

        if not self.config.enabled:
            result.allowed = True
            result.reason = "rate_limiting_disabled"
            return result

        bucket = self._bucket(user_id)
        bucket.prune(self.config.window_seconds, now)

        # Burst cooldown check
        if bucket.in_burst_cooldown(self.config.burst_cooldown_seconds, now):
            remaining = self.config.burst_cooldown_seconds - (now - bucket.last_burst_block_at)
            result.allowed = False
            result.reason = "burst_cooldown"
            result.window_resets_in = round(remaining, 2)
            result.requests_in_window = len(bucket.timestamps)
            return result

        # Window limit check
        count = len(bucket.timestamps)
        result.requests_in_window = count

        if count >= self.config.max_requests:
            oldest = bucket.timestamps[0] if bucket.timestamps else now
            result.allowed = False
            result.reason = "rate_limit_exceeded"
            result.window_resets_in = round((oldest + self.config.window_seconds) - now, 2)
            return result

        # Burst streak check
        if count > 0:
            gap = now - bucket.timestamps[-1]
            if gap < 1.0:  # sub-second gap = burst
                bucket.burst_streak += 1
            else:
                bucket.burst_streak = 0

        if bucket.burst_streak >= self.config.burst_max:
            bucket.last_burst_block_at = now
            bucket.burst_streak = 0
            result.allowed = False
            result.reason = "burst_detected"
            result.window_resets_in = self.config.burst_cooldown_seconds
            return result

        # Allow
        bucket.timestamps.append(now)
        result.allowed = True
        result.reason = "ok"
        result.requests_in_window = len(bucket.timestamps)
        return result

    def reset(self, user_id: str) -> None:
        self._buckets.pop(user_id, None)

    def reset_all(self) -> None:
        self._buckets.clear()

    def stats(self, user_id: str, _now_ts: Optional[float] = None) -> dict:
        now = _now_ts if _now_ts is not None else _utcnow_ts()
        bucket = self._bucket(user_id)
        bucket.prune(self.config.window_seconds, now)
        return {
            "user_id": user_id,
            "requests_in_window": len(bucket.timestamps),
            "max_requests": self.config.max_requests,
            "window_seconds": self.config.window_seconds,
            "burst_streak": bucket.burst_streak,
            "in_burst_cooldown": bucket.in_burst_cooldown(self.config.burst_cooldown_seconds, now),
        }
