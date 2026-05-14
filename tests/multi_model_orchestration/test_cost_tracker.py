"""Tests for P25 CostTracker."""
import pytest

from src.multi_model_orchestration.cost_tracker import CostTracker
from src.multi_model_orchestration.models import (
    PROVIDER_ANTHROPIC,
    PROVIDER_GROQ,
    ModelConfig,
)
from src.multi_model_orchestration.errors import CostLimitError


class TestCostTracker:
    @pytest.fixture
    def tracker(self):
        return CostTracker(daily_limit_usd=5.0, dry_run=True)

    def test_estimate_cost(self, tracker):
        model = ModelConfig.new("test", PROVIDER_ANTHROPIC, cost_per_1k_tokens=0.015)
        cost = tracker.estimate("a" * 1000, model)
        assert cost > 0.0

    def test_record_returns_cost(self, tracker):
        model = ModelConfig.new("test", PROVIDER_ANTHROPIC, cost_per_1k_tokens=0.010)
        cost = tracker.record(model, "generate_code", 500)
        assert cost == 0.005  # 500/1000 * 0.010

    def test_daily_total_accumulates(self, tracker):
        model = ModelConfig.new("test", PROVIDER_GROQ, cost_per_1k_tokens=0.001)
        tracker.record(model, "classify_intent", 1000)
        tracker.record(model, "classify_intent", 2000)
        assert tracker.daily_total == 0.003

    def test_daily_total_zero_on_empty(self, tracker):
        assert tracker.daily_total == 0.0

    def test_check_limit_dry_run_always_true(self, tracker):
        assert tracker.check_limit(100.0) is True  # dry_run ignores limits

    def test_check_limit_enforced_when_real(self):
        tracker = CostTracker(daily_limit_usd=1.0, dry_run=False)
        assert tracker.check_limit(0.5) is True
        # Simulate already spent 0.9
        model = ModelConfig.new("test", PROVIDER_GROQ, cost_per_1k_tokens=0.900)
        tracker.record(model, "test", 1000)
        assert tracker.check_limit(0.2) is False  # 0.9 + 0.2 > 1.0

    def test_assert_within_limit_passes(self, tracker):
        tracker.assert_within_limit(0.001)

    def test_assert_within_limit_raises(self):
        tracker = CostTracker(daily_limit_usd=0.01, dry_run=False)
        model = ModelConfig.new("test", PROVIDER_GROQ, cost_per_1k_tokens=0.009)
        tracker.record(model, "test", 1000)
        with pytest.raises(CostLimitError, match="exceed daily limit"):
            tracker.assert_within_limit(1.0)

    def test_by_model_breakdown(self, tracker):
        m1 = ModelConfig.new("model-a", PROVIDER_GROQ, cost_per_1k_tokens=0.001)
        m2 = ModelConfig.new("model-b", PROVIDER_ANTHROPIC, cost_per_1k_tokens=0.010)
        tracker.record(m1, "task1", 1000)
        tracker.record(m2, "task2", 500)
        breakdown = tracker.by_model()
        assert "model-a" in breakdown
        assert "model-b" in breakdown
        assert breakdown["model-a"] == 0.001
        assert breakdown["model-b"] == 0.005

    def test_by_provider_breakdown(self, tracker):
        m1 = ModelConfig.new("a", PROVIDER_GROQ, cost_per_1k_tokens=0.001)
        m2 = ModelConfig.new("b", PROVIDER_GROQ, cost_per_1k_tokens=0.002)
        tracker.record(m1, "task", 1000)
        tracker.record(m2, "task", 1000)
        assert tracker.by_provider()[PROVIDER_GROQ] == 0.003

    def test_remaining_budget(self, tracker):
        model = ModelConfig.new("test", PROVIDER_GROQ, cost_per_1k_tokens=0.001)
        tracker.record(model, "task", 1000)
        assert tracker.remaining_budget == 4.999

    def test_entry_count(self, tracker):
        assert tracker.entry_count == 0

    def test_reset_clears_entries(self, tracker):
        model = ModelConfig.new("test", PROVIDER_GROQ, cost_per_1k_tokens=0.001)
        tracker.record(model, "task", 1000)
        tracker.reset()
        assert tracker.entry_count == 0
        assert tracker.daily_total == 0.0

    def test_to_dict(self, tracker):
        d = tracker.to_dict()
        assert "daily_limit_usd" in d
        assert "daily_total" in d
        assert "remaining_budget" in d
        assert "by_model" in d
        assert "by_provider" in d
