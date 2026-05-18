"""ProviderRegistry — central injection point for all OMNIS providers.

Usage:
    registry = ProviderRegistry.default()
    tracer = registry.get("tracing")
    with tracer.span("my_operation") as ctx:
        ...

The registry is the ONLY place where OMNIS decides which backend to use.
Business logic never imports backends directly.
"""
from __future__ import annotations

from typing import Any, Optional, Type, TypeVar

from src.providers.base import Provider, ProviderHealth

T = TypeVar("T", bound=Provider)


class ProviderRegistry:
    """Holds and resolves OMNIS providers by name."""

    def __init__(self) -> None:
        self._providers: dict[str, Provider] = {}

    def register(self, provider: Provider) -> "ProviderRegistry":
        self._providers[provider.name] = provider
        return self

    def get(self, name: str) -> Provider:
        provider = self._providers.get(name)
        if provider is None:
            raise KeyError(f"Provider '{name}' not registered. Available: {list(self._providers)}")
        return provider

    def get_typed(self, name: str, type_: Type[T]) -> T:
        provider = self.get(name)
        if not isinstance(provider, type_):
            raise TypeError(f"Provider '{name}' is {type(provider).__name__}, expected {type_.__name__}")
        return provider

    def has(self, name: str) -> bool:
        return name in self._providers

    def health_all(self) -> dict[str, ProviderHealth]:
        return {name: p.health_check() for name, p in self._providers.items()}

    def dispose_all(self) -> None:
        for p in self._providers.values():
            p.dispose()

    @classmethod
    def default(cls) -> "ProviderRegistry":
        """Build default registry with built-in fallback providers (zero external deps)."""
        from src.providers.tracing import LocalJSONLProvider
        from src.providers.memory import LocalMemoryProvider
        from src.providers.workflow import SequentialWorkflowProvider
        from src.providers.mcp import LocalToolRegistryProvider
        from src.providers.runtime import MockRuntimeProvider

        registry = cls()
        registry.register(LocalJSONLProvider())
        registry.register(LocalMemoryProvider())
        registry.register(SequentialWorkflowProvider())
        registry.register(LocalToolRegistryProvider())
        registry.register(MockRuntimeProvider())
        return registry

    @classmethod
    def production(cls) -> "ProviderRegistry":
        """Build production registry — tries real backends, falls back to local.

        Override individual providers via environment variables:
        - LANGFUSE_PUBLIC_KEY + LANGFUSE_SECRET_KEY → LangfuseProvider
        - Future: MEM0_API_KEY → Mem0Provider
        - Future: LANGGRAPH_ENABLED=1 → LangGraphProvider
        """
        import os
        from src.providers.tracing import LocalJSONLProvider, LangfuseProvider
        from src.providers.memory import LocalMemoryProvider
        from src.providers.workflow import SequentialWorkflowProvider
        from src.providers.mcp import LocalToolRegistryProvider
        from src.providers.runtime import SubprocessRuntimeProvider

        registry = cls()

        # Tracing: try Langfuse, fall back to local
        if os.environ.get("LANGFUSE_PUBLIC_KEY"):
            registry.register(LangfuseProvider(fallback=LocalJSONLProvider()))
        else:
            registry.register(LocalJSONLProvider())

        registry.register(LocalMemoryProvider())
        registry.register(SequentialWorkflowProvider())
        registry.register(LocalToolRegistryProvider())
        registry.register(SubprocessRuntimeProvider())
        return registry
