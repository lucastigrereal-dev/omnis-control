"""Akasha Reader — Le memoria real do Akasha (PostgreSQL + pgvector).

DSN local (read-only, sem valor em prod):
    postgresql://akasha:akasha123@localhost:5432/akasha
"""

import os

DSN = os.getenv("AKASHA_DSN", "postgresql://akasha:akasha123@localhost:5432/akasha")


def _connect():
    """Retorna conexao ou None."""
    try:
        import psycopg2
        return psycopg2.connect(DSN, connect_timeout=3)
    except Exception:
        return None


def ping() -> bool:
    """Verifica se Akasha esta acessivel."""
    conn = _connect()
    if conn is None:
        return False
    try:
        conn.close()
        return True
    except Exception:
        return False


def get_recent_memories(limit: int = 5) -> list[dict[str, object]]:
    """Retorna as N memorias mais recentes da memoria_global.

    Colunas reais: conteudo, ingerido_em (nao content/created_at).
    """
    conn = _connect()
    if conn is None:
        return [{"error": "Akasha offline"}]

    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT conteudo, ingerido_em FROM memoria_global ORDER BY ingerido_em DESC LIMIT %s",
            (limit,),
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()

        return [
            {"content": row[0], "created_at": row[1].isoformat() if row[1] else None}
            for row in rows
        ]
    except Exception as e:
        try:
            conn.close()
        except Exception:
            pass
        return [{"error": str(e)}]


def get_project_context(project_name: str) -> str | None:
    """Busca descricao de um projeto em memoria_projetos por nome (ILIKE)."""
    conn = _connect()
    if conn is None:
        return None

    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT nome, descricao FROM memoria_projetos WHERE nome ILIKE %s LIMIT 1",
            (f"%{project_name}%",),
        )
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row:
            return f"{row[0]}: {row[1]}" if row[1] else row[0]
        return None
    except Exception:
        try:
            conn.close()
        except Exception:
            pass
        return None
