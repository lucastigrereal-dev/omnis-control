"""HotelPitchWorkflow — gera pitch de collab personalizado para hotel via Ollama.

Onda 33 — integra com SDRPipelineWorkflow (output execute → input pitch).
Pipeline:
  1. validate  → prospect válido, score presente
  2. prompt    → monta contexto: segmento, tier, Instagram, localização, nível de personalização
  3. generate  → OllamaAdapter → pitch em PT-BR com assunto, abertura, proposta, prova social, CTA
  4. akasha    → evento hotel_pitch_generated
  5. retorna   → HotelPitchResult pronto para uso no outreach

Uso:
  scored_lead = sdr_pipeline_result.leads[0]   # HOT ou WARM
  result = HotelPitchWorkflow().run(scored_lead)
  print(result.subject_line)
  print(result.full_pitch)
"""
from __future__ import annotations

import json
import logging
import urllib.request
from dataclasses import dataclass, field
from typing import Any

from src.commercial_sdr.models import OpportunityScore, ProspectProfile, ScoreTier
from src.akasha_event_sink.adapter import AkashaSinkAdapter, FileAkashaSink
from src.akasha_event_sink.models import SinkEvent
from src.utils.run_context import RunContext

_logger = logging.getLogger("omnis.workflows.hotel_pitch")
_COST_LOCAL_PCT = 100

_OLLAMA_BASE = "http://localhost:11434"
_MODEL = "llama3.1:8b"

_SYSTEM_PROMPT = (
    "Você é especialista em parcerias de marketing para influenciadores de viagem no Brasil. "
    "Escreva pitches de collab em português, diretos, calorosos e com prova de valor real. "
    "Responda APENAS em JSON válido."
)

_USER_TEMPLATE = """Crie um pitch de collab para o influenciador Lucas Tigre (2.3M seguidores, 6 perfis Instagram).

Prospect:
- Empresa: {company_name}
- Contato: {contact_name}
- Segmento: {segment}
- Localização: {location}
- Instagram: {instagram}
- Score tier: {tier}
- Score composto: {composite:.2f}

Perfis do influenciador: @lucastigrereal (690K), @oinatalrn (630K), @agenteviajabrasil (452K), @afamiliatigrereal (320K), @oquecomernatalrn (249K), @natalaivoueu (240K).

Gere o pitch em JSON com:
- subject_line: assunto do DM/email (máx 80 chars)
- opening: abertura pessoal e calorosa (1-2 frases)
- proposal: o que Lucas oferece exatamente (2-3 itens concretos)
- social_proof: prova social relevante para este segmento (1 frase)
- cta: call to action específico (1 frase)
"""


@dataclass
class HotelPitchResult:
    run_id: str
    success: bool
    profile_id: str
    company_name: str
    tier: str
    composite_score: float
    subject_line: str = ""
    opening: str = ""
    proposal: str = ""
    social_proof: str = ""
    cta: str = ""
    model_used: str = ""
    tokens_used: int = 0
    akasha_event_id: str = ""
    cost_local_pct: int = _COST_LOCAL_PCT
    error: str | None = None

    @property
    def full_pitch(self) -> str:
        parts = [p for p in [self.opening, self.proposal, self.social_proof, self.cta] if p]
        return "\n\n".join(parts)

    @property
    def char_count(self) -> int:
        return len(self.full_pitch)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "success": self.success,
            "profile_id": self.profile_id,
            "company_name": self.company_name,
            "tier": self.tier,
            "composite_score": round(self.composite_score, 3),
            "subject_line": self.subject_line,
            "opening": self.opening,
            "proposal": self.proposal,
            "social_proof": self.social_proof,
            "cta": self.cta,
            "model_used": self.model_used,
            "tokens_used": self.tokens_used,
            "char_count": self.char_count,
            "akasha_event_id": self.akasha_event_id,
            "cost_local_pct": self.cost_local_pct,
            "error": self.error,
        }


