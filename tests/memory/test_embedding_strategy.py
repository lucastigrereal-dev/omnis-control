"""Tests for embedding strategy + mock providers."""
from __future__ import annotations

import pytest

from src.memory.embeddings import (
    EmbeddingStrategy,
    MockHashEmbeddingProvider,
    MockConstantEmbeddingProvider,
    MockKeywordEmbeddingProvider,
    cosine_similarity,
)


class TestMockHashEmbeddingProvider:
    def test_same_input_same_output(self):
        p = MockHashEmbeddingProvider(dimensions=128)
        a = p.embed("hello world")
        b = p.embed("hello world")
        assert a == b

    def test_different_input_different_output(self):
        p = MockHashEmbeddingProvider(dimensions=128)
        a = p.embed("hello")
        b = p.embed("world")
        assert a != b

    def test_correct_dimensions(self):
        for dims in [64, 128, 384, 768]:
            p = MockHashEmbeddingProvider(dimensions=dims)
            assert len(p.embed("test")) == dims

    def test_embed_batch(self):
        p = MockHashEmbeddingProvider(dimensions=64)
        results = p.embed_batch(["a", "b", "c"])
        assert len(results) == 3
        assert all(len(r) == 64 for r in results)

    def test_values_in_range(self):
        p = MockHashEmbeddingProvider(dimensions=256)
        vec = p.embed("test")
        for v in vec:
            assert -1.0 <= v <= 1.0


class TestMockConstantEmbeddingProvider:
    def test_all_constant(self):
        p = MockConstantEmbeddingProvider(dimensions=128, constant=0.5)
        vec = p.embed("anything")
        assert vec == [0.5] * 128

    def test_embed_batch(self):
        p = MockConstantEmbeddingProvider(dimensions=32)
        results = p.embed_batch(["x", "y"])
        assert results[0] == [0.01] * 32
        assert results[1] == [0.01] * 32


class TestMockKeywordEmbeddingProvider:
    def test_keyword_boosts_dimension(self):
        p = MockKeywordEmbeddingProvider(dimensions=64, keywords={"turismo": 10})
        base = MockHashEmbeddingProvider(dimensions=64).embed("nada a ver")
        boosted = p.embed("turismo em natal")
        assert boosted[10] >= base[10]  # keyword found — boosted dimension

    def test_no_keyword_no_boost(self):
        p = MockKeywordEmbeddingProvider(dimensions=64, keywords={"turismo": 10})
        ref = MockHashEmbeddingProvider(dimensions=64).embed("sem match")
        result = p.embed("sem match")
        assert result == ref


class TestCosineSimilarity:
    def test_identical(self):
        vec = [0.5, 0.3, 0.1]
        assert cosine_similarity(vec, vec) == pytest.approx(1.0)

    def test_orthogonal(self):
        assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)

    def test_opposite(self):
        assert cosine_similarity([1.0, 0.0], [-1.0, 0.0]) == pytest.approx(-1.0)

    def test_dimension_mismatch(self):
        with pytest.raises(ValueError):
            cosine_similarity([1.0], [1.0, 2.0])

    def test_zero_vector(self):
        assert cosine_similarity([0.0, 0.0], [1.0, 0.0]) == 0.0


class TestEmbeddingStrategy:
    def test_default(self):
        s = EmbeddingStrategy.mock_default()
        assert s.provider == "mock_hash"
        assert s.dimensions == 384
        assert s.dry_run is True
        assert s.normalize is True
