"""SEOgramWorkflow — otimiza caption para o algoritmo do Instagram via Ollama.

Onda 35: recebe caption bruta + contexto de conta e retorna versão SEO-otimizada:
  - optimized_hook  — primeira linha reescrita para máximo gancho
  - hashtag_clusters — agrupados por nicho/localização/engajamento/trending
  - hashtags         — lista plana (max 30)
  - keyword_density  — float 0-1 (estimativa de cobertura de palavras-chave)
  - seo_score        — int 1-10
  - improvement_notes — sugestões de melhoria

dry_run=True  → retorna dados template sem chamar LLM
dry_run=False → chama OllamaAdapter local (custo zero)
"""
from __future__ import annotations

import json
import logging
import urllib.request
from dataclasses import dataclass, field

from src.akasha_event_sink.adapter import AkashaSinkAdapter
from src.akasha_event_sink.models import SinkEvent
from src.utils.run_context import RunContext

_logger = logging.getLogger("omnis.workflows.seogram")
_COST_LOCAL_PCT = 100
_OLLAMA_URL = "http://localhost:11434/v1/chat/completions"
_DEFAULT_MODEL = "llama3.1:8b"
_DEFAULT_TIMEOUT = 120

_DRY_RUN_RESULT = {
    "optimized_hook": "Praia de Ponta Negra ao entardecer — um espetáculo que só Natal tem.",
    "hashtag_clusters": {
        "niche": ["#turismo", "#viagem", "#brasil"],
        "location": ["#natal", "#riograndenorte", "#nordeste"],
        "engagement": ["#porDoDol", "#praia", "#natureza"],
        "trending": ["#reels", "#explorepage", "#foryou"],
    },
    "hashtags": [
        "#turismo", "#viagem", "#brasil",
        "#natal", "#riograndenorte", "#nordeste",
        "#porDoDol", "#praia", "#natureza",
        "#reels", "#explorepage", "#foryou",
    ],
    "keyword_density": 0.72,
    "seo_score": 8,
    "improvement_notes": [
        "Inclua CTA no último parágrafo",
        "Use localização precisa na primeira frase",
    ],
}


@dataclass
class SEOgramResult:
    run_id: str
    success: bool
    account_handle: str
    raw_caption: str
    optimized_hook: str = ""
    hashtag_clusters: dict[str, list[str]] = field(default_factory=dict)
    hashtags: list[str] = field(default_factory=list)
    keyword_density: float = 0.0
    seo_score: int = 0
    improvement_notes: list[str] = field(default_factory=list)
    model_used: str = ""
    tokens_used: int = 0
    akasha_event_id: str = ""
    cost_local_pct: int = _COST_LOCAL_PCT
    error: str | None = None

    @property
    def hashtag_count(self) -> int:
        return len(self.hashtags)

    @property
    def is_optimized(self) -> bool:
        return self.success and self.seo_score >= 7

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "success": self.success,
            "account_handle": self.account_handle,
            "optimized_hook": self.optimized_hook,
            "hashtags": self.hashtags,
            "hashtag_count": self.hashtag_count,
            "keyword_density": self.keyword_density,
            "seo_score": self.seo_score,
            "improvement_notes": self.improvement_notes,
            "model_used": self.model_used,
            "tokens_used": self.tokens_used,
            "akasha_event_id": self.akasha_event_id,
            "cost_local_pct": self.cost_local_pct,
        }


_SYSTEM_PROMPT = (
    "Você é um especialista em SEO para Instagram. "
    "Sempre responda com JSON válido, sem markdown, sem explicações extras."
)

_USER_TEMPLATE = """\
Conta: {account_handle}
Nicho: {niche}
Caption bruta:
---
{raw_caption}
---

Retorne JSON com exatamente estas chaves:
{{
  "optimized_hook": "primeira linha reescrita para máximo engajamento (string, 1 frase)",
  "hashtag_clusters": {{
    "niche": ["#tag1", "#tag2"],
    "location": ["#tag1", "#tag2"],
    "engagement": ["#tag1", "#tag2"],
    "trending": ["#tag1", "#tag2"]
  }},
  "hashtags": ["lista plana com até 30 hashtags"],
  "keyword_density": 0.85,
  "seo_score": 8,
  "improvement_notes": ["dica 1", "dica 2"]
}}

Regras:
- Total de hashtags ≤ 30
- seo_score deve refletir a caption ORIGINAL, não a reescrita
- improvement_notes: 2-4 dicas práticas específicas
- Responda SOMENTE o JSON, sem nenhum texto antes ou depois.
"""

