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
        """Busca contexto no Notion.

        STUB — Frente 1 implementa este método.

        Contrato esperado:
        - Usa NOTION_TOKEN do environment (já checado antes de chamar)
        - Retorna lista[ContextResult] com source="notion"
        - Nunca lança exceção — falha silenciosa (retorna [])
        - Timeout interno recomendado: 4s (abaixo do timeout do ThreadPoolExecutor)

        Interface para Frente 1:
            notion_client = Client(auth=os.environ["NOTION_TOKEN"])
            results = notion_client.search(query=query, page_size=max_results)
            # Para cada resultado, construir ContextResult(source="notion", ...)
        """
        _logger.info(
            "context_engine: _fetch_notion stub chamado (query=%r, max=%d) — "
            "aguardando implementação da Frente 1",
            query,
            max_results,
        )
        return []

    def _fetch_akasha(self, query: str, max_results: int) -> list[ContextResult]:
        """Busca contexto no Akasha (pgvector).

        STUB — Frente 2 implementa este método.

        Contrato esperado:
        - Usa AKASHA_DB_URL do environment (já checado antes de chamar)
        - Retorna lista[ContextResult] com source="akasha"
        - Nunca lança exceção — falha silenciosa (retorna [])
        - Timeout interno recomendado: 4s (abaixo do timeout do ThreadPoolExecutor)

        Interface para Frente 2 (psycopg2 / pgvector):
            conn = psycopg2.connect(os.environ["AKASHA_DB_URL"])
            # SELECT content, 1-(embedding <=> %s::vector) AS score
            #   FROM documents ORDER BY score DESC LIMIT %s
            # Para cada linha, construir ContextResult(source="akasha",
            #     content=row.content, relevance=row.score, ...)
        """
        _logger.info(
            "context_engine: _fetch_akasha stub chamado (query=%r, max=%d) — "
            "aguardando implementação da Frente 2",
            query,
            max_results,
        )
        return []
