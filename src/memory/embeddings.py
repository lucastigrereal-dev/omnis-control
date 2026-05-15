"""Embedding Strategy — deterministic mock providers, zero external API calls."""
from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Protocol


class EmbeddingProvider(Protocol):
    """Contract for embedding providers — returns deterministic float vectors."""

    @property
    def dimensions(self) -> int: ...

    def embed(self, text: str) -> list[float]: ...

    def embed_batch(self, texts: list[str]) -> list[list[float]]: ...


@dataclass
class EmbeddingStrategy:
    """Strategy configuration — which provider, dimensions, normalization."""

    strategy_id: str
    provider: str = "mock_hash"
    dimensions: int = 384
    normalize: bool = True
    dry_run: bool = True
    metadata: dict = field(default_factory=dict)

    @classmethod
    def mock_default(cls) -> "EmbeddingStrategy":
        import uuid

        return cls(strategy_id=f"estr_{uuid.uuid4().hex[:8]}")


class MockHashEmbeddingProvider:
    """Deterministic embedding from SHA-256 hash — zero external calls.

    Same input → same vector. Useful for dedup verification and testing.
    """

    def __init__(self, dimensions: int = 384) -> None:
        self._dimensions = dimensions

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed(self, text: str) -> list[float]:
        h = hashlib.sha256(text.encode("utf-8")).digest()
        vec = []
        for i in range(self._dimensions):
            byte_val = h[i % len(h)]
            vec.append((byte_val / 127.5) - 1.0)
        return vec

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]


class MockConstantEmbeddingProvider:
    """Returns constant vector — for tests that don't need real embeddings."""

    def __init__(self, dimensions: int = 384, constant: float = 0.01) -> None:
        self._dimensions = dimensions
        self._constant = constant

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed(self, text: str) -> list[float]:
        return [self._constant] * self._dimensions

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]


class MockKeywordEmbeddingProvider:
    """Keyword-weighted embedding — keywords in text boost specific dimensions."""

    def __init__(self, dimensions: int = 384, keywords: dict[str, int] | None = None) -> None:
        self._dimensions = dimensions
        self._keywords = keywords or {}
        self._hash_provider = MockHashEmbeddingProvider(dimensions=dimensions)

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed(self, text: str) -> list[float]:
        base = self._hash_provider.embed(text)
        text_lower = text.lower()
        for kw, dim in self._keywords.items():
            if kw in text_lower and 0 <= dim < self._dimensions:
                base[dim] += 0.5
        return base

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two vectors."""
    if len(a) != len(b):
        raise ValueError(f"Dimension mismatch: {len(a)} vs {len(b)}")
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
