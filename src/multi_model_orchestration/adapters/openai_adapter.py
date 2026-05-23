"""P25 OpenAI Adapter — real calls via openai SDK."""
from __future__ import annotations

import os
from datetime import datetime, timezone

from openai import OpenAI

from src.multi_model_orchestration.models import ModelConfig


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class OpenaiAdapter:
    provider = "openai"

    def __init__(self) -> None:
        self._client: OpenAI | None = None

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            api_key = os.environ.get("OPENAI_API_KEY", "")
            self._client = OpenAI(api_key=api_key)
        return self._client

    def execute(self, prompt: str, model: ModelConfig, **kwargs: object) -> dict[str, object]:
        t0 = datetime.now(timezone.utc)
        try:
            response = self.client.chat.completions.create(
                model=model.name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=kwargs.get("max_tokens", model.max_tokens),
                temperature=kwargs.get("temperature", 0.7),
            )
            elapsed = (datetime.now(timezone.utc) - t0).total_seconds() * 1000
            content = response.choices[0].message.content or ""
            usage = response.usage
            tokens_used = usage.total_tokens if usage else self.estimate_tokens(prompt)
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
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key or api_key.startswith("sk-"):
            # key set but might not be valid — try a minimal call
            try:
                self.client.models.list(limit=1)
                return True
            except Exception:
                return False
        return False

    def estimate_tokens(self, prompt: str) -> int:
        return max(1, len(prompt) // 4)


def register() -> None:
    from src.multi_model_orchestration.adapters import register_adapter
    register_adapter("openai", lambda: OpenaiAdapter())
