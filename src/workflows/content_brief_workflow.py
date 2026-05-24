"""ContentBriefWorkflow — gera brief editorial completo via Ollama para pré-produção.

Onda 34 — dado topic + formato + objetivo, Ollama (llama3.1:8b) retorna:
  - angle:      ângulo editorial único e diferenciado
  - key_points: 3-5 pontos que o conteúdo deve cobrir
  - photo_tips: dicas específicas de captura para o formato
  - hook_ideas: 2-3 ideias de gancho para o início
  - caption_draft: rascunho de legenda curta (hook apenas)
  - research_qs: 2-3 perguntas que o criador deve responder antes de gravar

Uso:
  result = ContentBriefWorkflow().run(
      account_handle="@oinatalrn",
      topic="Roteiro 48h em Natal: o que ninguém te conta",
      format="CAROUSEL",
      objective="alcance",
  )
  print(result.angle)
  print(result.photo_tips)
"""
from __future__ import annotations

import json
import logging
import urllib.request
from dataclasses import dataclass, field
from typing import Any

from src.akasha_event_sink.adapter import AkashaSinkAdapter, FileAkashaSink
from src.akasha_event_sink.models import SinkEvent
from src.utils.run_context import RunContext

_logger = logging.getLogger("omnis.workflows.content_brief")
_COST_LOCAL_PCT = 100
_OLLAMA_BASE = "http://localhost:11434"
_MODEL = "llama3.1:8b"

_VALID_FORMATS = {"FEED", "REELS", "CAROUSEL", "STORIES"}

_SYSTEM_PROMPT = (
    "Você é um diretor de conteúdo para criadores de viagem e gastronomia no Brasil com 2M+ seguidores. "
    "Gere briefs editoriais concisos, práticos e com ângulos únicos. "
    "Responda APENAS em JSON válido."
)

_USER_TEMPLATE = """Crie um brief editorial para o criador Lucas Tigre.

Perfil: {account}
Tópico: {topic}
Formato: {format}
Objetivo: {objective}

Gere o brief em JSON com:
- angle: ângulo editorial único (1 frase impactante)
- key_points: lista de 3-5 pontos essenciais que o conteúdo deve cobrir
- photo_tips: dicas de captura/produção específicas para {format} (2-3 dicas)
- hook_ideas: lista de 2-3 ideias de gancho para o início do conteúdo
- caption_draft: rascunho curto da legenda (apenas o hook, max 100 chars)
- research_qs: lista de 2-3 perguntas que o criador deve responder antes de produzir
"""


@dataclass
class ContentBriefResult:
    run_id: str
    success: bool
    account_handle: str
    topic: str
    format: str
    objective: str
    angle: str = ""
    key_points: list[str] = field(default_factory=list)
    photo_tips: list[str] = field(default_factory=list)
    hook_ideas: list[str] = field(default_factory=list)
    caption_draft: str = ""
    research_qs: list[str] = field(default_factory=list)
    model_used: str = ""
    tokens_used: int = 0
    akasha_event_id: str = ""
    cost_local_pct: int = _COST_LOCAL_PCT
    error: str | None = None

    @property
    def is_complete(self) -> bool:
        return bool(self.angle and self.key_points and self.hook_ideas)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "success": self.success,
            "account_handle": self.account_handle,
            "topic": self.topic,
            "format": self.format,
            "objective": self.objective,
            "angle": self.angle,
            "key_points": self.key_points,
            "photo_tips": self.photo_tips,
            "hook_ideas": self.hook_ideas,
            "caption_draft": self.caption_draft,
            "research_qs": self.research_qs,
            "model_used": self.model_used,
            "tokens_used": self.tokens_used,
            "akasha_event_id": self.akasha_event_id,
            "cost_local_pct": self.cost_local_pct,
            "error": self.error,
        }


