"""ProviderRegistry — central injection point for all OMNIS providers.

Usage:
    registry = ProviderRegistry.default()
    tracer = registry.get("tracing")
    with tracer.span("my_operation") as ctx:
        ...

    # Production: activates real backends when env vars present
    registry = ProviderRegistry.production()

The registry is the ONLY place where OMNIS decides which backend to use.
Business logic never imports backends directly.

Provider map:
    "tracing"   → TracingProvider   (LocalJSONL | Langfuse | OTel)
    "memory"    → MemoryProvider    (Local | Akasha | Mem0 | Hybrid | Semantic)
    "workflow"  → WorkflowProvider  (Sequential | LangGraph)
    "mcp"       → MCPProvider       (LocalRegistry | FastMCP)
    "runtime"   → RuntimeProvider   (Mock | Subprocess)
    "embedding" → EmbeddingProvider (TFIDF | SentenceTransformers)
    "model"     → ModelRouterProvider (Mock | Claude | OpenRouter)
    "guardrail" → GuardrailProvider (RuleBased | NeMo)
"""
from __future__ import annotations

import os
from typing import Type, TypeVar

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
        """Build default registry — zero external dependencies.

        All providers use built-in fallback backends.
        Safe to use in tests, CI, and offline environments.
        """
        from src.providers.tracing import LocalJSONLProvider
        from src.providers.memory import LocalMemoryProvider
        from src.providers.workflow import SequentialWorkflowProvider
        from src.providers.mcp import LocalToolRegistryProvider
        from src.providers.runtime import MockRuntimeProvider
        from src.providers.embedding import TFIDFEmbeddingProvider
        from src.providers.model_router import MockModelProvider
        from src.providers.guardrail import RuleBasedGuardrailProvider

        return (
            cls()
            .register(LocalJSONLProvider())
            .register(LocalMemoryProvider())
            .register(SequentialWorkflowProvider())
            .register(LocalToolRegistryProvider())
            .register(MockRuntimeProvider())
            .register(TFIDFEmbeddingProvider())
            .register(MockModelProvider())
            .register(RuleBasedGuardrailProvider())
        )

    @classmethod
    def production(cls) -> "ProviderRegistry":
        """Build production registry — activates real backends via env vars.

        Environment variables (all optional, all fall back to local):
        - LANGFUSE_PUBLIC_KEY + LANGFUSE_SECRET_KEY → LangfuseProvider
        - AKASHA_DB_URL                             → AkashaProvider
        - MEM0_API_KEY                              → Mem0Provider + HybridMemoryProvider
        - ANTHROPIC_API_KEY                         → ClaudeProvider
        - OPENROUTER_API_KEY                        → OpenRouterProvider
        - LANGGRAPH_ENABLED=1                       → LangGraphProvider
        - FASTMCP_ENABLED=1                         → FastMCPProvider (omnis tools)
        """
        from src.providers.tracing import LocalJSONLProvider, LangfuseProvider
        from src.providers.memory import LocalMemoryProvider, HybridMemoryProvider
        from src.providers.workflow import SequentialWorkflowProvider
        from src.providers.mcp import LocalToolRegistryProvider
        from src.providers.runtime import SubprocessRuntimeProvider
        from src.providers.embedding import TFIDFEmbeddingProvider, SentenceTransformerProvider
        from src.providers.model_router import MockModelProvider, ClaudeProvider, OpenRouterProvider
        from src.providers.guardrail import RuleBasedGuardrailProvider
        from src.providers.akasha import AkashaProvider
        from src.providers.mem0_provider import Mem0Provider
        from src.providers.langgraph_provider import LangGraphProvider
        from src.providers.fastmcp_provider import build_omnis_mcp_server

        registry = cls()

        # ── Tracing ──
        if os.environ.get("LANGFUSE_PUBLIC_KEY"):
            registry.register(LangfuseProvider(fallback=LocalJSONLProvider()))
        else:
            registry.register(LocalJSONLProvider())

        # ── Embedding ──
        # Use SentenceTransformers only when explicitly requested (avoids HF download on startup)
        st_model = os.environ.get("SENTENCE_TRANSFORMERS_MODEL")
        if st_model:
            registry.register(SentenceTransformerProvider(model_name=st_model, fallback=TFIDFEmbeddingProvider()))
        else:
            registry.register(TFIDFEmbeddingProvider())

        # ── Memory ──
        local_mem = LocalMemoryProvider()
        akasha = AkashaProvider(db_url=os.environ.get("AKASHA_DB_URL", ""))
        if os.environ.get("MEM0_API_KEY"):
            mem0 = Mem0Provider(api_key=os.environ.get("MEM0_API_KEY"))
            registry.register(HybridMemoryProvider(primary=akasha, fallbacks=[mem0, local_mem]))
        elif os.environ.get("AKASHA_DB_URL"):
            registry.register(HybridMemoryProvider(primary=akasha, fallbacks=[local_mem]))
        else:
            registry.register(local_mem)

        # ── Workflow ──
        if os.environ.get("LANGGRAPH_ENABLED"):
            registry.register(LangGraphProvider(fallback=SequentialWorkflowProvider()))
        else:
            registry.register(SequentialWorkflowProvider())

        # ── MCP ──
        if os.environ.get("FASTMCP_ENABLED"):
            registry.register(build_omnis_mcp_server())
        else:
            registry.register(LocalToolRegistryProvider())

        # ── Runtime ──
        registry.register(SubprocessRuntimeProvider())

        # ── Model Router ──
        if os.environ.get("ANTHROPIC_API_KEY"):
            registry.register(ClaudeProvider(
                api_key=os.environ.get("ANTHROPIC_API_KEY"),
                fallback=MockModelProvider(),
            ))
        elif os.environ.get("OPENROUTER_API_KEY"):
            registry.register(OpenRouterProvider(
                api_key=os.environ.get("OPENROUTER_API_KEY"),
                fallback=MockModelProvider(),
            ))
        else:
            registry.register(MockModelProvider())

        # ── Guardrail ──
        registry.register(RuleBasedGuardrailProvider())

        return registry
