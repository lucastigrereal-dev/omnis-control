"""P25 MockAdapter — returns simulated responses, never calls real APIs."""
from __future__ import annotations

from datetime import datetime, timezone

from src.multi_model_orchestration.adapters import ModelAdapter
from src.multi_model_orchestration.models import ModelConfig


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class MockAdapter:
    """Adapter that returns deterministic mock responses. Never calls external APIs."""

    provider = "mock"

    def execute(self, prompt: str, model: ModelConfig, **kwargs: object) -> dict[str, object]:
        return {
            "status": "dry_run",
            "model": model.name,
            "provider": self.provider,
            "content": f"[MOCK] Simulated response for prompt ({len(prompt)} chars)",
            "tokens_used": self.estimate_tokens(prompt),
            "latency_ms": 1,
            "timestamp": _now_iso(),
        }

    def health_check(self) -> bool:
        return True

    def estimate_tokens(self, prompt: str) -> int:
        return max(1, len(prompt) // 4)


def register() -> None:
    """Register mock adapter in the global adapter registry."""
    from src.multi_model_orchestration.adapters import register_adapter
    register_adapter("mock", lambda: MockAdapter())
