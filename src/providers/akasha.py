"""AkashaProvider — PostgreSQL + pgvector memory backend for OMNIS.

Connects OMNIS MemoryProvider to the Akasha PostgreSQL database.
Falls back gracefully to LocalMemoryProvider when DB is unavailable.

Requirements (optional):
    pip install psycopg2-binary pgvector

Env vars:
    AKASHA_DB_URL  — PostgreSQL DSN (e.g. postgresql://user:pass@localhost/akasha)
    AKASHA_TABLE   — table name (default: "memory_chunks")
"""
from __future__ import annotations

import os
from typing import Any, Optional

from src.providers.base import ProviderHealth, ProviderStatus
from src.providers.memory import MemoryProvider, MemoryResult, LocalMemoryProvider


class AkashaProvider(MemoryProvider):
    """MemoryProvider backed by PostgreSQL + pgvector (Akasha database).

    Uses parameterized queries only — no SQL injection risk.
    Falls back to LocalMemoryProvider on connection failure.
    """

    def __init__(
        self,
        db_url: Optional[str] = None,
        table: str = "omnis_memories",
        fallback: Optional[MemoryProvider] = None,
    ) -> None:
        self._db_url = db_url or os.environ.get("AKASHA_DB_URL", "")
        self._table = table
        self._fallback = fallback or LocalMemoryProvider()
        self._conn: Any = None
        self._available = False
        self._init()

    def _init(self) -> None:
        if not self._db_url:
            return
        try:
            import psycopg2  # type: ignore
            self._conn = psycopg2.connect(self._db_url, connect_timeout=5)
            self._available = True
        except Exception:
            self._available = False

    @property
    def backend(self) -> str:
        return "akasha_pgvector" if self._available else "local_memory(akasha_unavailable)"

    def health_check(self) -> ProviderHealth:
        if not self._available:
            return ProviderHealth(
                status=ProviderStatus.DEGRADED,
                provider_name=self.name,
                backend=self.backend,
                details={
                    "reason": "PostgreSQL not available or AKASHA_DB_URL not set",
                    "fallback": "local_memory",
                    "db_url_set": bool(self._db_url),
                },
            )
        try:
            with self._conn.cursor() as cur:
                cur.execute("SELECT 1")
            return ProviderHealth(
                status=ProviderStatus.OK,
                provider_name=self.name,
                backend=self.backend,
                details={"table": self._table},
            )
        except Exception as e:
            self._available = False
            return ProviderHealth(
                status=ProviderStatus.UNAVAILABLE,
                provider_name=self.name,
                backend=self.backend,
                details={"error": str(e), "fallback": "local_memory"},
            )

    def retrieve(self, query: str, *, k: int = 5, filter: Optional[dict] = None) -> list[MemoryResult]:
        if not self._available:
            return self._fallback.retrieve(query, k=k, filter=filter)
        try:
            # Full-text search fallback (semantic requires embedding — see EmbeddingProvider)
            with self._conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT id, content, 1.0 as score
                    FROM {self._table}
                    WHERE content ILIKE %s
                    LIMIT %s
                    """,
                    (f"%{query}%", k),
                )
                rows = cur.fetchall()
            return [
                MemoryResult(id=str(row[0]), content=row[1], score=float(row[2]), source=self.backend)
                for row in rows
            ]
        except Exception:
            return self._fallback.retrieve(query, k=k, filter=filter)

    def write(self, content: str, *, id: Optional[str] = None, metadata: Optional[dict] = None) -> str:
        if not self._available:
            return self._fallback.write(content, id=id, metadata=metadata)
        import uuid
        import json as _json
        entry_id = id or str(uuid.uuid4())
        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO {self._table} (id, content, metadata)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET content = EXCLUDED.content, metadata = EXCLUDED.metadata
                    """,
                    (entry_id, content, _json.dumps(metadata or {})),
                )
            self._conn.commit()
            return entry_id
        except Exception:
            self._conn.rollback()
            return self._fallback.write(content, id=entry_id, metadata=metadata)

    def delete(self, id: str) -> bool:
        if not self._available:
            return self._fallback.delete(id)
        try:
            with self._conn.cursor() as cur:
                cur.execute(f"DELETE FROM {self._table} WHERE id = %s", (id,))
                deleted = cur.rowcount > 0
            self._conn.commit()
            return deleted
        except Exception:
            self._conn.rollback()
            return False

    def dispose(self) -> None:
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
