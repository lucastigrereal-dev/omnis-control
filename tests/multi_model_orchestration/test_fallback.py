"""Tests for P25 FallbackChain."""
import pytest

from src.multi_model_orchestration.fallback import FallbackChain
from src.multi_model_orchestration.models import (
    CAPABILITY_TEXT,
    PROVIDER_MOCK,
    ModelConfig,
)
from src.multi_model_orchestration.registry import ModelRegistry
from src.multi_model_orchestration.errors import AllModelsExhaustedError


class TestFallbackChain:
    @pytest.fixture
    def registry(self):
        r = ModelRegistry()
        r.seed_defaults()
        return r

    @pytest.fixture
    def chain(self, registry):
        return FallbackChain(["mock-model", "groq-llama-3-70b"], registry)

    def test_fallback_executes_first_model(self, chain):
        result = chain.execute("test prompt")
        assert result["status"] == "dry_run"  # mock adapter always dry_run
        assert result["fallback_used"] is False

    def test_fallback_logs_attempts(self, chain):
        result = chain.execute("test")
        assert chain.attempts == 0  # success on first try, no fallback needed

    def test_fallback_skips_unknown_model(self, registry):
        chain = FallbackChain(["nonexistent-model", "mock-model"], registry)
        result = chain.execute("test")
        assert result["status"] == "dry_run"
        assert result["fallback_used"] is True
        assert chain.attempts == 1  # one skip

    def test_fallback_skips_disabled_model(self, registry):
        mock = registry.find_by_name("mock-model")
        registry.disable(mock.model_id)
        chain = FallbackChain(["mock-model"], registry)
        with pytest.raises(AllModelsExhaustedError):
            chain.execute("test")
        assert chain.attempts == 1

    def test_fallback_raises_when_all_exhausted(self, registry):
        chain = FallbackChain(["nonexistent-1", "nonexistent-2"], registry)
        with pytest.raises(AllModelsExhaustedError, match="All 2 fallback models failed"):
            chain.execute("test")

    def test_attempt_log_preserved(self, registry):
        chain = FallbackChain(["nonexistent", "nonexistent-2"], registry)
        try:
            chain.execute("test")
        except AllModelsExhaustedError:
            pass
        assert len(chain.attempt_log) == 2

    def test_current_model_set_on_success(self, chain):
        chain.execute("test")
        assert chain.current_model is not None
        assert chain.current_model.name == "mock-model"
