"""MemoryProvider — unified memory abstraction for OMNIS.

Backends:
1. LocalMemoryProvider  — in-memory dict (built-in, zero deps)
2. AkashaProvider       — PostgreSQL + pgvector (optional)
3. Mem0Provider         — mem0 cloud (optional)
4. HybridMemoryProvider — chain multiple backends with fallback

OMNIS core only imports MemoryProvider and MemoryResult.
"""
from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

from src.providers.base import Provider, ProviderHealth, ProviderStatus


@dataclass
class MemoryResult:
    """A single memory retrieval result."""
    id: str
    content: str
    score: float = 1.0
    source: str = "unknown"
    metadata: dict[str, Any] = field(default_factory=dict)


class MemoryProvider(Provider):
    """Abstract memory provider. Use registry.get('memory') to get instance."""

    @property
    def name(self) -> str:
        return "memory"

    @abstractmethod
    def retrieve(self, query: str, *, k: int = 5, filter: Optional[dict] = None) -> list[MemoryResult]:
        """Semantic retrieval. Returns up to k results ordered by relevance."""

    @abstractmethod
    def write(self, content: str, *, id: Optional[str] = None, metadata: Optional[dict] = None) -> str:
        """Write a memory entry. Returns the assigned id."""

    @abstractmethod
    def delete(self, id: str) -> bool:
        """Delete a memory entry. Returns True if deleted."""

    def search(self, query: str, k: int = 5) -> list[MemoryResult]:
        """Alias for retrieve for compatibility."""
        return self.retrieve(query, k=k)


# ── Built-in fallback: LocalMemoryProvider ─────────────────────────────────

class LocalMemoryProvider(MemoryProvider):
    """In-memory store. Zero deps. Keyword-based search (not semantic).

    Useful for tests, dry-run, and environments without vector backends.
    """

    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}

    @property
    def backend(self) -> str:
        return "local_memory"

    def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            status=ProviderStatus.OK,
            provider_name=self.name,
            backend=self.backend,
            details={"entries": len(self._store)},
        )

    def retrieve(self, query: str, *, k: int = 5, filter: Optional[dict] = None) -> list[MemoryResult]:
        query_lower = query.lower()
        results = []
        for entry_id, entry in self._store.items():
            content = entry["content"]
            score = sum(1 for word in query_lower.split() if word in content.lower())
            if score > 0:
                results.append(MemoryResult(
                    id=entry_id,
                    content=content,
                    score=float(score),
                    source=self.backend,
                    metadata=entry.get("metadata", {}),
                ))
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:k]

    def write(self, content: str, *, id: Optional[str] = None, metadata: Optional[dict] = None) -> str:
        import uuid
        entry_id = id or str(uuid.uuid4())
        self._store[entry_id] = {"content": content, "metadata": metadata or {}}
        return entry_id

    def delete(self, id: str) -> bool:
        if id in self._store:
            del self._store[id]
            return True
        return False


# ── Optional: HybridMemoryProvider ─────────────────────────────────────────

class HybridMemoryProvider(MemoryProvider):
    """Chains multiple MemoryProviders. Reads from all, writes to primary.

    Example:
        HybridMemoryProvider(
            primary=AkashaProvider(...),
            fallbacks=[Mem0Provider(...), LocalMemoryProvider()]
        )
    """

    def __init__(
        self,
        primary: MemoryProvider,
        fallbacks: Optional[list[MemoryProvider]] = None,
    ) -> None:
        self._primary = primary
        self._fallbacks = fallbacks or []

    @property
    def backend(self) -> str:
        return f"hybrid({self._primary.backend}+{len(self._fallbacks)})"

    def health_check(self) -> ProviderHealth:
        primary_health = self._primary.health_check()
        return ProviderHealth(
            status=primary_health.status,
            provider_name=self.name,
            backend=self.backend,
            details={
                "primary": primary_health.details,
                "fallbacks": [f.backend for f in self._fallbacks],
            },
        )

    def retrieve(self, query: str, *, k: int = 5, filter: Optional[dict] = None) -> list[MemoryResult]:
        all_results: list[MemoryResult] = []
        for provider in [self._primary] + self._fallbacks:
            try:
                results = provider.retrieve(query, k=k, filter=filter)
                for r in results:
                    r.source = provider.backend
                all_results.extend(results)
            except Exception:
                continue
        # deduplicate by id, keep highest score
        seen: dict[str, MemoryResult] = {}
        for r in all_results:
            if r.id not in seen or r.score > seen[r.id].score:
                seen[r.id] = r
        return sorted(seen.values(), key=lambda r: r.score, reverse=True)[:k]

    def write(self, content: str, *, id: Optional[str] = None, metadata: Optional[dict] = None) -> str:
        return self._primary.write(content, id=id, metadata=metadata)

    def delete(self, id: str) -> bool:
        return self._primary.delete(id)
