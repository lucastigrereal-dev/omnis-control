"""Mission Planner — generates structured MissionPlan from intent + request."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from src.mission_builder.models import MissionPlan
from src.mission_builder.intent import detect_intent
from src.mission_builder.errors import IntentUnknownError

# Account handle extraction: "para @handle" or "para handle"
_ACCOUNT_RE = re.compile(r'para\s+@?([\w]+)', re.IGNORECASE)
# Post count extraction: "10 posts", "20 posts"
_COUNT_RE = re.compile(r'\b(\d+)\s+posts?\b', re.IGNORECASE)

_INTENT_STEPS = {
    "carousel": [
        "1. Definir tema e objetivo da sequência",
        "2. Criar slides outline (título, corpo, CTA)",
        "3. Produzir legenda principal",
        "4. Selecionar ou criar assets visuais",
        "5. Exportar pacote offline",
        "6. Revisão humana e aprovação",
    ],
    "reels": [
        "1. Definir tema e duração alvo (até 90s)",
        "2. Criar shot list e roteiro de locução",
        "3. Gravar ou selecionar clipes",
        "4. Produzir legenda e hashtags",
        "5. Exportar pacote de roteiro",
        "6. Revisão humana e aprovação",
    ],
    "campaign": [
        "1. Definir tema geral e número de posts",
        "2. Criar calendário de publicação",
        "3. Gerar briefing por post",
        "4. Produzir legendas e assets",
        "5. Exportar pacote de campanha",
        "6. Revisão humana e aprovação",
    ],
    "post": [
        "1. Definir tema e objetivo do post",
        "2. Criar legenda com hook + corpo + CTA",
        "3. Selecionar ou criar asset visual",
        "4. Exportar pacote de post simples",
        "5. Revisão humana e aprovação",
    ],
    "story": [
        "1. Definir tema e duração (até 15s por frame)",
        "2. Criar storyboard simples",
        "3. Produzir texto para cada frame",
        "4. Selecionar assets",
        "5. Exportar pacote de stories",
        "6. Revisão humana e aprovação",
    ],
}

_INTENT_FORMAT = {
    "carousel": "carrossel",
    "reels": "reel",
    "campaign": "campanha",
    "post": "feed",
    "story": "stories",
    "unknown": "desconhecido",
}

_DEFAULT_SLOTS = {
    "carousel": 5,
    "reels": 1,
    "campaign": 10,
    "post": 1,
    "story": 3,
    "unknown": 1,
}


def _extract_account(text: str) -> str:
    m = _ACCOUNT_RE.search(text)
    return m.group(1).lower() if m else "afamiliatigrereal"


def _extract_slot_count(text: str, intent: str) -> int:
    m = _COUNT_RE.search(text)
    if m:
        n = int(m.group(1))
        return min(n, 100)
    return _DEFAULT_SLOTS.get(intent, 1)


def build_plan(
    request_text: str,
    account_handle: Optional[str] = None,
    objective: str = "engajamento",
    config_path: Optional[Path] = None,
    allow_unknown: bool = False,
) -> MissionPlan:
    """Build a MissionPlan from a free-text request.

    Raises IntentUnknownError if intent is 'unknown' and allow_unknown=False.
    """
    intent, deliverable, description = detect_intent(request_text, config_path=config_path)

    if intent == "unknown" and not allow_unknown:
        raise IntentUnknownError(
            f"Nao consegui detectar o tipo de conteudo em: '{request_text}'. "
            f"Tente mencionar: carrossel, reels, campanha, post simples, stories."
        )

    handle = account_handle or _extract_account(request_text)
    slots = _extract_slot_count(request_text, intent)
    steps = _INTENT_STEPS.get(intent, ["1. Definir objetivo", "2. Produzir conteudo", "3. Revisar"])
    format_ = _INTENT_FORMAT.get(intent, "desconhecido")

    return MissionPlan.new(
        request_text=request_text,
        intent=intent,
        deliverable=deliverable,
        description=description,
        account_handle=handle,
        format=format_,
        objective=objective,
        estimated_slots=slots,
        steps=steps,
    )
