"""SemanticMemoryProvider — MemoryProvider with real vector search.

Wraps any MemoryProvider and adds embedding-based semantic retrieval.
Replaces the keyword-only search in LocalMemoryProvider for production use.

Usage:
    provider = SemanticMemoryProvider(
        store=AkashaProvider(),
        embedder=TFIDFEmbeddingProvider(),
    )
    results = provider.retrieve("hotéis Natal RN com piscina")
"""
from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from src.providers.base import Provider, ProviderHealth, ProviderStatus
from src.providers.memory import MemoryProvider, MemoryResult
from src.providers.embedding import EmbeddingProvider, TFIDFEmbeddingProvider


@dataclass
class _EmbeddedEntry:
    id: str
    content: str
    vector: list[float]
    metadata: dict[str, Any] = field(default_factory=dict)


class SemanticMemoryProvider(MemoryProvider):
    """MemoryProvider with embedding-based similarity search.

    Keeps an in-process vector index for fast cosine similarity.
    Writes are also forwarded to the underlying store for persistence.
    """

    def __init__(
        self,
        store: Optional[MemoryProvider] = None,
        embedder: Optional[EmbeddingProvider] = None,
    ) -> None:
        from src.providers.memory import LocalMemoryProvider
        self._store = store or LocalMemoryProvider()
        self._embedder = embedder or TFIDFEmbeddingProvider()
        self._index: dict[str, _EmbeddedEntry] = {}

    @property
    def backend(self) -> str:
        return f"semantic({self._embedder.backend}+{self._store.backend})"

    def health_check(self) -> ProviderHealth:
        store_health = self._store.health_check()
        embedder_health = self._embedder.health_check()
        status = store_health.status if store_health.status.value > embedder_health.status.value else embedder_health.status
        return ProviderHealth(
            status=store_health.status,
            provider_name=self.name,
            backend=self.backend,
            details={
                "store": store_health.details,
                "embedder": embedder_health.details,
                "indexed": len(self._index),
            },
        )

    def retrieve(self, query: str, *, k: int = 5, filter: Optional[dict] = None) -> list[MemoryResult]:
        if not self._index:
            return self._store.retrieve(query, k=k, filter=filter)

        q_vec = self._embedder.embed(query)
        scored = []
        for entry in self._index.values():
            score = _cosine(q_vec, entry.vector)
            if score > 0:
                scored.append(MemoryResult(
                    id=entry.id,
                    content=entry.content,
                    score=score,
                    source=self.backend,
                    metadata=entry.metadata,
                ))
        scored.sort(key=lambda r: r.score, reverse=True)
        return scored[:k]

    def write(self, content: str, *, id: Optional[str] = None, metadata: Optional[dict] = None) -> str:
        entry_id = id or str(uuid.uuid4())
        vector = self._embedder.embed(content)
        self._index[entry_id] = _EmbeddedEntry(
            id=entry_id,
            content=content,
            vector=vector,
            metadata=metadata or {},
        )
        self._store.write(content, id=entry_id, metadata=metadata)
        return entry_id

    def delete(self, id: str) -> bool:
        self._index.pop(id, None)
        return self._store.delete(id)

    def index_from_store(self, texts: list[str]) -> None:
        """Pre-embed a corpus to fit TF-IDF vocabulary. Call before retrieve."""
        if hasattr(self._embedder, "fit"):
            self._embedder.fit(texts)  # type: ignore[attr-defined]


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)