def _call_ollama(user_content: str, timeout: int = 120) -> tuple[str, int]:
    payload = json.dumps({
        "model": _MODEL,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "response_format": {"type": "json_object"},
        "max_tokens": 700,
        "temperature": 0.60,
    }).encode()

    req = urllib.request.Request(
        f"{_OLLAMA_BASE}/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read())

    raw = data["choices"][0]["message"]["content"]
    tokens = data.get("usage", {}).get("total_tokens", 0)
    return raw, tokens


def _to_list(v: object) -> list[str]:
    if isinstance(v, list):
        return [str(x) for x in v]
    if isinstance(v, str) and v:
        return [v]
    return []


def _parse_brief(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    try:
        d = json.loads(text)
        return {
            "angle": str(d.get("angle", "")),
            "key_points": _to_list(d.get("key_points", [])),
            "photo_tips": _to_list(d.get("photo_tips", [])),
            "hook_ideas": _to_list(d.get("hook_ideas", [])),
            "caption_draft": str(d.get("caption_draft", ""))[:120],
            "research_qs": _to_list(d.get("research_qs", [])),
        }
    except (json.JSONDecodeError, ValueError):
        return {
            "angle": raw[:100],
            "key_points": [], "photo_tips": [],
            "hook_ideas": [], "caption_draft": "",
            "research_qs": [],
        }


_DRY_RUN_BRIEF = {
    "angle": "O ângulo que ninguém explorou ainda neste destino",
    "key_points": ["Ponto 1: experiência única", "Ponto 2: dica prática", "Ponto 3: contexto local"],
    "photo_tips": ["Hora dourada para melhores fotos", "Perspectiva baixa valoriza o cenário"],
    "hook_ideas": ["'Nunca pensei encontrar isso em {topic}'", "'Isso mudou minha visão sobre o destino'"],
    "caption_draft": "Você vai se arrepender de não ter ido antes…",
    "research_qs": ["Qual a melhor época para visitar?", "Quais locais costumam ser fotogênicos?"],
}


class ContentBriefWorkflow:
    """Gera brief editorial para pré-produção de conteúdo.

    dry_run=True usa template estático (sem Ollama).
    dry_run=False chama llama3.1:8b local.
    """

    def __init__(self, akasha_sink: AkashaSinkAdapter | None = None) -> None:
        self._sink = akasha_sink or FileAkashaSink()

    def run(
        self,
        account_handle: str,
        topic: str,
        format: str = "FEED",
        objective: str = "alcance",
        dry_run: bool = False,
    ) -> ContentBriefResult:
        ctx = RunContext.new(budget_usd=0.0)

        def _err(code: str) -> ContentBriefResult:
            return ContentBriefResult(
                run_id=ctx.run_id, success=False,
                account_handle=account_handle, topic=topic,
                format=format, objective=objective, error=code,
            )

        if not account_handle.strip():
            return _err("empty_account_handle")
        if not topic.strip():
            return _err("empty_topic")
        if format.upper() not in _VALID_FORMATS:
            return _err(f"invalid_format:{format}")

        fmt = format.upper()
        obj = objective.lower()

        _logger.info("%s content_brief.start account=%s topic=%s fmt=%s",
                     ctx.log_prefix(), account_handle, topic[:40], fmt)

        if dry_run:
            brief = dict(_DRY_RUN_BRIEF)
            model_used = "mock/template"
            tokens_used = 0
        else:
            user_content = _USER_TEMPLATE.format(
                account=account_handle,
                topic=topic,
                format=fmt,
                objective=obj,
            )
            try:
                raw, tokens_used = _call_ollama(user_content)
                brief = _parse_brief(raw)
                model_used = _MODEL
            except Exception as exc:
                _logger.error("%s content_brief.llm_error: %s", ctx.log_prefix(), exc)
                return _err(f"llm_error:{type(exc).__name__}")

        event = SinkEvent(
            event_type="content_brief_generated",
            source=ctx.run_id,
            payload={
                "account_handle": account_handle,
                "topic": topic[:80],
                "format": fmt,
                "objective": obj,
                "angle_preview": brief["angle"][:60],
                "key_points_count": len(brief["key_points"]),
                "model_used": model_used,
                "tokens_used": tokens_used,
                "dry_run": dry_run,
            },
        )
        self._sink.write_event(event)

        return ContentBriefResult(
            run_id=ctx.run_id,
            success=True,
            account_handle=account_handle,
            topic=topic,
            format=fmt,
            objective=obj,
            angle=brief["angle"],
            key_points=brief["key_points"],
            photo_tips=brief["photo_tips"],
            hook_ideas=brief["hook_ideas"],
            caption_draft=brief["caption_draft"],
            research_qs=brief["research_qs"],
            model_used=model_used,
            tokens_used=tokens_used,
            akasha_event_id=event.event_id,
        )
