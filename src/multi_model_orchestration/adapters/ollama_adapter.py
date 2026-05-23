"""P25 Ollama Adapter — real calls via HTTP to local Ollama server."""
from __future__ import annotations

import json
import os
import urllib.request
from datetime import datetime, timezone

from src.multi_model_orchestration.models import ModelConfig


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class OllamaAdapter:
    provider = "ollama"

    def __init__(self) -> None:
        self._base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

    def execute(self, prompt: str, model: ModelConfig, **kwargs: object) -> dict[str, object]:
        t0 = datetime.now(timezone.utc)
        try:
            messages = []
            system = kwargs.get("system", "")
            if system:
                messages.append({"role": "system", "content": str(system)})
            messages.append({"role": "user", "content": prompt})

            payload = json.dumps({
                "model": model.name,
                "messages": messages,
                "stream": False,
                "options": {
                    "num_predict": kwargs.get("max_tokens", model.max_tokens),
                },
            }).encode("utf-8")

            req = urllib.request.Request(
                f"{self._base_url}/api/chat",
                data=payload,
                headers={"Content-Type": "application/json"},
            )

            with urllib.request.urlopen(req, timeout=kwargs.get("timeout", 120)) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            elapsed = (datetime.now(timezone.utc) - t0).total_seconds() * 1000
            content = data.get("message", {}).get("content", "")
            eval_count = data.get("eval_count", 0)
            prompt_eval_count = data.get("prompt_eval_count", 0)
            tokens_used = eval_count + prompt_eval_count or self.estimate_tokens(prompt)

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
        try:
            req = urllib.request.Request(
                f"{self._base_url}/api/tags",
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status == 200
        except Exception:
            return False

    def estimate_tokens(self, prompt: str) -> int:
        return max(1, len(prompt) // 4)


def register() -> None:
    from src.multi_model_orchestration.adapters import register_adapter
    register_adapter("ollama", lambda: OllamaAdapter())
