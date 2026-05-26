"""Testes — AkashaConnector (WAVE 7).

Cobre: is_available, status, search_chunks (FTS + ILIKE), read_memories,
       write_memory, graceful sem credencial, erros de conexão, anti-teatro.
Todos os testes mockam psycopg2.connect (sem conexão real ao banco).
"""
from __future__ import annotations

import json
from unittest.mock import patch, MagicMock, call

import pytest

from src.akasha_connector.connector import (
    AkashaConnector,
    AkashaStatus,
    ChunkResult,
    MemoryRecord,
)


# ------------------------------------------------------------------
# Helpers de mock
# ------------------------------------------------------------------

def _make_conn(rows_map: dict = None):
    """Cria mock de psycopg2.connect com cur.fetchall() configurável."""
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value = cur

    if rows_map:
        # cur.fetchall() retorna a lista correspondente ao SQL que foi executado
        cur.fetchall.side_effect = lambda: rows_map.get(
            getattr(cur, "_last_sql", ""), []
        )

    return conn, cur


def _patch_connect(conn):
    """Patch psycopg2.connect para retornar mock de conn."""
    return patch("psycopg2.connect", return_value=conn)


def _chunk_row(text="Texto chunk", domain="juridico", fname="doc.pdf",
               ftype="pdf", section="Intro", rank=0.8):
    return (text, domain, fname, ftype, section, rank)


def _memory_row(mid="omnis_abc", content="Memoria OMNIS", meta=None,
                created="2026-05-01 12:00:00", updated="2026-05-01 12:00:00"):
    return (mid, content, meta or {"tipo": "arquitetura"}, created, updated)


# ------------------------------------------------------------------
# is_available
# ------------------------------------------------------------------

class TestIsAvailable:
    def test_sem_url_false(self):
        ak = AkashaConnector(db_url="")
        assert ak.is_available() is False

    def test_com_url_true(self):
        ak = AkashaConnector(db_url="postgresql://akasha:pw@localhost/akasha")
        assert ak.is_available() is True

    def test_sem_env_false(self, monkeypatch):
        monkeypatch.delenv("AKASHA_DB_URL", raising=False)
        ak = AkashaConnector()
        assert ak.is_available() is False


# ------------------------------------------------------------------
# status
# ------------------------------------------------------------------

class TestStatus:
    def test_sem_url_retorna_offline(self):
        ak = AkashaConnector(db_url="")
        st = ak.status()
        assert st.connected is False
        assert "AKASHA_DB_URL" in st.error

    def test_falha_de_conexao_retorna_offline(self):
        ak = AkashaConnector(db_url="postgresql://x:y@z/w")
        with patch("psycopg2.connect", side_effect=Exception("connection refused")):
            st = ak.status()
        assert st.connected is False
        assert st.error != ""

    def test_conectado_retorna_counts(self):
        ak = AkashaConnector(db_url="postgresql://ak:pw@localhost/akasha")
        conn = MagicMock()
        cur = MagicMock()
        conn.cursor.return_value = cur
        # Cada fetchone retorna um count diferente
        cur.fetchone.side_effect = [(22319,), (607036,), (10,), (18,), (32,)]
        with _patch_connect(conn):
            st = ak.status()
        assert st.connected is True
        assert st.documents == 22319
        assert st.chunks == 607036
        assert st.omnis_memories == 10

    def test_to_dict_estavel(self):
        ak = AkashaConnector(db_url="")
        st = ak.status()
        d = st.to_dict()
        assert "connected" in d
        assert "documents" in d
        assert "chunks" in d
        assert "omnis_memories" in d

    def test_summary_offline(self):
        st = AkashaStatus(connected=False, error="sem conexao")
        assert "OFFLINE" in st.summary()

    def test_summary_online(self):
        st = AkashaStatus(connected=True, documents=100, chunks=1000, omnis_memories=5,
                          memoria_global=2, memoria_projetos=3)
        s = st.summary()
        assert "OK" in s
        assert "100" in s


# ------------------------------------------------------------------
# search_chunks
# ------------------------------------------------------------------