def _call_ollama(prompt_user: str, timeout: int = 60) -> tuple[str, int]:
    """Chama Ollama diretamente. Retorna (raw_content, tokens_used)."""
    payload = json.dumps({
        "model": _MODEL,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": prompt_user},
        ],
        "response_format": {"type": "json_object"},
        "max_tokens": 600,
        "temperature": 0.65,
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


def _parse_pitch(raw: str) -> dict[str, str]:
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]

    def _to_str(v: object) -> str:
        if isinstance(v, list):
            return "\n".join(f"• {item}" for item in v)
        return str(v) if v is not None else ""

    try:
        d = json.loads(text)
        return {
            "subject_line": _to_str(d.get("subject_line", "")),
            "opening": _to_str(d.get("opening", "")),
            "proposal": _to_str(d.get("proposal", "")),
            "social_proof": _to_str(d.get("social_proof", "")),
            "cta": _to_str(d.get("cta", "")),
        }
    except (json.JSONDecodeError, ValueError):
        return {"subject_line": "", "opening": raw[:200], "proposal": "", "social_proof": "", "cta": ""}


class HotelPitchWorkflow:
    """Gera pitch de collab para hotel via Ollama local.

    dry_run=True retorna pitch template sem chamar o modelo.
    """

    def __init__(self, akasha_sink: AkashaSinkAdapter | None = None) -> None:
        self._sink = akasha_sink or FileAkashaSink()

    def run(
        self,
        prospect: ProspectProfile,
        score: OpportunityScore | None = None,
        dry_run: bool = False,
    ) -> HotelPitchResult:
        ctx = RunContext.new(budget_usd=0.0)

        def _err(code: str) -> HotelPitchResult:
            return HotelPitchResult(
                run_id=ctx.run_id,
                success=False,
                profile_id=prospect.profile_id,
                company_name=prospect.company_name,
                tier="unknown",
                composite_score=0.0,
                error=code,
            )

        if not prospect.profile_id:
            return _err("empty_profile_id")
        if not prospect.company_name:
            return _err("empty_company_name")

        tier_val = score.tier.value if score else "warm"
        composite = score.composite if score else 0.5
        instagram = prospect.instagram_handle or "(sem Instagram)"
        location = prospect.location or "Brasil"

        _logger.info("%s hotel_pitch.start company=%s tier=%s",
                     ctx.log_prefix(), prospect.company_name, tier_val)

        if dry_run:
            pitch = {
                "subject_line": f"Collab {prospect.company_name} × Lucas Tigre",
                "opening": f"Olá {prospect.contact_name}, vi {prospect.company_name} e adorei!",
                "proposal": "• Post Feed + Stories nos 3 perfis mais relevantes\n• Alcance orgânico de até 690K\n• Conteúdo autêntico, sem roteiro artificial",
                "social_proof": "Lucas já fez collabs com mais de 40 hotéis e pousadas no Nordeste.",
                "cta": "Podemos conversar esta semana para alinhar os detalhes?",
            }
            model_used = "mock/template"
            tokens_used = 0
        else:
            user_content = _USER_TEMPLATE.format(
                company_name=prospect.company_name,
                contact_name=prospect.contact_name or "Responsável",
                segment=prospect.segment,
                location=location,
                instagram=instagram,
                tier=tier_val.upper(),
                composite=composite,
            )
            try:
                raw, tokens_used = _call_ollama(user_content)
                pitch = _parse_pitch(raw)
                model_used = _MODEL
            except Exception as exc:
                _logger.error("%s hotel_pitch.llm_error: %s", ctx.log_prefix(), exc)
                return _err(f"llm_error:{type(exc).__name__}")

        event = SinkEvent(
            event_type="hotel_pitch_generated",
            source=ctx.run_id,
            payload={
                "profile_id": prospect.profile_id,
                "company_name": prospect.company_name,
                "tier": tier_val,
                "composite": round(composite, 3),
                "subject_line": pitch["subject_line"][:80],
                "model_used": model_used,
                "tokens_used": tokens_used,
                "dry_run": dry_run,
            },
        )
        self._sink.write_event(event)

        return HotelPitchResult(
            run_id=ctx.run_id,
            success=True,
            profile_id=prospect.profile_id,
            company_name=prospect.company_name,
            tier=tier_val,
            composite_score=composite,
            subject_line=pitch["subject_line"],
            opening=pitch["opening"],
            proposal=pitch["proposal"],
            social_proof=pitch["social_proof"],
            cta=pitch["cta"],
            model_used=model_used,
            tokens_used=tokens_used,
            akasha_event_id=event.event_id,
        )
