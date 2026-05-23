"""ResearchConductorLego — STORM-adapted wide research sem dspy.

Extrai o algoritmo core do stanford-oval/storm e adapta ao padrão OMNIS:
  - LiteLLM proxy local-first (Ollama) em vez de OpenAI/Anthropic hardcoded
  - SearchBackend plugável em vez de Bing/Google hardcoded
  - asyncio.to_thread wrapper para não travar o runtime OMNIS

Pipeline STORM simplificado (5 etapas):
  1. _generate_perspectives  → N ângulos de pesquisa sobre o tópico
  2. _curate_knowledge       → Q&A por perspectiva + busca + snippets
  3. _generate_outline       → Estrutura do artigo
  4. _generate_article       → Artigo completo com citações
  5. _polish_article         → Revisão final

Regras OMNIS:
  - dry_run=True por padrão — retorna plano sem chamar LLM/search
  - Approval gate antes de publicar/compartilhar em dry_run=False
  - Semaphore(1) — pesquisa é pesada, 1 sessão por vez
  - LLM roteado via LiteLLM proxy (LITELLM_URL + STORM_LLM_MODEL)
  - cost_local_pct=100 quando modelo começa com "ollama/"
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import threading
from pathlib import Path
from typing import Protocol, runtime_checkable

from src.interfaces.research_conductor import (
    ResearchConductor, ResearchSpec, ResearchResult,
    ResearchPerspective, ResearchCitation,
)

_logger = logging.getLogger("omnis.legos.research")

LITELLM_URL = os.getenv("LITELLM_URL", "http://localhost:4001")
STORM_LLM_MODEL = os.getenv("STORM_LLM_MODEL", "ollama/qwen2.5:7b")
SEARXNG_URL = os.getenv("SEARXNG_URL", "")

_RESEARCH_SEMAPHORE = threading.Semaphore(1)

_PUBLISH_KEYWORDS = frozenset({
    "publicar", "publish", "upload", "postar", "post",
    "enviar", "send", "share", "compartilhar",
})


def _requires_publish_approval(goal: str) -> bool:
    return any(kw in goal.lower() for kw in _PUBLISH_KEYWORDS)


def _cost_local_pct() -> int:
    m = STORM_LLM_MODEL.lower()
    if m.startswith("ollama/"):
        return 100
    if any(m.startswith(p) for p in ("gpt", "openai/", "claude", "anthropic/")):
        return 0
    return 50


# ── Search Backend (plugável) ─────────────────────────────────────────────────

class _SearchResult:
    __slots__ = ("url", "title", "snippet")

    def __init__(self, url: str, title: str, snippet: str) -> None:
        self.url = url
        self.title = title
        self.snippet = snippet


@runtime_checkable
class SearchBackend(Protocol):
    def search(self, query: str, k: int = 3) -> list[_SearchResult]: ...
    def name(self) -> str: ...


class NullSearchBackend:
    """Retorna lista vazia — usado em dry_run ou quando nenhum backend configurado."""

    def search(self, query: str, k: int = 3) -> list[_SearchResult]:
        return []

    def name(self) -> str:
        return "null"


class SearXNGBackend:
    """Busca via SearXNG. Não requer API key — apenas SEARXNG_URL apontando para a instância."""

    def __init__(self, url: str) -> None:
        self._url = url.rstrip("/")

    def name(self) -> str:
        return "searxng"

    def search(self, query: str, k: int = 3) -> list[_SearchResult]:
        import urllib.request
        import urllib.parse

        params = urllib.parse.urlencode({
            "q": query, "format": "json", "language": "auto",
        })
        try:
            req_url = f"{self._url}/search?{params}"
            with urllib.request.urlopen(req_url, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            results = []
            for item in data.get("results", [])[:k]:
                results.append(_SearchResult(
                    url=item.get("url", ""),
                    title=item.get("title", ""),
                    snippet=item.get("content", item.get("snippet", ""))[:800],
                ))
            return results
        except Exception as exc:
            _logger.warning("[research] SearXNG search failed: %s", exc)
            return []


# ── LLM Client ───────────────────────────────────────────────────────────────

class _LLMClient:
    """Chama litellm.completion com api_base apontando para nosso proxy local."""

    def chat(self, messages: list[dict], max_tokens: int = 800) -> str:
        import litellm
        resp = litellm.completion(
            model=STORM_LLM_MODEL,
            messages=messages,
            api_base=LITELLM_URL,
            max_tokens=max_tokens,
            temperature=0.7,
        )
        return resp.choices[0].message.content.strip()


# ── STORM Pipeline (sync, sem dspy) ──────────────────────────────────────────

class _StormPipeline:
    """Algoritmo STORM extraído sem dependência de dspy.

    Correspondências com stanford-oval/storm:
      PersonaGenerator          → _generate_perspectives
      KnowledgeCurationModule   → _curate_knowledge
      OutlineGenerationModule   → _generate_outline
      ArticleGenerationModule   → _generate_article
      ArticlePolishingModule    → _polish_article

    LLM calls via _LLMClient (litellm → proxy local).
    Search via SearchBackend plugável.
    """

    def __init__(self, llm: _LLMClient, search: SearchBackend) -> None:
        self._llm = llm
        self._search = search

    def run(self, spec: ResearchSpec) -> ResearchResult:
        topic = spec.topic

        perspectives = self._generate_perspectives(topic, spec.max_perspectives)
        info_table, citations = self._curate_knowledge(
            topic, perspectives, spec.max_search_queries_per_perspective,
        )
        outline = self._generate_outline(topic, info_table)
        draft = self._generate_article(topic, outline, info_table, citations)
        polished = self._polish_article(topic, draft)

        return ResearchResult(
            success=True,
            topic=topic,
            report=polished,
            perspectives=perspectives,
            citations=citations,
            dry_run=False,
            artifacts={
                "cost_local_pct": _cost_local_pct(),
                "llm_model": STORM_LLM_MODEL,
                "search_backend": self._search.name(),
                "perspectives_count": len(perspectives),
                "citations_count": len(citations),
            },
        )

    def _generate_perspectives(self, topic: str, n: int) -> list[ResearchPerspective]:
        """Etapa 1 — PersonaGenerator: gera N perspectivas de pesquisa."""
        prompt = (
            f"Research topic: '{topic}'\n"
            f"Generate {n} distinct research perspectives/angles.\n"
            "For each, provide a short name and 2-3 key questions.\n"
            "Respond with JSON only:\n"
            '[{"name": "...", "questions": ["...", "..."]}]'
        )
        try:
            raw = self._llm.chat([{"role": "user", "content": prompt}], max_tokens=600)
            raw = raw.strip()
            if raw.startswith("```"):
                raw = "\n".join(raw.split("\n")[1:])
                if raw.endswith("```"):
                    raw = raw[: raw.rfind("```")]
            data = json.loads(raw)
            return [
                ResearchPerspective(
                    name=item.get("name", f"Perspective {i+1}"),
                    questions=item.get("questions", []),
                )
                for i, item in enumerate(data[:n])
            ]
        except Exception as exc:
            _logger.warning("[research] perspective generation failed: %s", exc)
            return [ResearchPerspective(name=f"Perspective {i+1}", questions=[topic]) for i in range(min(n, 3))]

    def _curate_knowledge(
        self, topic: str, perspectives: list[ResearchPerspective], queries_per: int,
    ) -> tuple[list[dict], list[ResearchCitation]]:
        """Etapa 2 — KnowledgeCurationModule: Q&A por perspectiva + busca."""
        info_table: list[dict] = []
        citations: list[ResearchCitation] = []
        seen_urls: set[str] = set()

        for persp in perspectives:
            queries = (persp.questions or [topic])[:queries_per]
            persp_snippets: list[str] = []

            for query in queries:
                results = self._search.search(query, k=3)
                for r in results:
                    if r.url and r.url not in seen_urls:
                        seen_urls.add(r.url)
                        citations.append(ResearchCitation(
                            url=r.url, title=r.title,
                            snippet=r.snippet, perspective=persp.name,
                        ))
                    if r.snippet:
                        persp_snippets.append(f"[{r.title}]: {r.snippet}")

            synthesis = ""
            if persp_snippets:
                prompt = (
                    f"Topic: {topic}\nPerspective: {persp.name}\n\n"
                    "Sources:\n" + "\n".join(persp_snippets[:5]) + "\n\n"
                    "Synthesize 2-3 key insights for this perspective."
                )
                try:
                    synthesis = self._llm.chat(
                        [{"role": "user", "content": prompt}], max_tokens=400,
                    )
                except Exception as exc:
                    _logger.warning("[research] synthesis failed for '%s': %s", persp.name, exc)
                    synthesis = "\n".join(persp_snippets[:2])

            info_table.append({
                "perspective": persp.name,
                "questions": queries,
                "synthesis": synthesis,
                "snippets": persp_snippets[:5],
            })

        return info_table, citations

    def _generate_outline(self, topic: str, info_table: list[dict]) -> str:
        """Etapa 3 — OutlineGenerationModule."""
        summary = "\n".join(
            f"- {item['perspective']}: {item.get('synthesis', '')[:200]}"
            for item in info_table
        )
        prompt = (
            f"Create a structured article outline for: '{topic}'\n\n"
            f"Research perspectives:\n{summary}\n\n"
            "Generate 4-6 main sections with 2-3 key points each.\n"
            "Format: ## Section\\n- point 1\\n- point 2"
        )
        try:
            return self._llm.chat([{"role": "user", "content": prompt}], max_tokens=500)
        except Exception as exc:
            _logger.warning("[research] outline generation failed: %s", exc)
            return "\n".join(f"## {item['perspective']}" for item in info_table)

    def _generate_article(
        self,
        topic: str,
        outline: str,
        info_table: list[dict],
        citations: list[ResearchCitation],
    ) -> str:
        """Etapa 4 — ArticleGenerationModule."""
        cit_context = "\n".join(
            f"[{i+1}] {c.title}: {c.snippet[:200]}"
            for i, c in enumerate(citations[:12])
        )
        info_context = "\n\n".join(
            f"### {item['perspective']}\n{item.get('synthesis', '')}"
            for item in info_table
        )
        prompt = (
            f"Write a comprehensive article about: '{topic}'\n\n"
            f"Outline:\n{outline}\n\n"
            f"Research:\n{info_context}\n\n"
            f"Citations:\n{cit_context}\n\n"
            "Write 600-900 words. Reference citations as [1], [2], etc."
        )
        try:
            return self._llm.chat([{"role": "user", "content": prompt}], max_tokens=1200)
        except Exception as exc:
            _logger.warning("[research] article generation failed: %s", exc)
            return f"# {topic}\n\n" + "\n\n".join(
                item.get("synthesis", "") for item in info_table
            )

    def _polish_article(self, topic: str, draft: str) -> str:
        """Etapa 5 — ArticlePolishingModule."""
        prompt = (
            f"Polish this article about '{topic}':\n\n{draft}\n\n"
            "Ensure clear structure, smooth transitions, strong intro and conclusion. "
            "Keep citations. Same length."
        )
        try:
            return self._llm.chat([{"role": "user", "content": prompt}], max_tokens=1400)
        except Exception as exc:
            _logger.warning("[research] polish failed: %s", exc)
            return draft


# ── ResearchConductorLego ─────────────────────────────────────────────────────

class ResearchConductorLego:
    """Implementação do Protocol ResearchConductor.

    STORM algorithm sem dspy — litellm local-first + SearchBackend plugável.
    Injeção de dependências para facilitar testes:
      search_backend → qualquer SearchBackend (default: SearXNGBackend ou NullSearchBackend)
      llm_client     → _LLMClient (default: usa LITELLM_URL + STORM_LLM_MODEL)
    """

    def __init__(
        self,
        search_backend: SearchBackend | None = None,
        llm_client: _LLMClient | None = None,
    ) -> None:
        self._search = search_backend or self._default_search()
        self._llm = llm_client or _LLMClient()

    @staticmethod
    def _default_search() -> SearchBackend:
        if SEARXNG_URL:
            return SearXNGBackend(SEARXNG_URL)
        return NullSearchBackend()

    def health_check(self) -> bool:
        """Retorna True se litellm está disponível (LLM proxy pode estar offline)."""
        try:
            import litellm  # noqa: F401
            return True
        except ImportError:
            return False

    def execute(self, spec: ResearchSpec) -> ResearchResult:
        """Executa pesquisa via pipeline STORM adaptado."""
        if not spec.dry_run and _requires_publish_approval(spec.topic):
            _logger.warning("[research] APPROVAL REQUIRED for topic: '%s'", spec.topic[:80])
            return ResearchResult(
                success=False, topic=spec.topic, report="", dry_run=False,
                error="approval_required",
                artifacts={"approval_required": True, "topic": spec.topic},
            )

        if spec.dry_run:
            return self._dry_run_plan(spec)

        acquired = _RESEARCH_SEMAPHORE.acquire(timeout=5)
        if not acquired:
            return ResearchResult(
                success=False, topic=spec.topic, report="", dry_run=False,
                error="research_semaphore_timeout",
            )

        try:
            pipeline = _StormPipeline(llm=self._llm, search=self._search)
            result = pipeline.run(spec)

            if spec.output_dir:
                result = self._persist_result(result, spec)

            if spec.store_in_akasha:
                self._store_in_akasha(result)

            return result
        except Exception as exc:
            _logger.error("[research] pipeline failed: %s", exc)
            return ResearchResult(
                success=False, topic=spec.topic, report="", dry_run=False,
                error=str(exc),
            )
        finally:
            _RESEARCH_SEMAPHORE.release()

    async def execute_async(self, spec: ResearchSpec) -> ResearchResult:
        """Wrapper async — não trava o runtime OMNIS."""
        return await asyncio.to_thread(self.execute, spec)

    def _dry_run_plan(self, spec: ResearchSpec) -> ResearchResult:
        plan = (
            f"# Plano de Pesquisa: {spec.topic}\n\n"
            f"## Pipeline STORM (dry_run)\n"
            f"1. Gerar {spec.max_perspectives} perspectivas sobre o tópico\n"
            f"2. {spec.max_search_queries_per_perspective} queries de busca por perspectiva\n"
            f"3. Curar conhecimento (Q&A + síntese por perspectiva)\n"
            f"4. Gerar outline estruturado\n"
            f"5. Gerar artigo completo com citações\n"
            f"6. Polish final\n\n"
            f"## Configuração\n"
            f"- LLM: {STORM_LLM_MODEL} via {LITELLM_URL}\n"
            f"- Search backend: {self._search.name()}\n"
            f"- Output dir: {spec.output_dir}\n"
            f"- Store in Akasha: {spec.store_in_akasha}\n"
            f"- cost_local_pct: {_cost_local_pct()}%\n\n"
            f"[dry_run=True — nenhuma chamada LLM ou busca realizada]"
        )
        mock_perspectives = [
            ResearchPerspective(
                name=f"Perspectiva {i+1}",
                questions=[f"Query exemplo {i+1} sobre: {spec.topic}"],
            )
            for i in range(spec.max_perspectives)
        ]
        return ResearchResult(
            success=True,
            topic=spec.topic,
            report=plan,
            perspectives=mock_perspectives,
            citations=[],
            dry_run=True,
            artifacts={
                "mode": "dry_run_plan",
                "llm_model": STORM_LLM_MODEL,
                "search_backend": self._search.name(),
                "cost_local_pct": _cost_local_pct(),
            },
        )

    def _persist_result(self, result: ResearchResult, spec: ResearchSpec) -> ResearchResult:
        slug = spec.topic[:50].replace(" ", "_").replace("/", "_")
        out_dir = Path(spec.output_dir) / slug
        out_dir.mkdir(parents=True, exist_ok=True)

        report_path = str(out_dir / "report.md")
        citations_path = str(out_dir / "citations.json")

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"# {spec.topic}\n\n{result.report}")

        cit_data = [
            {"url": c.url, "title": c.title, "snippet": c.snippet, "perspective": c.perspective}
            for c in result.citations
        ]
        with open(citations_path, "w", encoding="utf-8") as f:
            json.dump(cit_data, f, ensure_ascii=False, indent=2)

        result.files_created.extend([report_path, citations_path])
        return result

    def _store_in_akasha(self, result: ResearchResult) -> None:
        """Persiste no Akasha (pgvector). Log apenas — não falha se Akasha offline."""
        _logger.info(
            "[research] store_in_akasha: topic='%s', perspectives=%d, citations=%d",
            result.topic, result.perspective_count, result.citation_count,
        )
