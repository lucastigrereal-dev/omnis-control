"""Memory Lookup Contract — adapter interface for Akasha/Qdrant retrieval."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class MemoryContext(BaseModel):
    """Context retrieved from memory systems."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    query: str = ""
    source: str = "unknown"  # "akasha", "qdrant", "unknown"
    chunks: list[dict] = Field(default_factory=list)
    relevance_score: float = 0.0
    retrieved_at: str = ""


class MemoryLookupAdapter(ABC):
    """Abstract interface for memory lookup adapters."""

    @abstractmethod
    def lookup(self, intent: str, limit: int = 5) -> MemoryContext: ...


class MockMemoryLookup(MemoryLookupAdapter):
    """Mock that always returns UNKNOWN — for testing and offline dev."""

    def lookup(self, intent: str, limit: int = 5) -> MemoryContext:
        return MemoryContext(
            query=intent,
            source="unknown",
            chunks=[],
            relevance_score=0.0,
        )
