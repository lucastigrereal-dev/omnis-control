"""ContextEngine — Camada 1 da Aurora.

Unifica fontes de contexto: state.json (sempre), leads.jsonl (sempre),
Notion (opcional — precisa de NOTION_TOKEN), Akasha (opcional — precisa de AKASHA_DB_URL).

Princípios:
- Graceful degradation: fonte indisponível → [] para aquela fonte, nunca crash
- Paralelismo via ThreadPoolExecutor (timeout 5s por fonte)
- Interface estável: Frente 1 (Notion) e Frente 2 (Akasha) só implementam
  _fetch_notion() e _fetch_akasha() — contrato não muda
- Sem inventar dado: se fonte não responde → results = []
- dry_run=True como default universal
"""
from __future__ import annotations

import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

_logger = logging.getLogger("omnis.aurora.context_engine")

_SOURCE_TIMEOUT_S = 5  # timeout por fonte (segundos)


@dataclass
class ContextResult:
    source: str        # "state_json" | "notion" | "akasha" | "leads"
    content: str       # texto recuperado
    relevance: float   # 0.0-1.0 (1.0 se não há ranking)
    metadata: dict = field(default_factory=dict)


@dataclass
class AuroraContext:
    results: list[ContextResult]
    sources_available: list[str]   # fontes que responderam com sucesso
    sources_failed: list[str]      # fontes que falharam (graceful degradation)
    query: str
    built_at: str

    def to_dict(self) -> dict:
        return {
            "results": [
                {
                    "source": r.source,
                    "content": r.content,
                    "relevance": r.relevance,
                    "metadata": r.metadata,
                }
                for r in self.results
            ],
            "sources_available": self.sources_available,
            "sources_failed": self.sources_failed,
            "query": self.query,
            "built_at": self.built_at,
        }


