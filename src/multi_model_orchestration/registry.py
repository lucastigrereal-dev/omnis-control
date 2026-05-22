"""P25 ModelRegistry — register, find, enable/disable models."""
from __future__ import annotations

from typing import Optional

from src.multi_model_orchestration.errors import InvalidModelConfigError
from src.multi_model_orchestration.models import (
    COMPLEXITY_CRITICAL,
    COMPLEXITY_HIGH,
    COMPLEXITY_LOW,
    COMPLEXITY_MEDIUM,
    PROVIDER_ANTHROPIC,
    PROVIDER_GROQ,
    PROVIDER_MOCK,
    PROVIDER_OPENAI,
    PROVIDER_OLLAMA,
    CAPABILITY_CODE,
    CAPABILITY_ANALYSIS,
    CAPABILITY_PLANNING,
    CAPABILITY_TEXT,
    CAPABILITY_CLASSIFICATION,
    CAPABILITY_SUMMARIZATION,
    ModelConfig,
    TaskClass,
)


class ModelRegistry:
    """Registry of available models with search and lifecycle management."""

    def __init__(self, dry_run: bool = True) -> None:
        self.dry_run = dry_run
        self._models: dict[str, ModelConfig] = {}

    # ── CRUD ────────────────────────────────────────────────────────────────

    def register(self, model: ModelConfig) -> None:
        """Register a model config."""
        self._models[model.model_id] = model

    def unregister(self, model_id: str) -> bool:
        """Remove a model from the registry. Returns True if it existed."""
        if model_id in self._models:
            del self._models[model_id]
            return True
        return False

    def get(self, model_id: str) -> Optional[ModelConfig]:
        """Get a model by ID, or None."""
        return self._models.get(model_id)

    def find_by_name(self, name: str) -> Optional[ModelConfig]:
        """Find a model by exact name match."""
        for m in self._models.values():
            if m.name == name:
                return m
        return None

    # ── Search / Filter ─────────────────────────────────────────────────────

    def find(self, capabilities: Optional[list[str]] = None, max_cost: Optional[float] = None) -> list[ModelConfig]:
        """Find models matching criteria. Enabled only."""
        results: list[ModelConfig] = []
        for m in self._models.values():
            if not m.enabled:
                continue
            if capabilities and not all(c in m.capabilities for c in capabilities):
                continue
            if max_cost is not None and m.cost_per_1k_tokens > max_cost:
                continue
            results.append(m)
        return sorted(results, key=lambda m: m.priority)

    def find_for_task(self, task: TaskClass) -> list[ModelConfig]:
        """Find models capable of handling a given task."""
        candidates = self.find(capabilities=task.min_capabilities, max_cost=task.max_cost_usd)
        # Sort: cheapest first for low complexity, most capable first for critical
        if task.complexity in (COMPLEXITY_CRITICAL, COMPLEXITY_HIGH):
            candidates.sort(key=lambda m: (-len(m.capabilities), m.priority, m.cost_per_1k_tokens))
        else:
            candidates.sort(key=lambda m: (m.cost_per_1k_tokens, m.priority))
        return candidates

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def enable(self, model_id: str) -> None:
        """Enable a model."""
        model = self._models.get(model_id)
        if model is None:
            raise InvalidModelConfigError(f"Model not found: {model_id!r}")
        model.enabled = True

    def disable(self, model_id: str) -> None:
        """Disable a model."""
        model = self._models.get(model_id)
        if model is None:
            raise InvalidModelConfigError(f"Model not found: {model_id!r}")
        model.enabled = False

    # ── List ─────────────────────────────────────────────────────────────────

    def list_all(self) -> list[ModelConfig]:
        """List all models (enabled and disabled)."""
        return sorted(self._models.values(), key=lambda m: m.priority)

    def list_enabled(self) -> list[ModelConfig]:
        """List enabled models only."""
        return [m for m in self._models.values() if m.enabled]

    def list_by_provider(self, provider: str) -> list[ModelConfig]:
        """List models for a specific provider."""
        return [m for m in self._models.values() if m.provider == provider]

    def list_by_capability(self, capability: str) -> list[ModelConfig]:
        """List models that have a specific capability."""
        return [m for m in self._models.values() if capability in m.capabilities]

    # ── Info ─────────────────────────────────────────────────────────────────

    @property
    def count(self) -> int:
        return len(self._models)

    @property
    def enabled_count(self) -> int:
        return len(self.list_enabled())

    @property
    def providers(self) -> list[str]:
        return sorted({m.provider for m in self._models.values()})

    # ── Default seed ─────────────────────────────────────────────────────────

    def seed_defaults(self) -> None:
        """Seed registry with default model configurations and register adapters."""
        from src.multi_model_orchestration.adapters.mock_adapter import register as register_mock
        from src.multi_model_orchestration.adapters.openai_adapter import register as register_openai
        from src.multi_model_orchestration.adapters.anthropic_adapter import register as register_anthropic
        from src.multi_model_orchestration.adapters.ollama_adapter import register as register_ollama

        register_mock()
        register_openai()
        register_anthropic()
        register_ollama()

        defaults = [
            # ── Anthropic ──────────────────────────────────────────────────
            ModelConfig.new("claude-opus-4-7", PROVIDER_ANTHROPIC,
                            capabilities=[CAPABILITY_TEXT, CAPABILITY_CODE, CAPABILITY_ANALYSIS, CAPABILITY_PLANNING],
                            cost_per_1k_tokens=0.015, avg_latency_ms=3000, max_tokens=200000, priority=2),
            ModelConfig.new("claude-sonnet-4-6", PROVIDER_ANTHROPIC,
                            capabilities=[CAPABILITY_TEXT, CAPABILITY_CODE, CAPABILITY_ANALYSIS],
                            cost_per_1k_tokens=0.003, avg_latency_ms=1500, max_tokens=200000, priority=1),
            ModelConfig.new("claude-haiku-4-5", PROVIDER_ANTHROPIC,
                            capabilities=[CAPABILITY_TEXT, CAPABILITY_CLASSIFICATION, CAPABILITY_SUMMARIZATION],
                            cost_per_1k_tokens=0.001, avg_latency_ms=500, max_tokens=200000, priority=1),
            # ── OpenAI ─────────────────────────────────────────────────────
            ModelConfig.new("gpt-4o", PROVIDER_OPENAI,
                            capabilities=[CAPABILITY_TEXT, CAPABILITY_CODE, CAPABILITY_ANALYSIS, CAPABILITY_PLANNING],
                            cost_per_1k_tokens=0.005, avg_latency_ms=1200, max_tokens=128000, priority=2),
            ModelConfig.new("gpt-4.1-mini", PROVIDER_OPENAI,
                            capabilities=[CAPABILITY_TEXT, CAPABILITY_CLASSIFICATION, CAPABILITY_SUMMARIZATION],
                            cost_per_1k_tokens=0.0006, avg_latency_ms=400, max_tokens=128000, priority=1),
            # ── Ollama (local + cloud) ─────────────────────────────────────
            ModelConfig.new("qwen2.5-coder:7b", PROVIDER_OLLAMA,
                            capabilities=[CAPABILITY_TEXT, CAPABILITY_CODE, CAPABILITY_ANALYSIS, CAPABILITY_CLASSIFICATION],
                            cost_per_1k_tokens=0.0, avg_latency_ms=800, max_tokens=4096, priority=10),
            ModelConfig.new("llama3.2:3b", PROVIDER_OLLAMA,
                            capabilities=[CAPABILITY_TEXT, CAPABILITY_CLASSIFICATION, CAPABILITY_SUMMARIZATION],
                            cost_per_1k_tokens=0.0, avg_latency_ms=400, max_tokens=4096, priority=10),
            ModelConfig.new("llama3.1:8b", PROVIDER_OLLAMA,
                            capabilities=[CAPABILITY_TEXT, CAPABILITY_CODE, CAPABILITY_ANALYSIS],
                            cost_per_1k_tokens=0.0, avg_latency_ms=1000, max_tokens=4096, priority=10),
            ModelConfig.new("deepseek-v4-pro:cloud", PROVIDER_OLLAMA,
                            capabilities=[CAPABILITY_TEXT, CAPABILITY_CODE, CAPABILITY_ANALYSIS, CAPABILITY_PLANNING],
                            cost_per_1k_tokens=0.0, avg_latency_ms=2000, max_tokens=8192, priority=8),
            ModelConfig.new("nomic-embed-text:latest", PROVIDER_OLLAMA,
                            capabilities=[CAPABILITY_TEXT, CAPABILITY_CLASSIFICATION],
                            cost_per_1k_tokens=0.0, avg_latency_ms=200, max_tokens=8192, priority=10),
            ModelConfig.new("qwen-coder-q5-recommended:latest", PROVIDER_OLLAMA,
                            capabilities=[CAPABILITY_TEXT, CAPABILITY_CODE, CAPABILITY_ANALYSIS],
                            cost_per_1k_tokens=0.0, avg_latency_ms=600, max_tokens=4096, priority=10),
            # ── Groq ───────────────────────────────────────────────────────
            ModelConfig.new("groq-llama-3-70b", PROVIDER_GROQ,
                            capabilities=[CAPABILITY_TEXT, CAPABILITY_CLASSIFICATION],
                            cost_per_1k_tokens=0.0005, avg_latency_ms=200, max_tokens=8192, priority=3),
            # ── Mock (fallback) ────────────────────────────────────────────
            ModelConfig.new("mock-model", PROVIDER_MOCK,
                            capabilities=[CAPABILITY_TEXT, CAPABILITY_CODE, CAPABILITY_ANALYSIS, CAPABILITY_PLANNING, CAPABILITY_CLASSIFICATION],
                            cost_per_1k_tokens=0.0, avg_latency_ms=1, max_tokens=4096, priority=99),
        ]
        for model in defaults:
            self.register(model)
