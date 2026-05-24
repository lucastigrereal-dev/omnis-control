"""OllamaAdapter — gera legendas Instagram via Ollama local (custo zero).

Compatível com a interface LLMAdapter (mesmo Protocol do litellm_adapter).
Chama http://localhost:11434/v1/chat/completions diretamente.
"""
from __future__ import annotations

import json
import logging
import urllib.request
from dataclasses import dataclass

from src.agentic.llm_adapter import CaptionLLMOutput, CaptionPromptInput

_logger = logging.getLogger("omnis.ollama_adapter")

_OLLAMA_BASE = "http://localhost:11434"
_DEFAULT_MODEL = "llama3.1:8b"

_SYSTEM_PROMPT = (
    "Você é especialista em copywriting para Instagram de viagens e gastronomia no Brasil. "
    "Escreva legendas autênticas em português, com gancho emocional, corpo com valor real e CTA claro. "
    "Responda APENAS em JSON válido."
)

_USER_TEMPLATE = (
    "Perfil: {account}\n"
    "Tópico: {topic}\n"
    "Formato: {format}\n"
    "Objetivo: {objective}\n"
    "{context_block}"
    "Gere a legenda. JSON com chaves: hook (str), body (str), cta (str), hashtags (lista de strings, 5-8 itens)."
)


class OllamaAdapter:
    """Chama Ollama local para geração de legendas. Sem custo, sem rede externa."""

    def __init__(self, model: str = _DEFAULT_MODEL, base_url: str = _OLLAMA_BASE) -> None:
        self.model = model
        self.model_used = model
        self.base_url = base_url

    def health_check(self) -> bool:
        try:
            with urllib.request.urlopen(f"{self.base_url}/api/tags", timeout=3):
                return True
        except (urllib.error.URLError, OSError):
            return False

    @staticmethod
    def _parse_response(raw: str) -> tuple[str, str, str, list[str]]:
        try:
            # Strip markdown fences if present
            text = raw.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            d = json.loads(text)
            return (
                str(d.get("hook", "")),
                str(d.get("body", "")),
                str(d.get("cta", "")),
                [str(h) for h in d.get("hashtags", [])],
            )
        except (json.JSONDecodeError, KeyError, ValueError):
            # Fallback: return raw as body
            return "", raw[:300], "", []

    def generate_caption(self, prompt: CaptionPromptInput) -> CaptionLLMOutput:
        _logger.info("ollama.generate_caption: model=%s account=%s", self.model, prompt.account_handle)

        context_block = ""
        if prompt.context_md.strip():
            context_block = f"Contexto adicional:\n{prompt.context_md.strip()}\n\n"

        user_content = _USER_TEMPLATE.format(
            account=prompt.account_handle,
            topic=prompt.context_md or prompt.account_handle,
            format=prompt.format,
            objective=prompt.objective,
            context_block=context_block,
        )

        payload = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": 800,
            "temperature": 0.7,
        }).encode()

        req = urllib.request.Request(
            f"{self.base_url}/v1/chat/completions",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())

        raw_content = data["choices"][0]["message"]["content"]
        tokens = data.get("usage", {}).get("total_tokens", 0)
        hook, body, cta, hashtags = self._parse_response(raw_content)

        _logger.info("ollama.done: tokens=%d hook_len=%d", tokens, len(hook))

        return CaptionLLMOutput(
            hook=hook,
            body=body,
            cta=cta,
            hashtags=hashtags,
            raw=raw_content,
            model_used=self.model,
            tokens_used=tokens,
        )
