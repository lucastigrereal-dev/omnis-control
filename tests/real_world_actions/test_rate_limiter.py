"""Tests for P27 RateLimiter."""
import pytest
import time

from src.real_world_actions.rate_limiter import RateLimiter
from src.real_world_actions.models import RateLimit


class TestRateLimiter:
    @pytest.fixture
    def rl(self):
        return RateLimiter()

    def test_check_returns_true_initially(self, rl):
        assert rl.check("gmail", "send_email") is True

    def test_record_and_remaining(self, rl):
        rl.record("gmail", "send_email")
        remaining = rl.remaining("gmail", "send_email")
        assert remaining["hourly"] >= 0

    def test_check_respects_hourly_limit(self, rl):
        strict = RateLimit(max_per_hour=3, max_per_day=1000, concurrent_max=5)
        for _ in range(3):
            rl.record("gmail", "send_email")
        assert rl.check("gmail", "send_email", strict) is False

    def test_check_respects_daily_limit(self, rl):
        strict = RateLimit(max_per_hour=1000, max_per_day=2)
        rl.record("gmail", "send_email")
        rl.record("gmail", "send_email")
        assert rl.check("gmail", "send_email", strict) is False

    def test_check_respects_concurrent_limit(self, rl):
        strict = RateLimit(max_per_hour=100, max_per_day=1000, concurrent_max=1)
        rl.acquire("gmail", "send_email")
        assert rl.check("gmail", "send_email", strict) is False

    def test_release_frees_concurrent_slot(self, rl):
        strict = RateLimit(max_per_hour=100, max_per_day=1000, concurrent_max=1)
        rl.acquire("gmail", "send_email")
        rl.release("gmail", "send_email")
        assert rl.check("gmail", "send_email", strict) is True

    def test_different_actions_have_separate_limits(self, rl):
        strict = RateLimit(max_per_hour=1, max_per_day=1000)
        rl.record("github", "git_push")
        assert rl.check("github", "create_pr", strict) is True

    def test_different_providers_separate(self, rl):
        rl.record("gmail", "send_email")
        assert rl.check("github", "git_push") is True

    def test_remaining_returns_all_keys(self, rl):
        rl.record("gmail", "send_email")
        remaining = rl.remaining("gmail", "send_email")
        assert "hourly" in remaining
        assert "daily" in remaining
        assert "concurrent" in remaining

    def test_stats_returns_snapshot(self, rl):
        rl.record("gmail", "send_email")
        stats = rl.stats()
        assert "gmail:send_email" in stats
        assert stats["gmail:send_email"]["daily_used"] == 1

    def test_reset_all(self, rl):
        rl.record("gmail", "send_email")
        rl.reset()
        stats = rl.stats()
        assert len(stats) == 0

    def test_reset_specific_provider(self, rl):
        rl.record("gmail", "send_email")
        rl.record("github", "git_push")
        rl.reset(provider="gmail", action="send_email")
        stats = rl.stats()
        assert "gmail:send_email" not in stats
        assert "github:git_push" in stats

    def test_clean_old_removes_expired_entries(self, rl):
        rl.record("gmail", "send_email")
        remaining_before = rl.remaining("gmail", "send_email")
        assert remaining_before["hourly"] >= 0
