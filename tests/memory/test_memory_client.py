"""Testes para OmnisMemoryClient e qdrant_collections — graceful degradation sem Qdrant."""
from __future__ import annotations
import pytest

from src.memory.memory_client import OmnisMemoryClient
from src.memory.qdrant_collections import COLLECTIONS, setup_collections


# ---------------------------------------------------------------------------
# Graceful degradation (Qdrant offline)
# ---------------------------------------------------------------------------

class TestGracefulDegradation:
    """Todos os testes passam sem Qdrant rodando."""

    def test_client_graceful_sem_qdrant(self):
        """OmnisMemoryClient com Qdrant off → available=False, sem exceção."""
        # porta 19999 nunca vai estar aberta
        client = OmnisMemoryClient(host="localhost", port=19999)
        assert client.available is False

    def test_remember_sem_qdrant_retorna_none(self):
        """remember() sem Qdrant → None."""
        client = OmnisMemoryClient(host="localhost", port=19999)
        result = client.remember("texto de teste", "marketing_library", {"tipo": "hook"})
        assert result is None

    def test_search_sem_qdrant_retorna_vazio(self):
        """search() sem Qdrant → lista vazia."""
        client = OmnisMemoryClient(host="localhost", port=19999)
        results = client.search("viagem", "marketing_library")
        assert results == []

    def test_setup_collections_sem_qdrant(self):
        """setup_collections() sem Qdrant → dict com 'unavailable' para cada collection."""
        result = setup_collections(host="localhost", port=19999)
        assert isinstance(result, dict)
        for name in COLLECTIONS:
            assert result[name] == "unavailable", (
                f"Collection '{name}' deveria ser 'unavailable', got '{result[name]}'"
            )

    def test_search_marketing_library_sem_qdrant(self):
        """search_marketing_library() sem Qdrant → lista vazia."""
        client = OmnisMemoryClient(host="localhost", port=19999)
        results = client.search_marketing_library("viagem")
        assert results == []

    def test_save_mission_context_sem_qdrant(self):
        """save_mission_context() sem Qdrant → None, sem exceção."""
        client = OmnisMemoryClient(host="localhost", port=19999)
        result = client.save_mission_context(
            mission_id="m-001",
            result={"goal": "publicar reel", "status": "done", "sector": "midia"},
        )
        assert result is None


# ---------------------------------------------------------------------------
# Collections definitions
# ---------------------------------------------------------------------------

class TestCollectionsDefinicoes:
    """Valida a estrutura de COLLECTIONS sem precisar de Qdrant."""

    def test_collections_definidas(self):
        """COLLECTIONS tem exatamente 5 entradas."""
        assert len(COLLECTIONS) == 5

    def test_collections_tem_chaves_esperadas(self):
        """Cada collection tem 'size', 'description' e 'payload_fields'."""
        required_keys = {"size", "description", "payload_fields"}
        for name, config in COLLECTIONS.items():
            assert required_keys.issubset(config.keys()), (
                f"Collection '{name}' missing keys: {required_keys - set(config.keys())}"
            )

    def test_collections_size_1536(self):
        """Todas as collections usam size=1536."""
        for name, config in COLLECTIONS.items():
            assert config["size"] == 1536, f"Collection '{name}' size != 1536"

    def test_colecoes_esperadas_presentes(self):
        """Verifica que as 5 collections esperadas estão presentes."""
        expected = {
            "marketing_library",
            "mission_memory",
            "aurora_conversations",
            "obsidian_notes",
            "project_context",
        }
        assert set(COLLECTIONS.keys()) == expected


# ---------------------------------------------------------------------------
# Embed stub
# ---------------------------------------------------------------------------

class TestEmbedStub:
    """Valida o stub de embedding."""

    def test_embed_stub_tamanho(self):
        """embed('texto') retorna lista de 1536 floats."""
        client = OmnisMemoryClient(host="localhost", port=19999)
        vec = client.embed("qualquer texto aqui")
        assert isinstance(vec, list)
        assert len(vec) == 1536

    def test_embed_stub_valores_zero(self):
        """Stub retorna zeros (placeholder até embedding real)."""
        client = OmnisMemoryClient(host="localhost", port=19999)
        vec = client.embed("teste")
        assert all(v == 0.0 for v in vec)

    def test_embed_texto_vazio(self):
        """embed('') não lança exceção."""
        client = OmnisMemoryClient(host="localhost", port=19999)
        vec = client.embed("")
        assert len(vec) == 1536
