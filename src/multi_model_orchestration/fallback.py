"""P25 FallbackChain — try models sequentially until one succeeds."""
from __future__ import annotations

from typing import Optional

from src.multi_model_orchestration.adapters import get_adapter
from src.multi_model_orchestration.errors import AllModelsExhaustedError, ProviderUnavailableError
from src.multi_model_orchestration.models import ModelConfig
from src.multi_model_orchestration.registry import ModelRegistry


class FallbackChain:
    """Execute a prompt against a chain of models: try A, if fail try B, then C."""

    def __init__(self, model_names: list[str], registry: ModelRegistry) -> None:
        self.model_names = model_names
        self.registry = registry
        self._attempts: list[dict] = []
        self._current_model: Optional[ModelConfig] = None

    def execute(self, prompt: str, context: Optional[dict] = None) -> dict:
        """Execute prompt, falling back through model chain on failure."""
        context = context or {}
        last_error = None

        for name in self.model_names:
            model = self.registry.find_by_name(name)
            if model is None or not model.enabled:
                self._attempts.append({"model": name, "status": "skipped", "reason": "not found or disabled"})
                continue

            adapter = get_adapter(model.provider)
            if adapter is None:
                self._attempts.append({"model": name, "status": "skipped", "reason": f"no adapter for {model.provider}"})
                continue

            if not adapter.health_check():
                self._attempts.append({"model": name, "status": "skipped", "reason": "health check failed"})
                continue

            try:
                result = adapter.execute(prompt, model, **context)
                result["fallback_used"] = len(self._attempts) > 0
                result["fallback_attempts"] = self._attempts
                self._current_model = model
                return result
            except Exception as e:
                self._attempts.append({"model": name, "status": "failed", "error": str(e)[:200]})
                last_error = e

        raise AllModelsExhaustedError(
            f"All {len(self.model_names)} fallback models failed. Attempts: {self._attempts}"
        ) from last_error

    @property
    def attempts(self) -> int:
        return len(self._attempts)

    @property
    def attempt_log(self) -> list[dict]:
        return list(self._attempts)

    @property
    def current_model(self) -> Optional[ModelConfig]:
        return self._current_model