class ContextEngine:
    """Unifica fontes de contexto para a Aurora. Falha silenciosa por fonte.

    Uso mínimo:
        engine = ContextEngine(data_dir=Path("data"))
        ctx = engine.build(query="leads hoteis publicidade")

    Quando Notion e Akasha forem conectados (Frentes 1 e 2), basta implementar
    _fetch_notion() e _fetch_akasha() — a interface build() não muda.
    """

    def __init__(
        self,
        data_dir: Path = Path("data"),
        dry_run: bool = True,
    ) -> None:
        self.data_dir = Path(data_dir)
        self.dry_run = dry_run

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def build(
        self,
        query: str = "",
        max_results_per_source: int = 5,
    ) -> AuroraContext:
        """Busca contexto em todas as fontes disponíveis em paralelo.

        Fontes sempre ativas: state_json, leads.
        Fontes opcionais: notion (NOTION_TOKEN), akasha (AKASHA_DB_URL).

        Retorna AuroraContext com resultados agregados e logs de sucesso/falha.
        """
        built_at = datetime.now(timezone.utc).isoformat()

        # Mapa nome → callable
        sources: dict[str, Callable[[], list[ContextResult]]] = {
            "state_json": lambda: self._fetch_state_json(query),
            "leads": lambda: self._fetch_leads(query),
        }

        # Fontes opcionais — ativadas só se variável de ambiente presente
        if os.environ.get("NOTION_TOKEN"):
            sources["notion"] = lambda: self._fetch_notion(query, max_results_per_source)
        if os.environ.get("AKASHA_DB_URL"):
            sources["akasha"] = lambda: self._fetch_akasha(query, max_results_per_source)

        all_results: list[ContextResult] = []
        sources_available: list[str] = []
        sources_failed: list[str] = []

        executor = ThreadPoolExecutor(max_workers=len(sources) or 1)
        try:
            futures = {
                name: executor.submit(fn)
                for name, fn in sources.items()
            }

            for name, future in futures.items():
                try:
                    results = future.result(timeout=_SOURCE_TIMEOUT_S)
                    all_results.extend(results)
                    sources_available.append(name)
                    _logger.debug(
                        "context_engine: fonte=%s ok, %d resultados", name, len(results)
                    )
                except FuturesTimeoutError:
                    sources_failed.append(name)
                    future.cancel()
                    _logger.warning(
                        "context_engine: fonte=%s timeout após %ds — ignorada",
                        name,
                        _SOURCE_TIMEOUT_S,
                    )
                except Exception as exc:  # noqa: BLE001
                    sources_failed.append(name)
                    _logger.warning(
                        "context_engine: fonte=%s erro (%s: %s) — ignorada",
                        name,
                        type(exc).__name__,
                        exc,
                    )
        finally:
            # cancel_futures=True descarta tarefas pendentes na fila;
            # wait=False não bloqueia esperando threads já iniciadas.
            executor.shutdown(wait=False, cancel_futures=True)

        return AuroraContext(
            results=all_results,
            sources_available=sources_available,
            sources_failed=sources_failed,
            query=query,
            built_at=built_at,
        )

    # ------------------------------------------------------------------
    # Fontes sempre disponíveis
    # ------------------------------------------------------------------

    def _fetch_state_json(self, query: str) -> list[ContextResult]:  # noqa: ARG002
        """Lê data/state.json — sempre disponível, nunca falha em produção."""
        state_path = self.data_dir / "state.json"
        if not state_path.exists():
            _logger.debug("context_engine: state.json ausente em %s", state_path)
            return []

        try:
            raw = state_path.read_text(encoding="utf-8")
            data = json.loads(raw)
        except Exception as exc:  # noqa: BLE001
            _logger.warning("context_engine: falha ao ler state.json: %s", exc)
            return []

        # Serializa campos chave como texto legível para o prompt
        lines = []
        for key, val in data.items():
            if isinstance(val, (dict, list)):
                lines.append(f"{key}: {json.dumps(val, ensure_ascii=False)}")
            else:
                lines.append(f"{key}: {val}")

        content = "\n".join(lines)
        return [
            ContextResult(
                source="state_json",
                content=content,
                relevance=1.0,
                metadata={"path": str(state_path), "keys": list(data.keys())},
            )
        ]

    def _fetch_leads(self, query: str) -> list[ContextResult]:  # noqa: ARG002
        """Lê data/leads.jsonl — sempre disponível, nunca falha em produção."""
        leads_path = self.data_dir / "leads.jsonl"
        if not leads_path.exists():
            _logger.debug("context_engine: leads.jsonl ausente em %s", leads_path)
            return []

        results: list[ContextResult] = []
        try:
            for i, line in enumerate(leads_path.open(encoding="utf-8")):
                line = line.strip()
                if not line:
                    continue
                try:
                    lead = json.loads(line)
                except json.JSONDecodeError:
                    _logger.debug("context_engine: linha %d inválida em leads.jsonl", i)
                    continue

                nome = lead.get("nome", "?")
                perfil = lead.get("perfil", "?")
                temp = lead.get("temperatura", "?")
                status = lead.get("status", "?")
                valor = lead.get("valor_potencial", "?")
                ultimo = lead.get("ultimo_contato", "?")

                content = (
                    f"Lead: {nome} ({perfil}) | temp={temp} | "
                    f"status={status} | valor=R${valor} | ultimo_contato={ultimo}"
                )

                # Leads quentes têm relevância mais alta
                relevance = 1.0 if temp == "quente" else (0.7 if temp == "morno" else 0.4)

                results.append(
                    ContextResult(
                        source="leads",
                        content=content,
                        relevance=relevance,
                        metadata=lead,
                    )
                )
        except Exception as exc:  # noqa: BLE001
            _logger.warning("context_engine: falha ao ler leads.jsonl: %s", exc)
            return []

        return results

    # ------------------------------------------------------------------
    # Fontes opcionais — stubs prontos para Frente 1 e Frente 2
    # ------------------------------------------------------------------

    def _fetch_notion(self, query: str, max_results: int) -> list[ContextResult]:
        """Busca contexto no Notion via REST API (urllib stdlib, sem dependências).

        - Usa NOTION_TOKEN do environment (já checado antes de chamar)
        - POST https://api.notion.com/v1/search com query
        - Extrai título de cada page/database retornado
        - Retorna [] se sem resultados, sem páginas compartilhadas ou falha de rede
        - Nunca lança exceção — toda falha é silenciosa
        - Timeout: 8s (API externa)
        """
        import urllib.request
        import urllib.error

        token = os.environ.get("NOTION_TOKEN", "")
        if not token:
            return []

        payload = json.dumps({
            "query": query,
            "page_size": max(1, min(max_results, 20)),
        }).encode("utf-8")

        req = urllib.request.Request(
            "https://api.notion.com/v1/search",
            data=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            _logger.warning(
                "context_engine: Notion HTTP %d — %s", exc.code, exc.reason
            )
            return []
        except Exception as exc:  # noqa: BLE001
            _logger.warning("context_engine: Notion falhou (%s: %s) — ignorado", type(exc).__name__, exc)
            return []

        results: list[ContextResult] = []
        for item in data.get("results", []):
            obj_type = item.get("object", "")
            item_id = item.get("id", "")

            # Extrai título — formato varia entre page e database
            title = ""
            props = item.get("properties", {})
            for prop in props.values():
                ptype = prop.get("type", "")
                if ptype == "title":
                    parts = prop.get("title", [])
                    title = "".join(p.get("plain_text", "") for p in parts)
                    break
            if not title:
                # Databases têm title no top-level
                for part in item.get("title", []):
                    title += part.get("plain_text", "")

            if not title:
                title = f"[{obj_type} sem título]"

            # Monta conteúdo: título + URL da página
            url = item.get("url", "")
            content = f"{title}"
            if url:
                content += f" ({url})"

            results.append(
                ContextResult(
                    source="notion",
                    content=content,
                    relevance=1.0,
                    metadata={"id": item_id, "type": obj_type, "url": url},
                )
            )

        _logger.debug(
            "context_engine: Notion retornou %d resultados para query=%r",
            len(results),
            query,
        )
        return results

    def _fetch_akasha(self, query: str, max_results: int) -> list[ContextResult]:
        """Busca contexto no Akasha via full-text search (tsvector) no pgvector DB.

        Princípios:
        - Checar AKASHA_DB_URL via os.getenv — se ausente retorna [] (graceful)
        - Conectar com connect_timeout=3s para não bloquear o ThreadPoolExecutor
        - Busca FTS em document_chunks.tsv (tsvector indexado) + join em documents
        - Fallback ILIKE se FTS não retornar resultados
        - Fechar conexão sempre (try/finally)
        - Nunca lança exceção — toda falha retorna [] com log
        - Nunca inventa dado: banco vazio ou query sem match → retorna []
        """
        db_url = os.environ.get("AKASHA_DB_URL")
        if not db_url:
            _logger.debug("context_engine: AKASHA_DB_URL ausente — akasha ignorado")
            return []

        try:
            import psycopg2  # import local para não quebrar se psycopg2 não instalado
        except ImportError:
            _logger.warning("context_engine: psycopg2 não instalado — akasha ignorado")
            return []

        conn = None
        try:
            conn = psycopg2.connect(db_url, connect_timeout=3)
            cur = conn.cursor()
            cur.execute("SET statement_timeout = 5000")  # 5s por query (psycopg2 API)

            results: list[ContextResult] = []

            # Estratégia 1: full-text search via tsvector (coluna indexada)
            # Usa 'simple' para aceitar qualquer idioma sem stemming agressivo
            if query.strip():
                try:
                    cur.execute(
                        """
                        SELECT
                            dc.chunk_text,
                            d.domain,
                            d.file_name,
                            d.file_type,
                            dc.section_title,
                            ts_rank(dc.tsv, plainto_tsquery('simple', %(q)s)) AS rank
                        FROM document_chunks dc
                        JOIN documents d ON dc.document_id = d.id
                        WHERE dc.tsv @@ plainto_tsquery('simple', %(q)s)
                        ORDER BY rank DESC
                        LIMIT %(limit)s
                        """,
                        {"q": query, "limit": max_results},
                    )
                    rows = cur.fetchall()
                    for row in rows:
                        chunk_text, domain, file_name, file_type, section_title, rank = row
                        if not chunk_text:
                            continue
                        results.append(
                            ContextResult(
                                source="akasha",
                                content=str(chunk_text),
                                relevance=float(rank) if rank else 0.5,
                                metadata={
                                    "domain": domain,
                                    "file_name": file_name,
                                    "file_type": file_type,
                                    "section_title": section_title,
                                    "strategy": "fts_tsvector",
                                },
                            )
                        )
                except Exception as exc:  # noqa: BLE001
                    _logger.debug("context_engine: akasha FTS falhou (%s) — sem resultados", exc)

            # Estratégia 2: ILIKE fallback se FTS não retornou nada e query não está vazia
            if not results and query.strip():
                try:
                    cur.execute(
                        """
                        SELECT
                            dc.chunk_text,
                            d.domain,
                            d.file_name,
                            d.file_type,
                            dc.section_title
                        FROM document_chunks dc
                        JOIN documents d ON dc.document_id = d.id
                        WHERE dc.chunk_text ILIKE %(pattern)s
                        LIMIT %(limit)s
                        """,
                        {"pattern": f"%{query}%", "limit": max_results},
                    )
                    rows = cur.fetchall()
                    for row in rows:
                        chunk_text, domain, file_name, file_type, section_title = row
                        if not chunk_text:
                            continue
                        results.append(
                            ContextResult(
                                source="akasha",
                                content=str(chunk_text),
                                relevance=0.5,
                                metadata={
                                    "domain": domain,
                                    "file_name": file_name,
                                    "file_type": file_type,
                                    "section_title": section_title,
                                    "strategy": "ilike_fallback",
                                },
                            )
                        )
                except Exception as exc:  # noqa: BLE001
                    _logger.debug("context_engine: akasha ILIKE falhou (%s) — sem resultados", exc)

            _logger.debug(
                "context_engine: akasha retornou %d resultados para query=%r",
                len(results),
                query,
            )
            return results

        except Exception as exc:  # noqa: BLE001
            _logger.warning(
                "context_engine: akasha conexao falhou (%s: %s) — retornando []",
                type(exc).__name__,
                exc,
            )
            return []
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:  # noqa: BLE001
                    pass
