"""Tests for EmbeddingProvider — TFIDFEmbeddingProvider + SentenceTransformerProvider fallback."""
import pytest
from src.providers.embedding import TFIDFEmbeddingProvider, SentenceTransformerProvider, _cosine


class TestTFIDFEmbeddingProvider:
    def test_health_ok(self):
        assert TFIDFEmbeddingProvider().health_check().ok

    def test_embed_returns_vector(self):
        p = TFIDFEmbeddingProvider()
        vec = p.embed("OMNIS gastronomia Natal")
        assert isinstance(vec, list)
        assert len(vec) == p.dimensions

    def test_embed_batch(self):
        p = TFIDFEmbeddingProvider()
        vecs = p.embed_batch(["hello", "world"])
        assert len(vecs) == 2
        assert all(len(v) == p.dimensions for v in vecs)

    def test_similarity_same_text(self):
        p = TFIDFEmbeddingProvider()
        p.fit(["OMNIS sistema operacional conteúdo", "gastronomia Natal restaurante"])
        s = p.similarity("OMNIS sistema", "OMNIS sistema")
        assert s > 0.9

    def test_similarity_different_text(self):
        p = TFIDFEmbeddingProvider()
        p.fit(["OMNIS sistema operacional", "gastronomia Natal restaurante hotel"])
        s = p.similarity("OMNIS sistema", "gastronomia Natal")
        assert s < 0.5

    def test_rank_returns_ordered(self):
        p = TFIDFEmbeddingProvider()
        p.fit(["hotel Natal praia", "restaurante gastronomia", "OMNIS sistema"])
        candidates = ["hotel Natal praia", "restaurante gastronomia", "OMNIS sistema"]
        ranked = p.rank("hotel Natal", candidates, k=3)
        assert ranked[0][0] == "hotel Natal praia"
        assert ranked[0][1] >= ranked[1][1]

    def test_fit_builds_vocab(self):
        p = TFIDFEmbeddingProvider(vocab_size=64)
        p.fit(["hello world", "foo bar"])
        assert len(p._vocab) > 0

    def test_embed_without_fit_uses_hash_fallback(self):
        p = TFIDFEmbeddingProvider()
        vec = p.embed("test content")
        assert any(v != 0 for v in vec)

    def test_backend(self):
        assert TFIDFEmbeddingProvider().backend == "tfidf"

    def test_name(self):
        assert TFIDFEmbeddingProvider().name == "embedding"

    def test_dimensions(self):
        p = TFIDFEmbeddingProvider(vocab_size=128)
        assert p.dimensions == 128


class TestSentenceTransformerProviderFallback:
    def test_health_degraded_without_lib(self):
        p = SentenceTransformerProvider(fallback=TFIDFEmbeddingProvider())
        h = p.health_check()
        # Will be degraded if sentence_transformers not installed
        assert h.status.value in ("ok", "degraded")

    def test_embed_falls_back_to_tfidf(self):
        p = SentenceTransformerProvider(fallback=TFIDFEmbeddingProvider())
        vec = p.embed("test text")
        assert isinstance(vec, list)

    def test_embed_batch_falls_back(self):
        p = SentenceTransformerProvider(fallback=TFIDFEmbeddingProvider())
        vecs = p.embed_batch(["a", "b"])
        assert len(vecs) == 2


class TestCosine:
    def test_same_vector(self):
        v = [1.0, 0.0, 0.5]
        assert _cosine(v, v) > 0.99

    def test_orthogonal(self):
        assert _cosine([1.0, 0.0], [0.0, 1.0]) == 0.0

    def test_zero_vector(self):
        assert _cosine([0.0, 0.0], [1.0, 0.0]) == 0.0
