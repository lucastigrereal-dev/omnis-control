#!/usr/bin/env python3
"""jarvis-brain: Motor de contexto multi-fonte. Consulta Akasha + Mem0 + Obsidian + Docker."""

import json
import os
import subprocess
import sys
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
OBSIDIAN_BASE = os.path.expanduser("~/Desktop/OBSIDIAN/ComandoCentral")


def buscar_akasha(query: str, top_k: int = 10) -> list:
    """Busca semântica no Akasha via pgvector + tsvector."""
    try:
        import psycopg2
        r = urlopen(Request(f"{OLLAMA_URL}/api/embeddings",
                           json.dumps({"model": "nomic-embed-text", "prompt": query}).encode(),
                           {"Content-Type": "application/json"}), timeout=10)
        emb = json.loads(r.read()).get("embedding")
        if not emb:
            return [{"erro": "Ollama offline"}]

        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, titulo, summary, score
            FROM busca_hibrida(%s, %s::vector, %s)
            WHERE score > 0.50
        """, (query, str(emb), top_k))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [{"id": r[0], "titulo": r[1], "summary": r[2], "score": float(r[3])} for r in rows]
    except ImportError:
        return [{"erro": "psycopg2 nao instalado"}]
    except Exception as e:
        return [{"erro": f"Akasha indisponivel: {e}"}]


def buscar_obsidian(query: str, max_results: int = 5) -> list:
    """Busca declarativa no Obsidian por grep."""
    results = []
    try:
        result = subprocess.run(
            ["grep", "-ri", query, f"{OBSIDIAN_BASE}/00_Contexto/", "--include=*.md", "-l"],
            capture_output=True, text=True, timeout=10
        )
        files = result.stdout.strip().split("\n")[:max_results] if result.stdout.strip() else []
        for f in files:
            if os.path.exists(f):
                trecho = subprocess.run(
                    ["grep", "-i", query, f, "-m", "2"],
                    capture_output=True, text=True, timeout=5
                )
                results.append({
                    "arquivo": os.path.relpath(f, OBSIDIAN_BASE),
                    "trechos": trecho.stdout.strip()[:200] if trecho.stdout.strip() else ""
                })
    except Exception:
        pass
    return results


def buscar_docker(projeto: Optional[str] = None) -> dict:
    """Estado dos containers Docker."""
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}\t{{.Ports}}"],
            capture_output=True, text=True, timeout=10
        )
        containers = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("\t")
            containers.append({"nome": parts[0], "status": parts[1], "portas": parts[2] if len(parts) > 2 else ""})

        # Filtra por projeto se especificado
        if projeto:
            containers = [c for c in containers if projeto.lower() in c["nome"].lower()]

        # Conta unhealthy
        unhealthy = [c for c in containers if "unhealthy" in c["status"].lower()]

        return {
            "containers": containers[:15],
            "total": len(containers),
            "unhealthy": [c["nome"] for c in unhealthy]
        }
    except Exception as e:
        return {"erro": f"Docker indisponivel: {e}"}


def brain(query: str, projeto: Optional[str] = None) -> dict:
    """Pipeline principal: consulta todas as fontes em paralelo (ou sequencial)."""
    if not query or not query.strip():
        return {"erro": "query vazia", "fontes": {}}

    from concurrent.futures import ThreadPoolExecutor, as_completed

    resultados = {"query": query}
    fontes = {}

    with ThreadPoolExecutor(max_workers=4) as executor:
        futuros = {
            executor.submit(buscar_akasha, query): "akasha",
            executor.submit(buscar_obsidian, query): "obsidian",
        }
        if projeto:
            futuros[executor.submit(buscar_docker, projeto)] = "docker"

        for future in as_completed(futuros):
            nome = futuros[future]
            try:
                fontes[nome] = future.result()
            except Exception as e:
                fontes[nome] = [{"erro": str(e)}]

    # Docker state (sempre incluso se projeto)
    if projeto:
        fontes["docker"] = buscar_docker(projeto)

    # Sintetizar
    resumo_akasha = [r for r in fontes.get("akasha", []) if "erro" not in r]
    resumo_obsidian = fontes.get("obsidian", [])

    sintese_parts = []
    if resumo_akasha:
        sintese_parts.append(f"Akasha: {len(resumo_akasha)} resultados")
    if resumo_obsidian:
        sintese_parts.append(f"Obsidian: {len(resumo_obsidian)} arquivos")
    if projeto and "docker" in fontes and "erro" not in fontes["docker"]:
        d = fontes["docker"]
        sintese_parts.append(f"Docker: {d.get('total', 0)} containers, {len(d.get('unhealthy', []))} unhealthy")

    resultados["fontes"] = fontes
    resultados["sintese"] = " | ".join(sintese_parts) if sintese_parts else "Nenhum resultado encontrado"
    resultados["next_action"] = f"Contexto coletado. Passar para jarvis-delegate com setor inferido da query."

    return resultados


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) or "ultimo progresso"
    projeto = sys.argv[2] if len(sys.argv) > 2 else None
    result = brain(query, projeto)
    print(json.dumps(result, indent=2, ensure_ascii=False))
