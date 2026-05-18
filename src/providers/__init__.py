"""OMNIS Provider Layer — LEGO modular architecture.

Providers are abstract interfaces that decouple OMNIS core from frameworks.
Each provider has at least one built-in fallback that requires no external deps.

Available providers:
- TracingProvider  → observability (local JSONL fallback, optional Langfuse/OTel)
- MemoryProvider   → memory retrieval/write (local fallback, optional mem0/Qdrant)
- WorkflowProvider → workflow orchestration (sequential fallback, optional LangGraph)
- RuntimeProvider  → tool/skill execution (subprocess fallback, optional FastMCP)
- MCPProvider      → MCP tool discovery (local fallback, optional FastMCP)

Usage:
    from src.providers.registry import ProviderRegistry
    registry = ProviderRegistry.default()
    tracer = registry.get("tracing")
"""
from src.providers.base import Provider, ProviderHealth, ProviderStatus

__all__ = ["Provider", "ProviderHealth", "ProviderStatus"]
