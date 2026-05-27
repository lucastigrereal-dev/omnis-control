"""OmnisMemoryClient — interface unificada para memória vetorial."""
from __future__ import annotations
from typing import Optional
import uuid


class OmnisMemoryClient:
    """Busca semântica e persistência via Qdrant.

    Graceful degradation: se Qdrant não estiver disponível,
    operações retornam resultados vazios sem levantar exceção.
    """

    def __init__(self, host: str = "localhost", port: int = 6333):
        self._host = host
        self._port = port
        self._client = None
        self._available = False
        self._try_connect()

    def _try_connect(self) -> None:
        try:
            from qdrant_client import QdrantClient

            self._client = QdrantClient(host=self._host, port=self._port, timeout=2)
            self._client.get_collections()
            self._available = True
        except Exception:
            self._available = False

    @property
    def available(self) -> bool:
        return self._available

    def embed(self, text: str) -> list[float]:
        """Stub embedding — retorna vetor zero (substituir por embedding real quando LiteLLM/OpenAI disponível)."""
        return [0.0] * 1536

    def remember(self, text: str, collection: str, payload: dict) -> Optional[str]:
        """Salva item na memória vetorial. Retorna ID ou None se indisponível."""
        if not self._available:
            return None
        try:
            from qdrant_client.models import PointStruct

            point_id = str(uuid.uuid4())
            self._client.upsert(
                collection_name=collection,
                points=[
                    PointStruct(
                        id=point_id,
                        vector=self.embed(text),
                        payload={"text": text[:500], **payload},
                    )
                ],
            )
            return point_id
        except Exception:
            return None

    def search(self, query: str, collection: str, top_k: int = 5) -> list[dict]:
        """Busca semântica. Retorna lista vazia se Qdrant indisponível."""
        if not self._available:
            return []
        try:
            results = self._client.search(
                collection_name=collection,
                query_vector=self.embed(query),
                limit=top_k,
            )
            return [{"payload": r.payload, "score": r.score} for r in results]
        except Exception:
            return []

    def search_marketing_library(
        self, tema: str, pagina: Optional[str] = None
    ) -> list[dict]:
        return self.search(f"{tema} {pagina or ''}", "marketing_library", top_k=5)

    def save_mission_context(self, mission_id: str, result: dict) -> Optional[str]:
        text = f"{result.get('goal', '')} {result.get('status', '')}"
        return self.remember(
            text,
            "mission_memory",
            {
                "mission_id": mission_id,
                "sector": result.get("sector"),
                "status": result.get("status"),
            },
        )
