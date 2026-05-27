"""Busca semântica nas notas Obsidian."""
from __future__ import annotations
from typing import Optional
from src.memory.memory_client import OmnisMemoryClient


def search_obsidian(
    query: str,
    top_k: int = 5,
    host: str = "localhost",
    port: int = 6333,
) -> list[dict]:
    """
    Busca semântica nas notas Obsidian indexadas no Qdrant.
    Retorna lista vazia se Qdrant indisponível.

    Args:
        query: texto de busca
        top_k: número máximo de resultados
        host: host do Qdrant
        port: porta do Qdrant

    Returns:
        Lista de dicts com keys: path, tags, score, excerpt
    """
    client = OmnisMemoryClient(host=host, port=port)
    results = client.search(query, "obsidian_notes", top_k=top_k)
    return [
        {
            "path": r["payload"].get("path", ""),
            "tags": r["payload"].get("tags", []),
            "score": r["score"],
            "excerpt": r["payload"].get("text", "")[:200],
        }
        for r in results
    ]