class TestSearchChunks:
    def test_sem_url_retorna_vazio(self):
        ak = AkashaConnector(db_url="")
        assert ak.search_chunks("qualquer") == []

    def test_query_vazia_retorna_vazio(self):
        ak = AkashaConnector(db_url="postgresql://x:y@z/w")
        assert ak.search_chunks("") == []
        assert ak.search_chunks("   ") == []

    def test_fts_retorna_chunks(self):
        ak = AkashaConnector(db_url="postgresql://x:y@z/w")
        conn, cur = _make_conn()
        cur.fetchall.side_effect = [
            [_chunk_row("Texto legal contrato", "juridico", "contrato.pdf")],
        ]
        with _patch_connect(conn):
            results = ak.search_chunks("contrato")
        assert len(results) == 1
        assert isinstance(results[0], ChunkResult)
        assert results[0].strategy == "fts_tsvector"
        assert results[0].domain == "juridico"

    def test_ilike_fallback_quando_fts_vazio(self):
        ak = AkashaConnector(db_url="postgresql://x:y@z/w")
        conn, cur = _make_conn()
        # FTS retorna [] → ILIKE retorna 1 row
        cur.fetchall.side_effect = [
            [],  # FTS
            [("Texto ILIKE match", "cloud_code", "file.md", "md", "Sec")],  # ILIKE
        ]
        with _patch_connect(conn):
            results = ak.search_chunks("match")
        assert len(results) == 1
        assert results[0].strategy == "ilike_fallback"

    def test_falha_de_conexao_retorna_vazio(self):
        ak = AkashaConnector(db_url="postgresql://x:y@z/w")
        with patch("psycopg2.connect", side_effect=Exception("refused")):
            results = ak.search_chunks("qualquer")
        assert results == []

    def test_to_dict_chunk_result(self):
        cr = ChunkResult(
            chunk_text="Texto", domain="jur", file_name="f.pdf",
            file_type="pdf", section_title="Intro", relevance=0.9,
            strategy="fts_tsvector",
        )
        d = cr.to_dict()
        assert d["chunk_text"] == "Texto"
        assert d["domain"] == "jur"
        assert d["relevance"] == 0.9
        assert d["strategy"] == "fts_tsvector"

    def test_summary_chunk(self):
        cr = ChunkResult(
            chunk_text="Cláusula X: proibido", domain="juridico",
            file_name="contrato.pdf", file_type="pdf",
            section_title="Cláusulas", relevance=0.8,
            strategy="fts_tsvector",
        )
        s = cr.summary()
        assert "juridico" in s
        assert "contrato.pdf" in s


# ------------------------------------------------------------------
# read_memories
# ------------------------------------------------------------------

class TestReadMemories:
    def test_sem_url_retorna_vazio(self):
        ak = AkashaConnector(db_url="")
        assert ak.read_memories() == []

    def test_retorna_lista_de_memoria_records(self):
        ak = AkashaConnector(db_url="postgresql://x:y@z/w")
        conn, cur = _make_conn()
        cur.fetchall.return_value = [
            _memory_row("omnis_abc", "OMNIS LEGO ativada", {"tipo": "arquitetura"}),
            _memory_row("omnis_xyz", "Lucas opera 6 perfis", {"tipo": "contexto"}),
        ]
        with _patch_connect(conn):
            memories = ak.read_memories()
        assert len(memories) == 2
        assert isinstance(memories[0], MemoryRecord)
        assert memories[0].memory_id == "omnis_abc"
        assert memories[0].content == "OMNIS LEGO ativada"

    def test_retorna_vazio_quando_sem_dados(self):
        ak = AkashaConnector(db_url="postgresql://x:y@z/w")
        conn, cur = _make_conn()
        cur.fetchall.return_value = []
        with _patch_connect(conn):
            memories = ak.read_memories()
        assert memories == []

    def test_falha_retorna_vazio(self):
        ak = AkashaConnector(db_url="postgresql://x:y@z/w")
        with patch("psycopg2.connect", side_effect=Exception("refused")):
            memories = ak.read_memories()
        assert memories == []

    def test_to_dict_memory_record(self):
        mr = MemoryRecord("m1", "conteudo", {"k": "v"}, "2026-01-01", "2026-01-02")
        d = mr.to_dict()
        assert d["memory_id"] == "m1"
        assert d["content"] == "conteudo"
        assert d["metadata"] == {"k": "v"}

    def test_summary_memory_record(self):
        mr = MemoryRecord("omnis_test", "Memória de teste importante", {"tipo": "test"})
        s = mr.summary()
        assert "omnis_test" in s
        assert "Memória de teste" in s


