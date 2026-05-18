"""ModelRouterProvider — model-agnostic LLM routing for OMNIS.

Routes model calls between Claude, OpenRouter, Ollama, etc.
OMNIS core never imports the Anthropic SDK directly — uses this provider.

Backends:
1. MockModelProvider    — deterministic responses for tests (zero deps)
2. ClaudeProvider       — Anthropic SDK (optional: pip install anthropic)
3. OpenRouterProvider   — any model via OpenRouter (optional: pip install openai)
4. OllamaProvider       — local models via Ollama (optional: pip install ollama)
"""
from __future__ import annotations

import os
from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

from src.providers.base import Provider, ProviderHealth, ProviderStatus


@dataclass
class ModelRequest:
    """Unified LLM request across all providers."""
    prompt: str
    system: Optional[str] = None
    model: Optional[str] = None
    max_tokens: int = 1024
    temperature: float = 0.7
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelResponse:
    """Unified LLM response across all providers."""
    content: str
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "model": self.model,
            "provider": self.provider,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost_usd": self.cost_usd,
        }


class ModelRouterProvider(Provider):
    """Abstract model router. Use registry.get('model') to get instance."""

    @property
    def name(self) -> str:
        return "model"

    @abstractmethod
    def complete(self, request: ModelRequest) -> ModelResponse:
        """Complete a prompt. Returns ModelResponse."""

    def ask(self, prompt: str, *, system: Optional[str] = None, model: Optional[str] = None) -> str:
        """Convenience method. Returns just the text content."""
        return self.complete(ModelRequest(prompt=prompt, system=system, model=model)).content


# ── Built-in: MockModelProvider ────────────────────────────────────────────

class MockModelProvider(ModelRouterProvider):
    """Deterministic responses for tests. Zero external deps."""

    def __init__(self, response: str = "mock response") -> None:
        self._response = response

    @property
    def backend(self) -> str:
        return "mock"

    def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            status=ProviderStatus.OK,
            provider_name=self.name,
            backend=self.backend,
        )

    def complete(self, request: ModelRequest) -> ModelResponse:
        return ModelResponse(
            content=self._response,
            model="mock",
            provider=self.backend,
            input_tokens=len(request.prompt.split()),
            output_tokens=len(self._response.split()),
        )


# ── Optional: ClaudeProvider ───────────────────────────────────────────────

class ClaudeProvider(ModelRouterProvider):
    """ModelRouterProvider backed by Anthropic Claude.

    Requires: pip install anthropic
    Env vars: ANTHROPIC_API_KEY

    Default model: claude-sonnet-4-6 (latest Sonnet)
    Falls back to MockModelProvider when not available.
    """

    DEFAULT_MODEL = "claude-sonnet-4-6"

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: str = DEFAULT_MODEL,
        fallback: Optional[ModelRouterProvider] = None,
    ) -> None:
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self._default_model = default_model
        self._fallback = fallback or MockModelProvider()
        self._client: Any = None
        self._available = False
        self._init()

    def _init(self) -> None:
        if not self._api_key:
            return
        try:
            import anthropic  # type: ignore
            self._client = anthropic.Anthropic(api_key=self._api_key)
            self._available = True
        except ImportError:
            self._available = False

    @property
    def backend(self) -> str:
        return f"claude({self._default_model})" if self._available else "mock(claude_unavailable)"

    def health_check(self) -> ProviderHealth:
        if not self._available:
            return ProviderHealth(
                status=ProviderStatus.DEGRADED,
                provider_name=self.name,
                backend=self.backend,
                details={
                    "reason": "anthropic not installed or ANTHROPIC_API_KEY not set",
                    "fallback": "mock",
                    "api_key_set": bool(self._api_key),
                },
            )
        return ProviderHealth(
            status=ProviderStatus.OK,
            provider_name=self.name,
            backend=self.backend,
            details={"default_model": self._default_model},
        )

    def complete(self, request: ModelRequest) -> ModelResponse:
        if not self._available:
            return self._fallback.complete(request)
        model = request.model or self._default_model
        kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": request.max_tokens,
            "messages": [{"role": "user", "content": request.prompt}],
        }
        if request.system:
            kwargs["system"] = request.system
        response = self._client.messages.create(**kwargs)
        content = response.content[0].text if response.content else ""
        return ModelResponse(
            content=content,
            model=model,
            provider="claude",
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )


# ── Optional: OpenRouterProvider ────────────────────────────────────────────

class OpenRouterProvider(ModelRouterProvider):
    """ModelRouterProvider backed by OpenRouter (any model).

    Requires: pip install openai
    Env vars: OPENROUTER_API_KEY

    Default model: meta-llama/llama-3.1-8b-instruct:free
    """

    DEFAULT_MODEL = "meta-llama/llama-3.1-8b-instruct:free"
    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: str = DEFAULT_MODEL,
        fallback: Optional[ModelRouterProvider] = None,
    ) -> None:
        # None = read from env; "" = explicitly no key (test/mock mode)
        self._api_key = os.environ.get("OPENROUTER_API_KEY", "") if api_key is None else api_key
        self._default_model = default_model
        self._fallback = fallback or MockModelProvider()
        self._client: Any = None
        self._available = False
        self._init()

    def _init(self) -> None:
        if not self._api_key:
            return
        try:
            from openai import OpenAI  # type: ignore
            self._client = OpenAI(api_key=self._api_key, base_url=self.BASE_URL)
            self._available = True
        except ImportError:
            self._available = False

    @property
    def backend(self) -> str:
        return f"openrouter({self._default_model})" if self._available else "mock(openrouter_unavailable)"

    def health_check(self) -> ProviderHealth:
        if not self._available:
            return ProviderHealth(
                status=ProviderStatus.DEGRADED,
                provider_name=self.name,
                backend=self.backend,
                details={"reason": "openai not installed or OPENROUTER_API_KEY not set", "fallback": "mock"},
            )
        return ProviderHealth(
            status=ProviderStatus.OK,
            provider_name=self.name,
            backend=self.backend,
        )

    def complete(self, request: ModelRequest) -> ModelResponse:
        if not self._available:
            return self._fallback.complete(request)
        model = request.model or self._default_model
        messages = []
        if request.system:
            messages.append({"role": "system", "content": request.system})
        messages.append({"role": "user", "content": request.prompt})
        response = self._client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )
        content = response.choices[0].message.content or ""
        return ModelResponse(
            content=content,
            model=model,
            provider="openrouter",
            input_tokens=response.usage.prompt_tokens if response.usage else 0,
            output_tokens=response.usage.completion_tokens if response.usage else 0,
        )
