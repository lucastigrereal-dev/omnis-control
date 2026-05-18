"""Tests for SemanticMemoryProvider."""
import pytest
from src.providers.semantic_memory import SemanticMemoryProvider
from src.providers.embedding import TFIDFEmbeddingProvider
from src.providers.memory import LocalMemoryProvider


class TestSemanticMemoryProvider:
    def _make(self) -> SemanticMemoryProvider:
        corpus = [
            "hotel Natal praia piscina litoral",
            "restaurante gastronomia culinária nordestina",
            "OMNIS sistema operacional conteúdo",
            "viagem turismo destino férias",
            "influencer Instagram seguidores publicidade",
        ]
        emb = TFIDFEmbeddingProvider()
        emb.fit(corpus)
        p = SemanticMemoryProvider(store=LocalMemoryProvider(), embedder=emb)
        for text in corpus:
            p.write(text)
        return p

    def test_health_ok(self):
        p = SemanticMemoryProvider()
        assert p.health_check().ok

    def test_retrieve_returns_relevant(self):
        p = self._make()
        results = p.retrieve("hotel praia", k=3)
        assert len(results) >= 1
        assert any("hotel" in r.content or "praia" in r.content for r in results)

    def test_retrieve_sorted_by_score(self):
        p = self._make()
        results = p.retrieve("gastronomia restaurante", k=5)
        if len(results) > 1:
            assert results[0].score >= results[-1].score

    def test_write_adds_to_index(self):
        p = SemanticMemoryProvider(embedder=TFIDFEmbeddingProvider())
        p.write("unique test content aqui")
        assert len(p._index) == 1

    def test_delete_removes_from_index(self):
        p = SemanticMemoryProvider(embedder=TFIDFEmbeddingProvider())
        id_ = p.write("to delete content")
        p.delete(id_)
        assert id_ not in p._index

    def test_retrieve_empty_falls_back_to_store(self):
        store = LocalMemoryProvider()
        store.write("keyword match content")
        p = SemanticMemoryProvider(store=store, embedder=TFIDFEmbeddingProvider())
        # index is empty, falls back to store keyword search
        results = p.retrieve("keyword match")
        assert len(results) >= 1

    def test_backend_includes_embedder_and_store(self):
        p = SemanticMemoryProvider(embedder=TFIDFEmbeddingProvider(), store=LocalMemoryProvider())
        assert "semantic" in p.backend
        assert "tfidf" in p.backend

    def test_name(self):
        assert SemanticMemoryProvider().name == "memory"
