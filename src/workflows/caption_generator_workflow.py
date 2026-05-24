"""CaptionGeneratorWorkflow — gera legenda Instagram com Ollama local.

Onda 32 — único workflow com LLM real (custo zero, offline-first).
Pipeline:
  1. validate   → garante account_handle, topic, format não vazios
  2. generate   → OllamaAdapter → CaptionLLMOutput (hook/body/cta/hashtags)
  3. akasha     → evento caption_generated com run_id, account, model
  4. retorna    → CaptionGeneratorResult com legenda pronta

Uso:
  wf = CaptionGeneratorWorkflow()          # OllamaAdapter padrão
  result = wf.run("@oinatalrn", "Praia de Ponta Negra ao entardecer", "FEED", "alcance")
  print(result.full_caption)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from src.agentic.llm_adapter import CaptionPromptInput, LLMAdapter
from src.agentic.ollama_adapter import OllamaAdapter
from src.akasha_event_sink.adapter import AkashaSinkAdapter, FileAkashaSink
from src.akasha_event_sink.models import SinkEvent
from src.utils.run_context import RunContext

_logger = logging.getLogger("omnis.workflows.caption_generator")
_COST_LOCAL_PCT = 100  # Ollama roda local — zero custo externo

_VALID_FORMATS = {"FEED", "REELS", "CAROUSEL", "STORIES"}
_VALID_OBJECTIVES = {"alcance", "conversao", "autoridade", "relacionamento", "engajamento"}


@dataclass
class CaptionGeneratorResult:
    run_id: str
    success: bool
    account_handle: str
    topic: str
    format: str
    objective: str
    hook: str = ""
    body: str = ""
    cta: str = ""
    hashtags: list[str] = field(default_factory=list)
    raw_caption: str = ""
    model_used: str = ""
    tokens_used: int = 0
    akasha_event_id: str = ""
    cost_local_pct: int = _COST_LOCAL_PCT
    error: str | None = None

    @property
    def full_caption(self) -> str:
        parts = [p for p in [self.hook, self.body, self.cta] if p]
        tags = " ".join(self.hashtags)
        text = "\n\n".join(parts)
        return f"{text}\n\n{tags}".strip() if tags else text

    @property
    def char_count(self) -> int:
        return len(self.full_caption)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "success": self.success,
            "account_handle": self.account_handle,
            "topic": self.topic,
            "format": self.format,
            "objective": self.objective,
            "hook": self.hook,
            "body": self.body,
            "cta": self.cta,
            "hashtags": self.hashtags,
            "raw_caption": self.raw_caption,
            "model_used": self.model_used,
            "tokens_used": self.tokens_used,
            "char_count": self.char_count,
            "akasha_event_id": self.akasha_event_id,
            "cost_local_pct": self.cost_local_pct,
            "error": self.error,
        }


class CaptionGeneratorWorkflow:
    """Gera legenda Instagram via Ollama local.

    dry_run=True usa MockLLMAdapter (sem chamada real).
    dry_run=False (padrão) usa OllamaAdapter real.
    """

    def __init__(
        self,
        llm: LLMAdapter | None = None,
        akasha_sink: AkashaSinkAdapter | None = None,
    ) -> None:
        self._llm = llm
        self._sink = akasha_sink or FileAkashaSink()

    def _get_llm(self, dry_run: bool) -> LLMAdapter:
        if self._llm is not None:
            return self._llm
        if dry_run:
            from src.agentic.llm_adapter import MockLLMAdapter
            return MockLLMAdapter()
        return OllamaAdapter()

    def run(
        self,
        account_handle: str,
        topic: str,
        format: str = "FEED",
        objective: str = "alcance",
        context_md: str = "",
        dry_run: bool = False,
    ) -> CaptionGeneratorResult:
        ctx = RunContext.new(budget_usd=0.0)

        def _err(code: str) -> CaptionGeneratorResult:
            return CaptionGeneratorResult(
                run_id=ctx.run_id,
                success=False,
                account_handle=account_handle,
                topic=topic,
                format=format,
                objective=objective,
                error=code,
            )

        if not account_handle.strip():
            return _err("empty_account_handle")
        if not topic.strip():
            return _err("empty_topic")
        if format.upper() not in _VALID_FORMATS:
            return _err(f"invalid_format:{format}")

        fmt = format.upper()
        obj = objective.lower()

        _logger.info("%s caption_generator.start account=%s topic=%s",
                     ctx.log_prefix(), account_handle, topic)

        try:
            llm = self._get_llm(dry_run)
            prompt = CaptionPromptInput(
                account_handle=account_handle,
                objective=obj,
                format=fmt,
                context_md=topic if not context_md else f"{topic}\n{context_md}",
            )
            output = llm.generate_caption(prompt)
        except Exception as exc:
            _logger.error("%s caption_generator.llm_error: %s", ctx.log_prefix(), exc)
            return _err(f"llm_error:{type(exc).__name__}")

        event = SinkEvent(
            event_type="caption_generated",
            source=ctx.run_id,
            payload={
                "account_handle": account_handle,
                "topic": topic,
                "format": fmt,
                "objective": obj,
                "model_used": output.model_used,
                "tokens_used": output.tokens_used,
                "hook_preview": output.hook[:80],
                "char_count": len(output.raw),
                "dry_run": dry_run,
            },
        )
        self._sink.write_event(event)

        return CaptionGeneratorResult(
            run_id=ctx.run_id,
            success=True,
            account_handle=account_handle,
            topic=topic,
            format=fmt,
            objective=obj,
            hook=output.hook,
            body=output.body,
            cta=output.cta,
            hashtags=output.hashtags,
            raw_caption=output.raw,
            model_used=output.model_used,
            tokens_used=output.tokens_used,
            akasha_event_id=event.event_id,
        )
