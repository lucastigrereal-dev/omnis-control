"""Testes para src/memory/obsidian_search.py — Wave 17."""
from __future__ import annotations
import pytest


# ---------------------------------------------------------------------------
# search_obsidian — sem Qdrant
# ---------------------------------------------------------------------------

class TestSearchObsidianSemQdrant:
    def test_search_obsidian_sem_qdrant(self):
        """search_obsidian() com Qdrant off → retorna lista vazia."""
        from src.memory.obsidian_search import search_obsidian
        # porta 19999 nunca vai estar aberta
        results = search_obsidian("viagem", host="localhost", port=19999)
        assert results == []

    def test_search_obsidian_retorna_lista(self):
        """Retorno é sempre uma lista, mesmo sem Qdrant."""
        from src.memory.obsidian_search import search_obsidian
        result = search_obsidian("gastronomia natal", host="localhost", port=19999)
        assert isinstance(result, list)

    def test_search_obsidian_nao_lanca_excecao(self):
        """search_obsidian() nunca lança exceção quando Qdrant está off."""
        from src.memory.obsidian_search import search_obsidian
        try:
            search_obsidian("família", host="localhost", port=19999)
        except Exception as exc:
            pytest.fail(f"search_obsidian lançou exceção inesperada: {exc}")

    def test_search_obsidian_query_vazia(self):
        """Query vazia com Qdrant off → lista vazia."""
        from src.memory.obsidian_search import search_obsidian
        results = search_obsidian("", host="localhost", port=19999)
        assert results == []

    def test_search_obsidian_top_k_respeitado(self):
        """top_k não causa erro mesmo sem Qdrant."""
        from src.memory.obsidian_search import search_obsidian
        results = search_obsidian("viagem", top_k=10, host="localhost", port=19999)
        assert len(results) <= 10


# ---------------------------------------------------------------------------
# search_obsidian — estrutura de resultado mockado
# ---------------------------------------------------------------------------

class TestSearchObsidianResultadoMockado:
    def test_resultado_tem_chaves_esperadas(self, monkeypatch):
        """Resultado tem keys: path, tags, score, excerpt."""
        from src.memory import memory_client as mc_mod
        from src.memory.obsidian_search import search_obsidian

        mock_results = [
            {
                "payload": {
                    "path": "notas/viagem/natal.md",
                    "tags": ["viagem", "natal"],
                    "text": "Nota sobre viagem para Natal, Rio Grande do Norte.",
                },
                "score": 0.92,
            }
        ]
        monkeypatch.setattr(mc_mod.OmnisMemoryClient, "_try_connect", lambda self: None)
        monkeypatch.setattr(mc_mod.OmnisMemoryClient, "available", property(lambda self: True))
        monkeypatch.setattr(
            mc_mod.OmnisMemoryClient,
            "search",
            lambda self, q, col, top_k=5: mock_results,
        )

        results = search_obsidian("viagem natal")
        assert len(results) == 1
        item = results[0]
        assert "path" in item
        assert "tags" in item
        assert "score" in item
        assert "excerpt" in item

    def test_excerpt_truncado_em_200(self, monkeypatch):
        """excerpt é truncado em 200 chars."""
        from src.memory import memory_client as mc_mod
        from src.memory.obsidian_search import search_obsidian

        texto_longo = "x" * 500
        mock_results = [
            {
                "payload": {"path": "nota.md", "tags": [], "text": texto_longo},
                "score": 0.5,
            }
        ]
        monkeypatch.setattr(mc_mod.OmnisMemoryClient, "_try_connect", lambda self: None)
        monkeypatch.setattr(mc_mod.OmnisMemoryClient, "available", property(lambda self: True))
        monkeypatch.setattr(
            mc_mod.OmnisMemoryClient,
            "search",
            lambda self, q, col, top_k=5: mock_results,
        )

        results = search_obsidian("qualquer")
        assert len(results[0]["excerpt"]) <= 200

    def test_resultado_sem_path_no_payload(self, monkeypatch):
        """Resultado sem 'path' no payload usa string vazia."""
        from src.memory import memory_client as mc_mod
        from src.memory.obsidian_search import search_obsidian

        mock_results = [{"payload": {"tags": [], "text": "texto"}, "score": 0.3}]
        monkeypatch.setattr(mc_mod.OmnisMemoryClient, "_try_connect", lambda self: None)
        monkeypatch.setattr(mc_mod.OmnisMemoryClient, "available", property(lambda self: True))
        monkeypatch.setattr(
            mc_mod.OmnisMemoryClient,
            "search",
            lambda self, q, col, top_k=5: mock_results,
        )

        results = search_obsidian("teste")
        assert results[0]["path"] == ""


# ---------------------------------------------------------------------------
# Importação e interface pública
# ---------------------------------------------------------------------------

class TestObsidianSearchInterface:
    def test_importacao_sem_erro(self):
        """Módulo importa sem erro."""
        from src.memory import obsidian_search  # noqa: F401

    def test_search_obsidian_callable(self):
        """search_obsidian é callable."""
        from src.memory.obsidian_search import search_obsidian
        assert callable(search_obsidian)
