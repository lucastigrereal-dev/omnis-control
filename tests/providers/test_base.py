"""Tests for Provider base and ProviderRegistry."""
import pytest
from src.providers.base import Provider, ProviderHealth, ProviderStatus
from src.providers.registry import ProviderRegistry


class ConcreteProvider(Provider):
    @property
    def name(self) -> str:
        return "test"

    @property
    def backend(self) -> str:
        return "mock"

    def health_check(self) -> ProviderHealth:
        return ProviderHealth(status=ProviderStatus.OK, provider_name=self.name, backend=self.backend)


class TestProviderHealth:
    def test_ok_status(self):
        h = ProviderHealth(status=ProviderStatus.OK, provider_name="tracing", backend="local")
        assert h.ok is True

    def test_degraded_not_ok(self):
        h = ProviderHealth(status=ProviderStatus.DEGRADED, provider_name="tracing", backend="local")
        assert h.ok is False

    def test_unavailable_not_ok(self):
        h = ProviderHealth(status=ProviderStatus.UNAVAILABLE, provider_name="tracing", backend="local")
        assert h.ok is False


class TestProviderRegistry:
    def test_register_and_get(self):
        registry = ProviderRegistry()
        p = ConcreteProvider()
        registry.register(p)
        assert registry.get("test") is p

    def test_get_missing_raises(self):
        registry = ProviderRegistry()
        with pytest.raises(KeyError):
            registry.get("nonexistent")

    def test_has(self):
        registry = ProviderRegistry()
        registry.register(ConcreteProvider())
        assert registry.has("test") is True
        assert registry.has("other") is False

    def test_health_all(self):
        registry = ProviderRegistry()
        registry.register(ConcreteProvider())
        health = registry.health_all()
        assert "test" in health
        assert health["test"].ok is True

    def test_default_registry_has_all_providers(self):
        registry = ProviderRegistry.default()
        assert registry.has("tracing")
        assert registry.has("memory")
        assert registry.has("workflow")
        assert registry.has("mcp")
        assert registry.has("runtime")

    def test_default_registry_all_healthy(self):
        registry = ProviderRegistry.default()
        for name, health in registry.health_all().items():
            assert health.ok, f"Provider '{name}' not healthy: {health.details}"

    def test_get_typed(self):
        from src.providers.tracing import TracingProvider
        registry = ProviderRegistry.default()
        tracer = registry.get_typed("tracing", TracingProvider)
        assert isinstance(tracer, TracingProvider)

    def test_dispose_all_safe(self):
        registry = ProviderRegistry.default()
        registry.dispose_all()  # must not raise
