"""Tests for MemoryProvider — LocalMemoryProvider and HybridMemoryProvider."""
import pytest
from src.providers.memory import LocalMemoryProvider, HybridMemoryProvider, MemoryResult
from src.providers.base import ProviderStatus


class TestLocalMemoryProvider:
    def test_health_ok(self):
        p = LocalMemoryProvider()
        assert p.health_check().ok

    def test_write_and_retrieve(self):
        p = LocalMemoryProvider()
        p.write("OMNIS é um sistema operacional de conteúdo")
        results = p.retrieve("sistema operacional")
        assert len(results) >= 1
        assert results[0].content == "OMNIS é um sistema operacional de conteúdo"

    def test_write_returns_id(self):
        p = LocalMemoryProvider()
        id_ = p.write("content")
        assert isinstance(id_, str)

    def test_write_with_explicit_id(self):
        p = LocalMemoryProvider()
        id_ = p.write("content", id="custom-id")
        assert id_ == "custom-id"

    def test_retrieve_sorted_by_score(self):
        p = LocalMemoryProvider()
        p.write("OMNIS tracing observabilidade Langfuse")
        p.write("OMNIS memória")
        results = p.retrieve("OMNIS tracing Langfuse")
        assert results[0].score >= results[-1].score

    def test_retrieve_empty(self):
        p = LocalMemoryProvider()
        results = p.retrieve("nothing matches")
        assert results == []

    def test_retrieve_k_limit(self):
        p = LocalMemoryProvider()
        for i in range(10):
            p.write(f"entry {i} sistema")
        results = p.retrieve("sistema", k=3)
        assert len(results) <= 3

    def test_delete_existing(self):
        p = LocalMemoryProvider()
        id_ = p.write("to delete")
        assert p.delete(id_) is True
        assert p.retrieve("to delete") == []

    def test_delete_nonexistent(self):
        p = LocalMemoryProvider()
        assert p.delete("nonexistent") is False

    def test_search_alias(self):
        p = LocalMemoryProvider()
        p.write("alias test content")
        results = p.search("alias test")
        assert len(results) >= 1

    def test_backend(self):
        assert LocalMemoryProvider().backend == "local_memory"

    def test_name(self):
        assert LocalMemoryProvider().name == "memory"


class TestHybridMemoryProvider:
    def test_health_reflects_primary(self):
        primary = LocalMemoryProvider()
        h = HybridMemoryProvider(primary=primary).health_check()
        assert h.ok

    def test_retrieve_aggregates_results(self):
        primary = LocalMemoryProvider()
        fallback = LocalMemoryProvider()
        primary.write("OMNIS primary content")
        fallback.write("OMNIS fallback content")
        hybrid = HybridMemoryProvider(primary=primary, fallbacks=[fallback])
        results = hybrid.retrieve("OMNIS content")
        assert len(results) >= 2

    def test_write_goes_to_primary(self):
        primary = LocalMemoryProvider()
        fallback = LocalMemoryProvider()
        hybrid = HybridMemoryProvider(primary=primary, fallbacks=[fallback])
        id_ = hybrid.write("primary write")
        assert id_ in primary._store
        assert id_ not in fallback._store

    def test_deduplication(self):
        primary = LocalMemoryProvider()
        primary.write("shared", id="same-id")
        fallback = LocalMemoryProvider()
        fallback.write("shared different text", id="same-id")
        hybrid = HybridMemoryProvider(primary=primary, fallbacks=[fallback])
        results = hybrid.retrieve("shared")
        ids = [r.id for r in results]
        assert ids.count("same-id") == 1

    def test_fallback_used_when_primary_empty(self):
        primary = LocalMemoryProvider()
        fallback = LocalMemoryProvider()
        fallback.write("only in fallback content here")
        hybrid = HybridMemoryProvider(primary=primary, fallbacks=[fallback])
        results = hybrid.retrieve("fallback content")
        assert len(results) >= 1

    def test_backend_name(self):
        hybrid = HybridMemoryProvider(primary=LocalMemoryProvider(), fallbacks=[LocalMemoryProvider()])
        assert "hybrid" in hybrid.backend