# ------------------------------------------------------------------
# write_memory
# ------------------------------------------------------------------

class TestWriteMemory:
    def test_sem_url_retorna_none(self):
        ak = AkashaConnector(db_url="")
        result = ak.write_memory("conteudo")
        assert result is None

    def test_content_vazio_retorna_none(self):
        ak = AkashaConnector(db_url="postgresql://x:y@z/w")
        result = ak.write_memory("   ")
        assert result is None

    def test_grava_e_retorna_id(self):
        ak = AkashaConnector(db_url="postgresql://x:y@z/w")
        conn, cur = _make_conn()
        with _patch_connect(conn):
            mid = ak.write_memory("Nova memória OMNIS", memory_id="omnis_w7test")
        assert mid == "omnis_w7test"
        conn.commit.assert_called_once()

    def test_id_gerado_quando_omitido(self):
        ak = AkashaConnector(db_url="postgresql://x:y@z/w")
        conn, cur = _make_conn()
        with _patch_connect(conn):
            mid = ak.write_memory("Conteudo auto-id")
        assert mid is not None
        assert mid.startswith("omnis_")

    def test_falha_retorna_none_e_rollback(self):
        ak = AkashaConnector(db_url="postgresql://x:y@z/w")
        conn, cur = _make_conn()
        cur.execute.side_effect = Exception("DB error")
        with _patch_connect(conn):
            mid = ak.write_memory("Conteudo")
        assert mid is None
        conn.rollback.assert_called_once()

    def test_falha_de_conexao_retorna_none(self):
        ak = AkashaConnector(db_url="postgresql://x:y@z/w")
        with patch("psycopg2.connect", side_effect=Exception("refused")):
            mid = ak.write_memory("Conteudo")
        assert mid is None


# ------------------------------------------------------------------
# Anti-teatro
# ------------------------------------------------------------------

class TestAntiTeatro:
    def test_chunk_text_refletido_exatamente(self):
        """O chunk_text retornado deve ser exatamente o que o banco retornou."""
        TEXTO = "ANTI_TEATRO_WAVE7_AKASHA_UNIQUE_STRING"
        ak = AkashaConnector(db_url="postgresql://x:y@z/w")
        conn, cur = _make_conn()
        cur.fetchall.side_effect = [
            [_chunk_row(TEXTO, "juridico", "doc.txt")],
        ]
        with _patch_connect(conn):
            results = ak.search_chunks("ANTI_TEATRO")
        assert results[0].chunk_text == TEXTO

    def test_memory_content_preservado(self):
        CONTENT = "ANTI_TEATRO_WAVE7_MEMORY_WRITE"
        ak = AkashaConnector(db_url="postgresql://x:y@z/w")
        conn, cur = _make_conn()
        with _patch_connect(conn):
            mid = ak.write_memory(CONTENT, memory_id="w7_anti_teatro")

        # Verifica que o execute foi chamado com o conteúdo correto
        calls = cur.execute.call_args_list
        sql_calls = [str(c) for c in calls]
        assert any(CONTENT in c for c in sql_calls)

    def test_status_counts_refletem_fetchone(self):
        ak = AkashaConnector(db_url="postgresql://x:y@z/w")
        conn = MagicMock()
        cur = MagicMock()
        conn.cursor.return_value = cur
        cur.fetchone.side_effect = [(999,), (888888,), (42,), (7,), (15,)]
        with _patch_connect(conn):
            st = ak.status()
        assert st.documents == 999
        assert st.chunks == 888888
        assert st.omnis_memories == 42
