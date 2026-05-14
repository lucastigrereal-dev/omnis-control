"""Tests for P25 ModelRegistry."""
import pytest

from src.multi_model_orchestration.models import (
    CAPABILITY_ANALYSIS,
    CAPABILITY_CODE,
    CAPABILITY_PLANNING,
    CAPABILITY_TEXT,
    COMPLEXITY_CRITICAL,
    COMPLEXITY_HIGH,
    COMPLEXITY_LOW,
    PROVIDER_ANTHROPIC,
    PROVIDER_GROQ,
    PROVIDER_MOCK,
    ModelConfig,
    TaskClass,
)
from src.multi_model_orchestration.registry import ModelRegistry
from src.multi_model_orchestration.errors import InvalidModelConfigError


class TestModelRegistry:
    @pytest.fixture
    def registry(self):
        r = ModelRegistry()
        r.seed_defaults()
        return r

    @pytest.fixture
    def empty_registry(self):
        return ModelRegistry()

    # ── seed_defaults ──────────────────────────────────────────────────────

    def test_seed_defaults_populates_registry(self, registry):
        assert registry.count >= 4

    def test_seed_defaults_includes_anthropic(self, registry):
        anthropic = registry.list_by_provider(PROVIDER_ANTHROPIC)
        assert len(anthropic) >= 2

    def test_seed_defaults_includes_mock(self, registry):
        assert len(registry.list_by_provider(PROVIDER_MOCK)) >= 1

    # ── register / unregister ──────────────────────────────────────────────

    def test_register_adds_model(self, empty_registry):
        m = ModelConfig.new("test-model", PROVIDER_MOCK)
        empty_registry.register(m)
        assert empty_registry.count == 1

    def test_unregister_removes_model(self, registry):
        m = ModelConfig.new("temp", PROVIDER_MOCK)
        registry.register(m)
        removed = registry.unregister(m.model_id)
        assert removed is True
        assert registry.get(m.model_id) is None

    def test_unregister_nonexistent(self, registry):
        assert registry.unregister("nonexistent") is False

    def test_get_returns_model(self, registry):
        m = ModelConfig.new("find-me", PROVIDER_MOCK)
        registry.register(m)
        assert registry.get(m.model_id) is not None

    def test_get_nonexistent(self, registry):
        assert registry.get("nonexistent") is None

    def test_find_by_name(self, registry):
        m = registry.find_by_name("claude-haiku-4-5")
        assert m is not None
        assert m.provider == PROVIDER_ANTHROPIC

    def test_find_by_name_nonexistent(self, registry):
        assert registry.find_by_name("nonexistent") is None

    # ── enable / disable ──────────────────────────────────────────────────

    def test_disable_model(self, registry):
        models = registry.list_enabled()
        model_id = models[0].model_id
        registry.disable(model_id)
        assert registry.get(model_id).enabled is False

    def test_enable_model(self, registry):
        models = registry.list_enabled()
        model_id = models[0].model_id
        registry.disable(model_id)
        registry.enable(model_id)
        assert registry.get(model_id).enabled is True

    def test_disable_nonexistent_raises(self, registry):
        with pytest.raises(InvalidModelConfigError):
            registry.disable("nonexistent")

    def test_enable_nonexistent_raises(self, registry):
        with pytest.raises(InvalidModelConfigError):
            registry.enable("nonexistent")

    # ── find ──────────────────────────────────────────────────────────────

    def test_find_by_capability(self, registry):
        results = registry.find(capabilities=[CAPABILITY_CODE])
        assert len(results) >= 1
        for m in results:
            assert CAPABILITY_CODE in m.capabilities

    def test_find_by_multiple_capabilities(self, registry):
        results = registry.find(capabilities=[CAPABILITY_CODE, CAPABILITY_TEXT])
        assert len(results) >= 1

    def test_find_with_max_cost(self, registry):
        results = registry.find(max_cost=0.002)
        for m in results:
            assert m.cost_per_1k_tokens <= 0.002

    def test_find_excludes_disabled(self, registry):
        models = registry.list_enabled()
        registry.disable(models[0].model_id)
        results = registry.find()
        disabled = [m for m in results if m.model_id == models[0].model_id]
        assert len(disabled) == 0

    # ── find_for_task ─────────────────────────────────────────────────────

    def test_find_for_low_complexity_task(self, registry):
        tc = TaskClass.new("classify_intent", complexity=COMPLEXITY_LOW, min_capabilities=["classification"])
        results = registry.find_for_task(tc)
        assert len(results) >= 1

    def test_find_for_high_complexity_task(self, registry):
        tc = TaskClass.new("plan_mission", complexity=COMPLEXITY_HIGH, min_capabilities=[CAPABILITY_PLANNING])
        results = registry.find_for_task(tc)
        assert len(results) >= 1

    def test_find_for_critical_task(self, registry):
        tc = TaskClass.new("execute_financial", complexity=COMPLEXITY_CRITICAL, min_capabilities=[CAPABILITY_ANALYSIS])
        results = registry.find_for_task(tc)
        assert len(results) >= 1

    # ── list methods ──────────────────────────────────────────────────────

    def test_list_all(self, registry):
        assert registry.list_all() == sorted(registry.list_all(), key=lambda m: m.priority)

    def test_list_enabled_only(self, registry):
        all_enabled = registry.list_enabled()
        for m in all_enabled:
            assert m.enabled is True

    def test_list_by_provider(self, registry):
        groq_models = registry.list_by_provider(PROVIDER_GROQ)
        for m in groq_models:
            assert m.provider == PROVIDER_GROQ

    def test_list_by_capability(self, registry):
        analysis_models = registry.list_by_capability(CAPABILITY_ANALYSIS)
        for m in analysis_models:
            assert CAPABILITY_ANALYSIS in m.capabilities

    # ── info ──────────────────────────────────────────────────────────────

    def test_count(self, registry):
        assert registry.count == len(registry.list_all())

    def test_enabled_count(self, registry):
        assert registry.enabled_count <= registry.count

    def test_providers(self, registry):
        assert PROVIDER_ANTHROPIC in registry.providers
        assert PROVIDER_MOCK in registry.providers
