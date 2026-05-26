"""AkashaConnector — Acesso ao Akasha PostgreSQL/pgvector.

Tabelas relevantes:
  document_chunks  — 607K+ chunks com FTS (tsvector) de 22K+ documentos
  omnis_memories   — memórias OMNIS (id, content, metadata, embedding)
  memoria_global   — memórias globais (conteudo, embedding)
  memoria_projetos — contexto de projetos (nome, descricao, prompt_template)

Princípios:
- Lê AKASHA_DB_URL de os.environ — nunca hardcoded
- connect_timeout=3s + statement_timeout=5000ms para não bloquear
- Toda falha → retorna [] / {} / None com log gracioso
- FTS (tsvector) primeiro, ILIKE como fallback
- Suporta leitura E escrita em omnis_memories (UPSERT por id)
- to_dict() estável para KRATOS consumir

Uso:
    from src.akasha_connector.connector import AkashaConnector
    ak = AkashaConnector()
    if ak.is_available():
        results = ak.search_chunks("hoteis natal turismo")
        memories = ak.read_memories(limit=10)
        ak.write_memory("novo contexto aprendido", memory_id="run_abc")
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

_logger = logging.getLogger("omnis.akasha.connector")

_CONNECT_TIMEOUT = 2     # segundos para conectar (budget: 5s total no executor Aurora)
_STMT_TIMEOUT_MS = 2500  # ms para cada query (2+2.5=4.5s < 5s budget)


@dataclass
class ChunkResult:
    """Chunk de documento recuperado do Akasha."""
    chunk_text: str
    domain: str
    file_name: str
    file_type: str
    section_title: str
    relevance: float          # ts_rank normalizado (0.0-1.0) ou 0.5 se ILIKE
    strategy: str             # "fts_tsvector" | "ilike_fallback"

    def to_dict(self) -> dict:
        return {
            "chunk_text": self.chunk_text,
            "domain": self.domain,
            "file_name": self.file_name,
            "file_type": self.file_type,
            "section_title": self.section_title,
            "relevance": self.relevance,
            "strategy": self.strategy,
        }

    def summary(self) -> str:
        return f"[{self.domain}/{self.file_name}] {self.chunk_text[:80]}"


@dataclass
class MemoryRecord:
    """Registro de memória OMNIS."""
    memory_id: str
    content: str
    metadata: dict = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict:
        return {
            "memory_id": self.memory_id,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def summary(self) -> str:
        meta_str = str(self.metadata)[:40] if self.metadata else ""
        return f"[{self.memory_id[:12]}] {self.content[:70]} {meta_str}"


@dataclass
class AkashaStatus:
    """Status do Akasha com contagem de rows por tabela."""
    connected: bool
    documents: int = 0
    chunks: int = 0
    omnis_memories: int = 0
    memoria_global: int = 0
    memoria_projetos: int = 0
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "connected": self.connected,
            "documents": self.documents,
            "chunks": self.chunks,
            "omnis_memories": self.omnis_memories,
            "memoria_global": self.memoria_global,
            "memoria_projetos": self.memoria_projetos,
            "error": self.error,
        }

    def summary(self) -> str:
        if not self.connected:
            return f"Akasha OFFLINE — {self.error}"
        return (
            f"Akasha OK | docs={self.documents} chunks={self.chunks} "
            f"memories={self.omnis_memories} global={self.memoria_global} "
            f"projetos={self.memoria_projetos}"
        )


class AkashaConnector:
    """Cliente para o Akasha PostgreSQL/pgvector.

    Lê AKASHA_DB_URL de os.environ. Se ausente, todos os métodos
    retornam dados vazios (graceful degradation).

    Uso:
        ak = AkashaConnector()
        if ak.is_available():
            chunks = ak.search_chunks("hoteis natal")
    """

    def __init__(self, db_url: Optional[str] = None) -> None:
        # Se db_url for None (omitido), usa env. Se "" (vazio explícito), respeita o vazio.
        self._db_url = os.environ.get("AKASHA_DB_URL", "") if db_url is None else db_url

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        """Retorna True se AKASHA_DB_URL está configurado."""
        return bool(self._db_url)

    def status(self) -> AkashaStatus:
        """Retorna status e contagem de rows. Nunca lança exceção."""
        if not self._db_url:
            return AkashaStatus(connected=False, error="AKASHA_DB_URL não configurado")

        conn = self._connect()
        if conn is None:
            return AkashaStatus(connected=False, error="falha ao conectar")

        try:
            cur = conn.cursor()
            cur.execute("SET statement_timeout = %s", (str(_STMT_TIMEOUT_MS),))

            counts: dict[str, int] = {}
            for table in ["documents", "document_chunks", "omnis_memories",
                          "memoria_global", "memoria_projetos"]:
                try:
                    cur.execute(f"SELECT COUNT(*) FROM {table}")
                    counts[table] = cur.fetchone()[0]
                except Exception:  # noqa: BLE001
                    counts[table] = -1

            return AkashaStatus(
                connected=True,
                documents=counts.get("documents", 0),
                chunks=counts.get("document_chunks", 0),
                omnis_memories=counts.get("omnis_memories", 0),
                memoria_global=counts.get("memoria_global", 0),
                memoria_projetos=counts.get("memoria_projetos", 0),
            )
        except Exception as exc:  # noqa: BLE001
            _logger.warning("akasha.status: erro — %s", exc)
            return AkashaStatus(connected=False, error=str(exc)[:80])
        finally:
            self._close(conn)

    # ------------------------------------------------------------------
    # Busca em document_chunks
    # ------------------------------------------------------------------

    def search_chunks(
        self,
        query: str,
        max_results: int = 5,
        domain_filter: Optional[str] = None,
    ) -> list[ChunkResult]:
        """Busca chunks por FTS (tsvector) com ILIKE fallback.

        Args:
            query: texto de busca
            max_results: máximo de resultados (1-50)
            domain_filter: filtra por domain (ex: "juridico", "cloud_code")

        Retorna [] se não disponível, sem resultados ou falha.
        """
        if not self._db_url or not query.strip():
            return []

        conn = self._connect()
        if conn is None:
            return []

        try:
            cur = conn.cursor()
            cur.execute("SET statement_timeout = %s", (str(_STMT_TIMEOUT_MS),))
            limit = max(1, min(max_results, 50))
            results: list[ChunkResult] = []

            # Estratégia 1: FTS tsvector
            try:
                domain_clause = "AND d.domain = %(domain)s" if domain_filter else ""
                cur.execute(
                    f"""
                    SELECT
                        dc.chunk_text,
                        d.domain,
                        d.file_name,
                        COALESCE(d.file_type, ''),
                        COALESCE(dc.section_title, ''),
                        ts_rank(dc.tsv, plainto_tsquery('simple', %(q)s)) AS rank
                    FROM document_chunks dc
                    JOIN documents d ON dc.document_id = d.id
                    WHERE dc.tsv @@ plainto_tsquery('simple', %(q)s)
                    {domain_clause}
                    ORDER BY rank DESC
                    LIMIT %(limit)s
                    """,
                    {"q": query, "domain": domain_filter, "limit": limit},
                )
                for row in cur.fetchall():
                    chunk_text, domain, file_name, file_type, section_title, rank = row
                    if chunk_text:
                        results.append(ChunkResult(
                            chunk_text=str(chunk_text),
                            domain=domain or "",
                            file_name=file_name or "",
                            file_type=file_type or "",
                            section_title=section_title or "",
                            relevance=float(rank) if rank else 0.5,
                            strategy="fts_tsvector",
                        ))
            except Exception as exc:  # noqa: BLE001
                _logger.debug("akasha.search_chunks: FTS falhou — %s", exc)

            # Estratégia 2: ILIKE fallback
            if not results:
                try:
                    domain_clause = "AND d.domain = %(domain)s" if domain_filter else ""
                    cur.execute(
                        f"""
                        SELECT
                            dc.chunk_text,
                            d.domain,
                            d.file_name,
                            COALESCE(d.file_type, ''),
                            COALESCE(dc.section_title, '')
                        FROM document_chunks dc
                        JOIN documents d ON dc.document_id = d.id
                        WHERE dc.chunk_text ILIKE %(pattern)s
                        {domain_clause}
                        LIMIT %(limit)s
                        """,
                        {"pattern": f"%{query}%", "domain": domain_filter, "limit": limit},
                    )
                    for row in cur.fetchall():
                        chunk_text, domain, file_name, file_type, section_title = row
                        if chunk_text:
                            results.append(ChunkResult(
                                chunk_text=str(chunk_text),
                                domain=domain or "",
                                file_name=file_name or "",
                                file_type=file_type or "",
                                section_title=section_title or "",
                                relevance=0.5,
                                strategy="ilike_fallback",
                            ))
                except Exception as exc:  # noqa: BLE001
                    _logger.debug("akasha.search_chunks: ILIKE falhou — %s", exc)

            _logger.debug("akasha.search_chunks: query=%r → %d resultados", query, len(results))
            return results

        except Exception as exc:  # noqa: BLE001
            _logger.warning("akasha.search_chunks: erro — %s", exc)
            return []
        finally:
            self._close(conn)

    # ------------------------------------------------------------------
    # Memórias OMNIS
    # ------------------------------------------------------------------

    def read_memories(
        self,
        limit: int = 20,
        keyword: Optional[str] = None,
    ) -> list[MemoryRecord]:
        """Lê memórias de omnis_memories (ordenadas por created_at DESC).

        Args:
            limit: máximo de registros (1-100)
            keyword: filtro ILIKE no content (opcional)
        """
        if not self._db_url:
            return []

        conn = self._connect()
        if conn is None:
            return []

        try:
            cur = conn.cursor()
            cur.execute("SET statement_timeout = %s", (str(_STMT_TIMEOUT_MS),))
            limit = max(1, min(limit, 100))

            if keyword:
                cur.execute(
                    """
                    SELECT id, content, metadata, created_at, updated_at
                    FROM omnis_memories
                    WHERE content ILIKE %(pattern)s
                    ORDER BY created_at DESC
                    LIMIT %(limit)s
                    """,
                    {"pattern": f"%{keyword}%", "limit": limit},
                )
            else:
                cur.execute(
                    """
                    SELECT id, content, metadata, created_at, updated_at
                    FROM omnis_memories
                    ORDER BY created_at DESC
                    LIMIT %(limit)s
                    """,
                    {"limit": limit},
                )

            results = []
            for row in cur.fetchall():
                mem_id, content, metadata, created_at, updated_at = row
                results.append(MemoryRecord(
                    memory_id=str(mem_id or ""),
                    content=str(content or ""),
                    metadata=dict(metadata) if isinstance(metadata, dict) else {},
                    created_at=str(created_at)[:19] if created_at else "",
                    updated_at=str(updated_at)[:19] if updated_at else "",
                ))

            _logger.debug("akasha.read_memories: %d registros", len(results))
            return results

        except Exception as exc:  # noqa: BLE001
            _logger.warning("akasha.read_memories: erro — %s", exc)
            return []
        finally:
            self._close(conn)

    def write_memory(
        self,
        content: str,
        memory_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Optional[str]:
        """Persiste uma memória em omnis_memories via UPSERT.

        Args:
            content:   texto da memória
            memory_id: ID único (gerado se omitido)
            metadata:  dict JSONB opcional

        Retorna memory_id se sucesso, None se falhar.
        """
        if not self._db_url or not content.strip():
            return None

        import uuid
        if not memory_id:
            memory_id = f"omnis_{str(uuid.uuid4())[:8]}"

        import json as _json
        meta_str = _json.dumps(metadata or {}, ensure_ascii=False)
        now = datetime.now(timezone.utc).isoformat()

        conn = self._connect()
        if conn is None:
            return None

        try:
            cur = conn.cursor()
            cur.execute("SET statement_timeout = %s", (str(_STMT_TIMEOUT_MS),))
            cur.execute(
                """
                INSERT INTO omnis_memories (id, content, metadata, created_at, updated_at)
                VALUES (%(id)s, %(content)s, %(meta)s::jsonb, %(now)s, %(now)s)
                ON CONFLICT (id) DO UPDATE
                    SET content    = EXCLUDED.content,
                        metadata   = EXCLUDED.metadata,
                        updated_at = EXCLUDED.updated_at
                """,
                {"id": memory_id, "content": content, "meta": meta_str, "now": now},
            )
            conn.commit()
            _logger.info("akasha.write_memory: id=%s gravado", memory_id)
            return memory_id

        except Exception as exc:  # noqa: BLE001
            _logger.warning("akasha.write_memory: erro — %s", exc)
            try:
                conn.rollback()
            except Exception:  # noqa: BLE001
                pass
            return None
        finally:
            self._close(conn)

    # ------------------------------------------------------------------
    # Helpers de conexão
    # ------------------------------------------------------------------

    def _connect(self):
        """Conecta ao Postgres. Retorna conn ou None."""
        try:
            import psycopg2
            return psycopg2.connect(self._db_url, connect_timeout=_CONNECT_TIMEOUT)
        except ImportError:
            _logger.warning("akasha: psycopg2 não instalado")
            return None
        except Exception as exc:  # noqa: BLE001
            _logger.warning("akasha: falha ao conectar — %s: %s", type(exc).__name__, exc)
            return None

    @staticmethod
    def _close(conn) -> None:
        if conn is not None:
            try:
                conn.close()
            except Exception:  # noqa: BLE001
                pass
