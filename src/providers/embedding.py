"""EmbeddingProvider — vector embedding abstraction for OMNIS.

Replaces MockHashEmbeddingProvider (SHA-256 is not semantics).

Backends:
1. TFIDFEmbeddingProvider  — pure Python TF-IDF cosine similarity (zero deps)
2. SentenceTransformerProvider — real semantic embeddings (optional: sentence-transformers)
3. OpenAIEmbeddingProvider — text-embedding-3-small (optional: openai)
"""
from __future__ import annotations

import math
import re
from abc import abstractmethod
from collections import Counter
from typing import Any, Optional

from src.providers.base import Provider, ProviderHealth, ProviderStatus


class EmbeddingProvider(Provider):
    """Abstract embedding provider."""

    @property
    def name(self) -> str:
        return "embedding"

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Vector dimension size."""

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """Embed a single text. Returns float vector of length self.dimensions."""

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts. More efficient than calling embed() in a loop."""

    def similarity(self, a: str, b: str) -> float:
        """Cosine similarity between two texts. Range [0, 1]."""
        va = self.embed(a)
        vb = self.embed(b)
        return _cosine(va, vb)

    def rank(self, query: str, candidates: list[str], k: int = 5) -> list[tuple[str, float]]:
        """Rank candidates by similarity to query. Returns (text, score) pairs."""
        q = self.embed(query)
        scored = [(c, _cosine(q, self.embed(c))) for c in candidates]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\b\w+\b", text.lower())


# ── Built-in: TFIDFEmbeddingProvider ───────────────────────────────────────

class TFIDFEmbeddingProvider(EmbeddingProvider):
    """Pure Python TF-IDF bag-of-words embeddings with cosine similarity.

    Not semantic (no neural network), but vastly better than SHA-256.
    Keyword overlap gives meaningful similarity scores.
    Zero external dependencies.

    Replaces: memory/embeddings.py MockHashEmbeddingProvider
    """

    def __init__(self, vocab_size: int = 512) -> None:
        self._vocab_size = vocab_size
        self._vocab: dict[str, int] = {}
        self._idf: dict[str, float] = {}
        self._corpus: list[list[str]] = []

    @property
    def backend(self) -> str:
        return "tfidf"

    @property
    def dimensions(self) -> int:
        return self._vocab_size

    def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            status=ProviderStatus.OK,
            provider_name=self.name,
            backend=self.backend,
            details={"vocab_size": self._vocab_size, "corpus_size": len(self._corpus)},
        )

    def fit(self, texts: list[str]) -> None:
        """Build vocabulary and IDF from a corpus. Optional but improves quality."""
        self._corpus = [_tokenize(t) for t in texts]
        all_tokens: list[str] = []
        for tokens in self._corpus:
            all_tokens.extend(set(tokens))
        freq = Counter(all_tokens)
        n_docs = len(self._corpus) or 1
        top = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:self._vocab_size]
        self._vocab = {word: i for i, (word, _) in enumerate(top)}
        self._idf = {
            word: math.log((n_docs + 1) / (count + 1)) + 1
            for word, count in top
        }

    def embed(self, text: str) -> list[float]:
        tokens = _tokenize(text)
        tf = Counter(tokens)
        total = len(tokens) or 1
        vec = [0.0] * self._vocab_size
        for word, idx in self._vocab.items():
            if word in tf:
                tfidf = (tf[word] / total) * self._idf.get(word, 1.0)
                vec[idx] = tfidf
        # Fallback: if vocab empty, use character hash buckets
        if not self._vocab:
            for token in tokens:
                for char in token:
                    vec[ord(char) % self._vocab_size] += 1.0 / total
        return vec

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]


# ── Optional: SentenceTransformerProvider ──────────────────────────────────

class SentenceTransformerProvider(EmbeddingProvider):
    """Real semantic embeddings via sentence-transformers.

    Requires: pip install sentence-transformers
    Default model: all-MiniLM-L6-v2 (384 dims, 80MB, runs CPU)

    Falls back to TFIDFEmbeddingProvider if not installed.
    """

    _DEFAULT_MODEL = "all-MiniLM-L6-v2"
    _DEFAULT_DIMS = 384

    def __init__(
        self,
        model_name: str = _DEFAULT_MODEL,
        fallback: Optional[EmbeddingProvider] = None,
    ) -> None:
        self._model_name = model_name
        self._fallback = fallback or TFIDFEmbeddingProvider()
        self._model: Any = None
        self._available = False
        self._dims = self._DEFAULT_DIMS
        self._init()

    def _init(self) -> None:
        try:
            import sentence_transformers  # type: ignore  # noqa: F401
            self._available = True
            # Model is loaded lazily on first embed() call to avoid slow startup
        except ImportError:
            self._available = False

    def _ensure_model(self) -> None:
        if self._model is None and self._available:
            try:
                from sentence_transformers import SentenceTransformer  # type: ignore
                self._model = SentenceTransformer(self._model_name)
                self._dims = self._model.get_sentence_embedding_dimension()
            except Exception:
                self._available = False

    @property
    def backend(self) -> str:
        return f"sentence_transformers({self._model_name})" if self._available else "tfidf(st_unavailable)"

    @property
    def dimensions(self) -> int:
        return self._dims if self._available else self._fallback.dimensions

    def health_check(self) -> ProviderHealth:
        if not self._available:
            return ProviderHealth(
                status=ProviderStatus.DEGRADED,
                provider_name=self.name,
                backend=self.backend,
                details={"reason": "sentence-transformers not installed", "fallback": "tfidf"},
            )
        return ProviderHealth(
            status=ProviderStatus.OK,
            provider_name=self.name,
            backend=self.backend,
            details={"model": self._model_name, "dims": self._dims},
        )

    def embed(self, text: str) -> list[float]:
        if not self._available:
            return self._fallback.embed(text)
        self._ensure_model()
        if self._model is None:
            return self._fallback.embed(text)
        return self._model.encode(text).tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not self._available:
            return self._fallback.embed_batch(texts)
        self._ensure_model()
        if self._model is None:
            return self._fallback.embed_batch(texts)
        return self._model.encode(texts).tolist()
