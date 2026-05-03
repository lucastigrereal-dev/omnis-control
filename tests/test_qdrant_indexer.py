"""Testes para qdrant_indexer — mock total, sem Qdrant real necessario."""
from unittest.mock import patch, MagicMock
import pytest


def test_get_status_offline():
    """Se qdrant-client ausente, retorna available=False sem crash."""
    with patch("src.memory.qdrant_indexer._get_client", return_value=None):
        from src.memory.qdrant_indexer import get_status
        result = get_status()
    assert result["available"] is False
    assert "collections" in result
    assert "collection_omnis_drafts" in result


def test_ensure_collection_offline():
    """Se cliente None, retorna False sem crash."""
    with patch("src.memory.qdrant_indexer._get_client", return_value=None):
        from src.memory.qdrant_indexer import ensure_collection
        assert ensure_collection() is False


def test_index_drafts_offline():
    """Se cliente None, retorna dict com indexed=0."""
    with patch("src.memory.qdrant_indexer._get_client", return_value=None):
        from src.memory.qdrant_indexer import index_drafts
        result = index_drafts()
    assert result["indexed"] == 0
    assert isinstance(result["errors"], list)
    assert len(result["errors"]) > 0


def test_index_drafts_missing_file(tmp_path):
    """Arquivo ausente retorna erro no dict, nao excecao."""
    with patch("src.memory.qdrant_indexer._get_client", return_value=None):
        from src.memory.qdrant_indexer import index_drafts
        result = index_drafts(str(tmp_path / "nao_existe.jsonl"))
    assert result["indexed"] == 0


def test_embed_text_fallback():
    """Fallback de embedding retorna lista de 384 floats."""
    with patch.dict("sys.modules", {"sentence_transformers": None}):
        from src.memory import qdrant_indexer
        vec = qdrant_indexer._embed_text("texto de teste")
    assert len(vec) == 384
    assert all(isinstance(v, float) for v in vec)
