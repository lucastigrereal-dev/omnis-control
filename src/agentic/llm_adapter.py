"""LLMAdapter — Protocol + implementações para geração de legendas via LLM.

MockLLMAdapter: usa template determinístico, sem IO. Padrão em testes e dry_run.
LiteLLMAdapter: chama gateway LiteLLM (:4002) com modelo configurável via env var.
  - Retry automático (3 tentativas, backoff exponencial 1-10s) em erros transientes.
  - Budget guard via RunContext: verifica teto antes de chamar, registra custo após.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.utils.run_context import BudgetExceededError, RunContext
from src.utils.llm_tracer import llm_span, set_llm_span_attrs

_logger = logging.getLogger("omnis.llm_adapter")


# ── DTOs ─────────────────────────────────────────────────────────────────────

@dataclass
class CaptionPromptInput:
    account_handle: str
    objective: str
    format: str
    context_md: str
    similar_captions: list[str] = field(default_factory=list)
    max_chars: int = 2200


@dataclass
class CaptionLLMOutput:
    hook: str
    body: str
    cta: str
    hashtags: list[str]
    raw: str
    model_used: str
    tokens_used: int = 0


# ── Protocol ──────────────────────────────────────────────────────────────────

@runtime_checkable
class LLMAdapter(Protocol):
    def generate_caption(self, prompt: CaptionPromptInput) -> CaptionLLMOutput: ...


# ── Mock (testes + dry_run) ───────────────────────────────────────────────────

_HOOKS: dict[str, str] = {
    "alcance": "Você precisa conhecer esse lugar",
    "conversao": "Reservas abertas — mas por tempo limitado",
    "autoridade": "Depois de visitar dezenas de destinos, posso dizer:",
    "relacionamento": "Esse momento ficou guardado na memória",
}

_HASHTAGS: dict[str, list[str]] = {
    "oinatalrn": ["#natal", "#turismorn", "#visitenatal", "#riogrande", "#rnturismo"],
    "agenteviajabrasil": ["#viajebrasil", "#brasil", "#destinosbrasil", "#turismo", "#travel"],
    "oquecomernatalrn": ["#gastronomia", "#natal", "#restaurante", "#comida", "#foodrn"],
    "afamiliatigrereal": ["#familia", "#viagem", "#viajandocomfilhos", "#ferias", "#kids"],
    "lucastigrereal": ["#lifestyle", "#viagem", "#tigrereal", "#dicas", "#brasil"],
    "natalaivoueu": ["#natal", "#praias", "#nordeste", "#viagem", "#rn"],
}


class MockLLMAdapter:
    """Gerador determinístico para testes e dry_run. Sem IO externo."""

    model_used: str = "mock/deterministic"

    def generate_caption(self, prompt: CaptionPromptInput) -> CaptionLLMOutput:
        handle = prompt.account_handle.lstrip("@").lower()
        hook = _HOOKS.get(prompt.objective, "Descubra isso com a gente")
        body = "• Detalhes únicos do local\n• Experiência real\n• Por que vale a pena"
        cta = "Salva esse post e manda para quem vai adorar saber!"
        hashtags = _HASHTAGS.get(handle, ["#viagem", "#brasil", "#turismo"])[:5]
        raw = f"{hook}\n\n{body}\n\n{cta}"
        return CaptionLLMOutput(
            hook=hook,
            body=body,
            cta=cta,
            hashtags=hashtags,
            raw=raw,
            model_used=self.model_used,
            tokens_used=0,
        )


# ── LiteLLM (produção) ────────────────────────────────────────────────────────

_LITELLM_BASE = os.getenv("LITELLM_BASE_URL", "http://localhost:4002")
_DEFAULT_MODEL = os.getenv("OMNIS_LLM_MODEL", "gemini/gemini-2.5-flash")
# Custo estimado por 1 000 tokens (USD). 0 = sem rastreamento de custo.
_COST_PER_1K_TOKENS = float(os.getenv("OMNIS_COST_PER_1K_TOKENS", "0.0"))

_SYSTEM_PROMPT = (
    "Você é um especialista em copywriting para Instagram de viagens e gastronomia no Brasil. "
    "Escreva legendas autênticas, em português, com gancho emocional, corpo com valor real e CTA claro. "
    "Máximo {max_chars} caracteres no total."
)

_USER_TEMPLATE = (
    "Conta: {account}\n"
    "Objetivo: {objective}\n"
    "Formato: {format}\n"
    "Contexto de memória:\n{context_md}\n"
    "{similar_block}"
    "\nGere a legenda completa. Responda em JSON com as chaves: hook, body, cta, hashtags (lista)."
)


class LiteLLMAdapter:
    """Chama o gateway LiteLLM local para geração real de legendas.

    Retry automático em erros de rede (3 tentativas, backoff 1-10s).
    Budget guard via RunContext — verifica teto antes, registra custo após.
    """

    def __init__(
        self,
        model: str = _DEFAULT_MODEL,
        base_url: str = _LITELLM_BASE,
        run_context: RunContext | None = None,
    ) -> None:
        self.model = model
        self.base_url = base_url
        self._ctx = run_context

    def health_check(self) -> bool:
        """Retorna True se o gateway LiteLLM está respondendo."""
        import urllib.request
        import urllib.error
        try:
            with urllib.request.urlopen(f"{self.base_url}/health", timeout=3):
                return True
        except (urllib.error.URLError, OSError):
            return False

    @staticmethod
    def _parse_response(raw_content: str) -> tuple[str, str, str, list[str]]:
        """Extrai hook/body/cta/hashtags do JSON da resposta LLM.

        Retorna fallback de texto livre se o JSON for inválido.
        """
        import json
        try:
            parsed = json.loads(raw_content)
            return (
                parsed.get("hook", ""),
                parsed.get("body", ""),
                parsed.get("cta", ""),
                parsed.get("hashtags", []),
            )
        except (json.JSONDecodeError, KeyError):
            return raw_content[:120], raw_content, "", []

    def generate_caption(self, prompt: CaptionPromptInput) -> CaptionLLMOutput:
        prefix = self._ctx.log_prefix() if self._ctx else "[run:none]"
        _logger.info("%s generate_caption: model=%s account=%s", prefix, self.model, prompt.account_handle)

        # Budget guard: estima custo antes de chamar (max_tokens como proxy)
        if self._ctx and _COST_PER_1K_TOKENS > 0:
            estimated = (1024 / 1000) * _COST_PER_1K_TOKENS
            self._ctx.check_budget(estimated)

        result = self._call_with_retry(prompt)

        # Registra custo real após resposta
        if self._ctx and _COST_PER_1K_TOKENS > 0:
            actual_cost = (result.tokens_used / 1000) * _COST_PER_1K_TOKENS
            self._ctx.add_cost(actual_cost)
            _logger.info("%s cost=%.5f USD tokens=%d", prefix, actual_cost, result.tokens_used)

        return result

    @retry(
        retry=retry_if_exception_type(OSError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def _call_with_retry(self, prompt: CaptionPromptInput) -> CaptionLLMOutput:
        """Executa a chamada HTTP ao LiteLLM com retry e span OpenTelemetry."""
        import json
        import time
        import urllib.request

        similar_block = ""
        if prompt.similar_captions:
            examples = "\n---\n".join(prompt.similar_captions[:3])
            similar_block = f"Exemplos de legendas similares aprovadas:\n{examples}\n"

        user_content = _USER_TEMPLATE.format(
            account=prompt.account_handle,
            objective=prompt.objective,
            format=prompt.format,
            context_md=prompt.context_md,
            similar_block=similar_block,
        )
        system_content = _SYSTEM_PROMPT.format(max_chars=prompt.max_chars)

        payload = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content},
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": 1024,
        }).encode()

        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        run_id = self._ctx.run_id if self._ctx else ""

        with llm_span("llm.generate_caption", model=self.model, run_id=run_id) as (span, t0):
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())

            latency_ms = (time.time() - t0) * 1000
            tokens = data.get("usage", {}).get("total_tokens", 0)
            cost_usd = (tokens / 1000) * _COST_PER_1K_TOKENS if _COST_PER_1K_TOKENS > 0 else 0.0

            set_llm_span_attrs(
                span,
                model=self.model,
                tokens=tokens,
                latency_ms=latency_ms,
                cost_usd=cost_usd,
                run_id=run_id,
            )

        raw_content = data["choices"][0]["message"]["content"]
        hook, body, cta, hashtags = self._parse_response(raw_content)
        raw = f"{hook}\n\n{body}\n\n{cta}" if cta else f"{hook}\n\n{body}"

        return CaptionLLMOutput(
            hook=hook,
            body=body,
            cta=cta,
            hashtags=hashtags,
            raw=raw,
            model_used=self.model,
            tokens_used=tokens,
        )
