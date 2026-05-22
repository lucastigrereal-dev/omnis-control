"""P25 Anthropic Adapter — real calls via anthropic SDK."""
from __future__ import annotations

import os
from datetime import datetime, timezone

from anthropic import Anthropic

from src.multi_model_orchestration.models import ModelConfig


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class AnthropicAdapter:
    provider = "anthropic"

    def __init__(self) -> None:
        self._client: Anthropic | None = None

    @property
    def client(self) -> Anthropic:
        if self._client is None:
            api_key = os.environ.get("ANTHROPIC_API_KEY", "")
            self._client = Anthropic(api_key=api_key)
        return self._client

    def execute(self, prompt: str, model: ModelConfig, **kwargs: dict) -> dict:
        t0 = datetime.now(timezone.utc)
        try:
            response = self.client.messages.create(
                model=model.name,
                max_tokens=kwargs.get("max_tokens", model.max_tokens),
                messages=[{"role": "user", "content": prompt}],
            )
            elapsed = (datetime.now(timezone.utc) - t0).total_seconds() * 1000
            content = ""
            for block in response.content:
                if block.type == "text":
                    content += block.text
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            return {
                "status": "ok",
                "model": model.name,
                "provider": self.provider,
                "content": content,
                "tokens_used": tokens_used,
                "latency_ms": int(elapsed),
                "timestamp": _now_iso(),
            }
        except Exception as exc:
            return {
                "status": "error",
                "model": model.name,
                "provider": self.provider,
                "content": "",
                "error": str(exc),
                "tokens_used": 0,
                "latency_ms": 0,
                "timestamp": _now_iso(),
            }

    def health_check(self) -> bool:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            return False
        return True

    def estimate_tokens(self, prompt: str) -> int:
        return max(1, len(prompt) // 4)


def register() -> None:
    from src.multi_model_orchestration.adapters import register_adapter
    register_adapter("anthropic", lambda: AnthropicAdapter())
