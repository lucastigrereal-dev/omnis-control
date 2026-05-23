"""P25 adapters — thin wrappers for model providers."""
from __future__ import annotations

from typing import Callable, Protocol

from src.multi_model_orchestration.models import ModelConfig


class ModelAdapter(Protocol):
    """Protocol for model provider adapters."""

    provider: str

    def execute(self, prompt: str, model: ModelConfig, **kwargs: object) -> dict[str, object]:
        """Execute a prompt on the model. Returns standardized response dict."""
        ...

    def health_check(self) -> bool:
        """True if the provider is accessible."""
        ...

    def estimate_tokens(self, prompt: str) -> int:
        """Estimate token count for a prompt."""
        ...


AdapterFactory = Callable[[], ModelAdapter]

ADAPTER_REGISTRY: dict[str, AdapterFactory] = {}


def register_adapter(provider: str, factory: AdapterFactory) -> None:
    """Register an adapter factory for a provider."""
    ADAPTER_REGISTRY[provider] = factory


def get_adapter(provider: str) -> ModelAdapter | None:
    """Get an adapter instance for a provider, or None if not registered."""
    factory = ADAPTER_REGISTRY.get(provider)
    if factory is None:
        return None
    return factory()


def list_adapters() -> list[str]:
    """List all registered adapter providers."""
    return sorted(ADAPTER_REGISTRY.keys())


def has_adapter(provider: str) -> bool:
    """Check if an adapter is registered for a provider."""
    return provider in ADAPTER_REGISTRY
