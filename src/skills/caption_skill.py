"""Caption generation skill — prompt templates for Instagram caption creation."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


CAPTION_SYSTEM_PROMPT = """Você é um criador de conteúdo para Instagram especializado em viagem, gastronomia e família.

Regras:
1. Hook forte na primeira linha (pergunta, afirmação polêmica ou curiosidade)
2. Texto envolvente, tom pessoal e autêntico
3. 3-5 hashtags estratégicas no final (misturar grandes + nicho)
4. Call-to-action genuíno (pergunta, "salva", "compartilha")
5. Máximo 150 palavras
6. Português natural, sem firulas corporativas
7. Incluir 2-3 emojis relevantes (não exagerar)"""


@dataclass
class CaptionRequest:
    topic: str
    page: str = "@lucastigrereal"
    tone: str = "autêntico"
    target_audience: str = "viajantes e famílias"
    max_words: int = 150
    include_hashtags: bool = True
    include_cta: bool = True

    def to_dict(self) -> dict:
        return {
            "topic": self.topic,
            "page": self.page,
            "tone": self.tone,
            "target_audience": self.target_audience,
            "max_words": self.max_words,
            "include_hashtags": self.include_hashtags,
            "include_cta": self.include_cta,
        }


@dataclass
class CaptionResult:
    caption: str
    topic: str
    page: str
    generated_at: str = field(default_factory=_now_iso)
    model_used: str = ""
    hook: str = ""
    hashtags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "caption": self.caption,
            "topic": self.topic,
            "page": self.page,
            "generated_at": self.generated_at,
            "model_used": self.model_used,
            "hook": self.hook,
            "hashtags": self.hashtags,
        }

    def save(self, path: str) -> None:
        import json
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def from_llm_response(cls, content: str, request: CaptionRequest, model_used: str = "") -> "CaptionResult":
        lines = content.strip().split("\n")
        hook = lines[0] if lines else ""
        hashtags = [l.strip() for l in lines if l.strip().startswith("#")]
        return cls(
            caption=content.strip(),
            topic=request.topic,
            page=request.page,
            model_used=model_used,
            hook=hook,
            hashtags=hashtags,
        )


def build_caption_prompt(request: CaptionRequest) -> str:
    """Build the user prompt for caption generation."""
    parts = [
        f"Crie uma legenda para Instagram sobre: {request.topic}",
        f"Perfil: {request.page}",
        f"Tom: {request.tone}",
        f"Público: {request.target_audience}",
        f"Máximo de {request.max_words} palavras.",
    ]
    if request.include_hashtags:
        parts.append("Inclua 3-5 hashtags relevantes ao final.")
    if request.include_cta:
        parts.append("Termine com um call-to-action (pergunta ou incentivo para salvar/compartilhar).")
    return "\n".join(parts)


def build_full_prompt(request: CaptionRequest) -> dict:
    """Build system + user prompt for the LLM call."""
    return {
        "system": CAPTION_SYSTEM_PROMPT,
        "user": build_caption_prompt(request),
    }
