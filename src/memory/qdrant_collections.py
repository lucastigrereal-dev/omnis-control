"""Definição das collections Qdrant do OMNIS."""
from __future__ import annotations
from dataclasses import dataclass

COLLECTIONS = {
    "marketing_library": {
        "size": 1536,
        "description": "Hooks, CTAs, cases, aprendizados de marketing",
        "payload_fields": ["tipo", "pagina", "tags", "taxa_engajamento"],
    },
    "mission_memory": {
        "size": 1536,
        "description": "Histórico de missões — contexto entre sessões",
        "payload_fields": ["mission_id", "sector", "squad", "status"],
    },
    "aurora_conversations": {
        "size": 1536,
        "description": "Histórico de conversas com Aurora",
        "payload_fields": ["timestamp", "user", "command"],
    },
    "obsidian_notes": {
        "size": 1536,
        "description": "Notas Obsidian indexadas",
        "payload_fields": ["path", "tags", "modified"],
    },
    "project_context": {
        "size": 1536,
        "description": "Contexto de projetos: KRATOS, Casa Segura, etc.",
        "payload_fields": ["project", "type", "relevance"],
    },
}


def setup_collections(host: str = "localhost", port: int = 6333) -> dict:
    """Cria as collections no Qdrant. Retorna status por collection.

    Se Qdrant não estiver rodando, retorna status 'unavailable' para cada
    collection (graceful degradation).
    """
    results = {}
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams

        client = QdrantClient(host=host, port=port, timeout=3)
        for name, config in COLLECTIONS.items():
            try:
                client.recreate_collection(
                    collection_name=name,
                    vectors_config=VectorParams(
                        size=config["size"], distance=Distance.COSINE
                    ),
                )
                results[name] = "created"
            except Exception as e:
                results[name] = f"error: {e}"
    except Exception:
        for name in COLLECTIONS:
            results[name] = "unavailable"
    return results
