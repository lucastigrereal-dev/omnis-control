"""P27 Action Adapters — registry for provider adapters."""

from typing import Optional

ADAPTER_REGISTRY: dict[str, "ActionAdapter"] = {}


# Protocol imported lazily to avoid circular import
class ActionAdapter:
    """Protocol for action adapters. Each adapter wraps an external service."""

    @property
    def provider(self) -> str:
        raise NotImplementedError

    @property
    def supported_actions(self) -> list[str]:
        raise NotImplementedError

    def execute(self, action_name: str, params: dict) -> dict:
        raise NotImplementedError

    def health_check(self) -> bool:
        raise NotImplementedError

    def validate_params(self, action_name: str, params: dict) -> list[str]:
        raise NotImplementedError


def register_adapter(adapter: ActionAdapter) -> None:
    ADAPTER_REGISTRY[adapter.provider] = adapter


def get_adapter(provider: str) -> Optional[ActionAdapter]:
    return ADAPTER_REGISTRY.get(provider)


def list_providers() -> list[str]:
    return sorted(ADAPTER_REGISTRY.keys())
