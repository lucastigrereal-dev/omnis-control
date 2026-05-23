"""LLMAdapter — Protocol + implementações para geração de legendas via LLM.

MockLLMAdapter: usa template determinístico, sem IO. Padrão em testes e dry_run.
LiteLLMAdapter: chama gateway LiteLLM (:4002) com modelo configurável via env var.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


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
    """Chama o gateway LiteLLM local para geração real de legendas."""

    def __init__(self, model: str = _DEFAULT_MODEL, base_url: str = _LITELLM_BASE) -> None:
        self.model = model
        self.base_url = base_url

    def generate_caption(self, prompt: CaptionPromptInput) -> CaptionLLMOutput:
        import json
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

        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())

        tokens = data.get("usage", {}).get("total_tokens", 0)
        raw_content = data["choices"][0]["message"]["content"]

        try:
            parsed = json.loads(raw_content)
            hook = parsed.get("hook", "")
            body = parsed.get("body", "")
            cta = parsed.get("cta", "")
            hashtags = parsed.get("hashtags", [])
        except (json.JSONDecodeError, KeyError):
            # fallback: trata resposta como texto livre
            hook = raw_content[:120]
            body = raw_content
            cta = ""
            hashtags = []

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
