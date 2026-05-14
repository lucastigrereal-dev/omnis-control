"""P27 RateLimiter — per-provider/action rate enforcement."""
import time
from dataclasses import dataclass, field
from collections import defaultdict

from src.real_world_actions.models import RateLimit


@dataclass
class _Bucket:
    """Tracks usage for one provider+action pair."""
    limit: RateLimit
    hourly: list[float] = field(default_factory=list)
    daily_count: int = 0
    concurrent: int = 0

    def clean_old(self, now: float) -> None:
        self.hourly = [t for t in self.hourly if now - t < 3600]


class RateLimiter:
    """Enforces rate limits per provider and action."""

    def __init__(self):
        self._buckets: dict[str, _Bucket] = {}  # key = "provider:action_name"
        self._default_limit = RateLimit()

    def _key(self, provider: str, action: str = "") -> str:
        return f"{provider}:{action}"

    def _get_or_create(self, provider: str, action: str, limit: RateLimit | None = None) -> _Bucket:
        k = self._key(provider, action)
        if k not in self._buckets:
            self._buckets[k] = _Bucket(limit=limit or self._default_limit)
        return self._buckets[k]

    def check(self, provider: str, action: str, limit: RateLimit | None = None) -> bool:
        """Returns True if action is within all rate limits."""
        now = time.time()
        bucket = self._get_or_create(provider, action, limit)
        bucket.clean_old(now)
        effective = limit or bucket.limit
        if len(bucket.hourly) >= effective.max_per_hour:
            return False
        if bucket.daily_count >= effective.max_per_day:
            return False
        if bucket.concurrent >= effective.concurrent_max:
            return False
        return True

    def record(self, provider: str, action: str) -> None:
        """Record a successful execution."""
        now = time.time()
        bucket = self._get_or_create(provider, action)
        bucket.clean_old(now)
        bucket.hourly.append(now)
        bucket.daily_count += 1

    def acquire(self, provider: str, action: str) -> None:
        """Mark concurrent slot as taken."""
        self._get_or_create(provider, action).concurrent += 1

    def release(self, provider: str, action: str) -> None:
        """Mark concurrent slot as freed."""
        bucket = self._get_or_create(provider, action)
        bucket.concurrent = max(0, bucket.concurrent - 1)

    def remaining(self, provider: str, action: str) -> dict:
        """Remaining capacity for a provider+action pair."""
        now = time.time()
        bucket = self._get_or_create(provider, action)
        bucket.clean_old(now)
        return {
            "hourly": max(0, bucket.limit.max_per_hour - len(bucket.hourly)),
            "daily": max(0, bucket.limit.max_per_day - bucket.daily_count),
            "concurrent": max(0, bucket.limit.concurrent_max - bucket.concurrent),
        }

    def stats(self) -> dict:
        """Snapshot of all tracked usage."""
        now = time.time()
        result = {}
        for k, bucket in self._buckets.items():
            bucket.clean_old(now)
            result[k] = {
                "hourly_used": len(bucket.hourly),
                "daily_used": bucket.daily_count,
                "concurrent": bucket.concurrent,
                "limit": bucket.limit.to_dict(),
            }
        return result

    def reset(self, provider: str = "", action: str = "") -> None:
        """Reset counters. If provider is empty, reset all."""
        if not provider:
            self._buckets.clear()
        else:
            k = self._key(provider, action)
            self._buckets.pop(k, None)