_NICHE_MAP: dict[str, str] = {
    "@oinatalrn": "turismo e gastronomia em Natal/RN, Brasil",
    "@agenteviajabrasil": "viagens pelo Brasil",
    "@afamiliatigrereal": "família e lifestyle",
    "@oquecomernatalrn": "gastronomia em Natal/RN",
    "@natalaivoueu": "guia turístico de Natal/RN e praias",
    "@lucastigrereal": "lifestyle, viagem e influência",
}


def _niche_for(handle: str) -> str:
    return _NICHE_MAP.get(handle, "conteúdo de nicho no Instagram brasileiro")


def _parse_json(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(
            line for line in lines if not line.strip().startswith("```")
        ).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass
    return {}


def _to_list(v: object) -> list[str]:
    if isinstance(v, list):
        return [str(x) for x in v]
    if isinstance(v, str):
        return [s.strip() for s in v.split(",") if s.strip()]
    return []


def _call_ollama(
    account_handle: str,
    raw_caption: str,
    model: str = _DEFAULT_MODEL,
    timeout: int = _DEFAULT_TIMEOUT,
) -> tuple[dict, str, int]:
    niche = _niche_for(account_handle)
    user_msg = _USER_TEMPLATE.format(
        account_handle=account_handle,
        niche=niche,
        raw_caption=raw_caption[:2000],
    )
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.4,
        "stream": False,
    }).encode()

    req = urllib.request.Request(
        _OLLAMA_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read())

    content = data["choices"][0]["message"]["content"]
    tokens = data.get("usage", {}).get("total_tokens", 0)
    model_used = data.get("model", model)
    return _parse_json(content), model_used, tokens


class SEOgramWorkflow:
    """Otimiza caption Instagram para SEO local via Ollama."""

    def __init__(self, akasha_sink=None) -> None:
        self._sink = akasha_sink or AkashaSinkAdapter()

    def run(
        self,
        account_handle: str,
        raw_caption: str,
        dry_run: bool = False,
    ) -> SEOgramResult:
        ctx = RunContext.new(budget_usd=0.0)

        if not account_handle.strip():
            return SEOgramResult(
                run_id=ctx.run_id, success=False,
                account_handle=account_handle, raw_caption=raw_caption,
                error="empty_account_handle",
            )
        if not raw_caption.strip():
            return SEOgramResult(
                run_id=ctx.run_id, success=False,
                account_handle=account_handle, raw_caption=raw_caption,
                error="empty_caption",
            )

        if dry_run:
            parsed = dict(_DRY_RUN_RESULT)
            model_used = "dry_run"
            tokens_used = 0
        else:
            try:
                parsed, model_used, tokens_used = _call_ollama(account_handle, raw_caption)
            except Exception as exc:
                _logger.error("seogram[%s]: ollama error — %s", ctx.run_id, exc)
                return SEOgramResult(
                    run_id=ctx.run_id, success=False,
                    account_handle=account_handle, raw_caption=raw_caption,
                    error=str(exc),
                )

        optimized_hook = str(parsed.get("optimized_hook", "")).strip()
        hashtag_clusters = parsed.get("hashtag_clusters") or {}
        if not isinstance(hashtag_clusters, dict):
            hashtag_clusters = {}
        hashtags_raw = parsed.get("hashtags") or []
        hashtags = _to_list(hashtags_raw)[:30]
        try:
            keyword_density = float(parsed.get("keyword_density", 0.0))
        except (TypeError, ValueError):
            keyword_density = 0.0
        try:
            seo_score = int(parsed.get("seo_score", 0))
        except (TypeError, ValueError):
            seo_score = 0
        improvement_notes = _to_list(parsed.get("improvement_notes") or [])

        event = SinkEvent(
            event_type="seogram_optimized",
            source=ctx.run_id,
            payload={
                "run_id": ctx.run_id,
                "account_handle": account_handle,
                "seo_score": seo_score,
                "hashtag_count": len(hashtags),
                "keyword_density": round(keyword_density, 3),
                "model_used": model_used,
                "tokens_used": tokens_used,
                "dry_run": dry_run,
            },
        )
        self._sink.write_event(event)

        _logger.info(
            "seogram[%s]: %s — seo_score=%d hashtags=%d tokens=%d",
            ctx.run_id, account_handle, seo_score, len(hashtags), tokens_used,
        )

        return SEOgramResult(
            run_id=ctx.run_id,
            success=True,
            account_handle=account_handle,
            raw_caption=raw_caption,
            optimized_hook=optimized_hook,
            hashtag_clusters=hashtag_clusters,
            hashtags=hashtags,
            keyword_density=keyword_density,
            seo_score=seo_score,
            improvement_notes=improvement_notes,
            model_used=model_used,
            tokens_used=tokens_used,
            akasha_event_id=event.event_id,
        )
