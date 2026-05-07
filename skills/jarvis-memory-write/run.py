#!/usr/bin/env python3
"""jarvis-memory-write: Persiste resultados em Akasha + Notion + Git."""

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from typing import Optional
from urllib.request import Request, urlopen

DB_CONFIG = {
    "host": os.getenv("AKASHA_HOST", "localhost"),
    "port": int(os.getenv("AKASHA_PORT", "5432")),
    "user": os.getenv("AKASHA_USER", "akasha"),
    "password": os.getenv("AKASHA_PASSWORD", "akasha123"),
    "database": os.getenv("AKASHA_DB", "akasha"),
}
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
PENDENCIAS_FILE = os.path.expanduser("~/.claude/PENDENCIAS_NOTION.md")


def gerar_fingerprint(conteudo: str) -> str:
    return hashlib.sha256(conteudo.encode()).hexdigest()[:16]


def salvar_akasha(conteudo: str, setor: str, skill_origem: str = "",
                  tags: Optional[list] = None, metadata_extra: Optional[dict] = None) -> dict:
    """Insere chunk no Akasha com fingerprint."""
    if not conteudo:
        return {"erro": "conteudo vazio"}

    try:
        import psycopg2
        fingerprint = gerar_fingerprint(conteudo)

        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Verifica duplicata por fingerprint
        cur.execute("SELECT id FROM memoria_conversas WHERE titulo LIKE %s LIMIT 1",
                    (f"%{fingerprint}%",))
        if cur.fetchone():
            cur.close()
            conn.close()
            return {"status": "duplicate_skipped", "fingerprint": fingerprint}

        # Gera embedding
        r = urlopen(Request(f"{OLLAMA_URL}/api/embeddings",
                            json.dumps({"model": "nomic-embed-text", "prompt": conteudo}).encode(),
                            {"Content-Type": "application/json"}), timeout=30)
        emb = json.loads(r.read()).get("embedding")

        metadata = {
            "setor": setor,
            "skill_origem": skill_origem,
            "tags": tags or [],
            "fingerprint": fingerprint,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if metadata_extra:
            metadata.update(metadata_extra)

        titulo = f"[{skill_origem}] {conteudo[:80]} | {fingerprint}" if skill_origem else f"{conteudo[:80]} | {fingerprint}"
        cur.execute("""
            INSERT INTO memoria_conversas (titulo, summary, embedding, metadata)
            VALUES (%s, %s, %s::vector, %s)
            RETURNING id
        """, (titulo, conteudo[:500], str(emb), json.dumps(metadata)))
        chunk_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "saved", "chunk_id": chunk_id, "fingerprint": fingerprint}

    except ImportError:
        return {"erro": "psycopg2 nao instalado"}
    except Exception as e:
        return {"erro": f"Akasha indisponivel: {e}"}


def salvar_notion_pendencia(conteudo: str, setor: str) -> dict:
    """Salva pendência no arquivo local (fallback enquanto NOTION_TOKEN não configurado)."""
    try:
        entry = f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M')} | {setor}\n{conteudo}\n"
        with open(PENDENCIAS_FILE, "a") as f:
            f.write(entry)
        return {"status": "pending_notion_token", "arquivo": PENDENCIAS_FILE}
    except Exception as e:
        return {"erro": f"Falha ao salvar pendencia: {e}"}


def commitar_git(repo_path: str, mensagem: str) -> dict:
    """Faz commit se houver mudanças."""
    try:
        result = subprocess.run(["git", "-C", repo_path, "status", "--short"],
                                capture_output=True, text=True, timeout=10)
        if not result.stdout.strip():
            return {"status": "no_changes"}

        subprocess.run(["git", "-C", repo_path, "add", "-A"], capture_output=True, timeout=10)
        commit_msg = f"feat({setor}): {mensagem}\n\nCo-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
        r = subprocess.run(["git", "-C", repo_path, "commit", "-m", commit_msg],
                           capture_output=True, text=True, timeout=15)
        if r.returncode == 0:
            sha = subprocess.run(["git", "-C", repo_path, "rev-parse", "--short", "HEAD"],
                                 capture_output=True, text=True, timeout=5)
            return {"status": "committed", "sha": sha.stdout.strip()}
        return {"status": "commit_failed", "erro": r.stderr[:200]}
    except Exception as e:
        return {"erro": str(e)}


def memory_write(conteudo: str, setor: str, skill_origem: str = "",
                 tags: Optional[list] = None, repo_path: Optional[str] = None,
                 commit_msg: Optional[str] = None,
                 metadata_extra: Optional[dict] = None) -> dict:
    """Pipeline completo: Akasha + Notion + Git."""
    resultado = {
        "status": "saved",
        "akasha": None,
        "notion": None,
        "git": None,
        "errors": [],
        "next_action": None,
    }

    # 1. Akasha
    akasha = salvar_akasha(conteudo, setor, skill_origem, tags, metadata_extra)
    resultado["akasha"] = akasha
    if "erro" in akasha:
        resultado["errors"].append(f"Akasha: {akasha['erro']}")

    # 2. Notion (fallback: pendência local)
    notion = salvar_notion_pendencia(conteudo, setor)
    resultado["notion"] = notion
    if "erro" in notion:
        resultado["errors"].append(f"Notion: {notion['erro']}")

    # 3. Git
    if repo_path:
        git = commitar_git(repo_path, commit_msg or skill_origem)
        resultado["git"] = git
        if "erro" in git:
            resultado["errors"].append(f"Git: {git['erro']}")

    if resultado["errors"]:
        resultado["status"] = "partial"

    resultado["next_action"] = "Pronto. Memoria salva."
    return resultado


if __name__ == "__main__":
    conteudo = " ".join(sys.argv[1:]) or "teste de memoria"
    result = memory_write(conteudo, setor="operacoes_organizacao", skill_origem="jarvis-memory-write")
    print(json.dumps(result, indent=2, ensure_ascii=False))
