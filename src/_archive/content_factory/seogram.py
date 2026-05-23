"""W092 — SEOgram Caption Generator contract."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.content_factory.brief import ContentBrief


@dataclass
class SEOgramCaption:
    caption_id: str
    brief_id: str
    hook: str = ""
    paragraph_1: str = ""
    paragraph_2: str = ""
    paragraph_3: str = ""
    cta: str = ""
    hashtags: list[str] = field(default_factory=list)
    keywords_used: list[str] = field(default_factory=list)
    approval_status: str = "draft"  # draft, approved, rejected
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def full_caption(self) -> str:
        parts = [self.hook, "", self.paragraph_1, "", self.paragraph_2]
        if self.paragraph_3:
            parts.extend(["", self.paragraph_3])
        parts.extend(["", self.cta, "", " ".join(self.hashtags)])
        return "\n".join(parts)

    def to_dict(self) -> dict:
        return {
            "caption_id": self.caption_id,
            "brief_id": self.brief_id,
            "hook": self.hook,
            "paragraph_1": self.paragraph_1,
            "paragraph_2": self.paragraph_2,
            "paragraph_3": self.paragraph_3,
            "cta": self.cta,
            "hashtags": self.hashtags,
            "keywords_used": self.keywords_used,
            "approval_status": self.approval_status,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SEOgramCaption":
        return cls(
            caption_id=d["caption_id"],
            brief_id=d.get("brief_id", ""),
            hook=d.get("hook", ""),
            paragraph_1=d.get("paragraph_1", ""),
            paragraph_2=d.get("paragraph_2", ""),
            paragraph_3=d.get("paragraph_3", ""),
            cta=d.get("cta", ""),
            hashtags=d.get("hashtags", []),
            keywords_used=d.get("keywords_used", []),
            approval_status=d.get("approval_status", "draft"),
            created_at=d.get("created_at", ""),
        )

    def to_markdown(self) -> str:
        lines = [
            f"# SEOgram Caption: {self.caption_id}",
            "",
            f"**Hook:** {self.hook}",
            "",
            self.paragraph_1,
            "",
            self.paragraph_2,
            "",
            self.paragraph_3 if self.paragraph_3 else "",
            "",
            f"**CTA:** {self.cta}",
            "",
            f"**Hashtags:** {' '.join(self.hashtags)}",
        ]
        return "\n".join(lines)


class SEOgramGenerator:
    """Deterministic SEOgram caption generator from a ContentBrief. No LLM, no API."""

    HOOK_TEMPLATES = {
        "alcance": "Descubra {title} como nunca antes!",
        "autoridade": "O guia definitivo de {title} que ninguem te contou",
        "conversao": "Economize em {title} com essa dica exclusiva",
        "relacionamento": "Voce tambem ama {title}? Vem comigo!",
    }

    PARAGRAPH_TEMPLATES = {
        "alcance": "Se voce busca {title}, prepare-se para uma experiencia incrivel. {brand} traz o melhor para voce aproveitar cada momento ao maximo.",
        "autoridade": "Depois de testar {title} em diversas situacoes, posso afirmar: isso muda tudo. A {brand} entrega qualidade consistente.",
        "conversao": "Oportunidade unica: {title} com condicoes especiais. Garanta o seu antes que acabe. A {brand} preparou algo imperdivel.",
        "relacionamento": "Fala pessoal! Hoje vou compartilhar minha experiencia com {title}. A {brand} me surpreendeu demais!",
    }

    HASHTAG_POOLS: dict[str, list[str]] = {
        "turismo": ["#turismo", "#viagem", "#turismobrasil", "#viagemdossonhos"],
        "hotel": ["#hotel", "#hospedagem", "#luxo", "#resort"],
        "gastronomia": ["#gastronomia", "#comida", "#restaurante", "#foodie"],
        "familia": ["#familia", "#viagemfamilia", "#diversao", "#ferias"],
        "default": ["#omnis", "#conteudo", "#brasil", "#dica"],
    }

    def generate(self, brief: ContentBrief) -> SEOgramCaption:
        import uuid
        objective = brief.objective if brief.objective in self.HOOK_TEMPLATES else "alcance"
        hook = self.HOOK_TEMPLATES[objective].format(title=brief.title, brand=brief.brand)
        p1 = self.PARAGRAPH_TEMPLATES[objective].format(title=brief.title, brand=brief.brand)

        niche = self._detect_niche(brief.keywords)
        hashtags = self.HASHTAG_POOLS.get(niche, self.HASHTAG_POOLS["default"])[:]

        p2 = f"Sabe o que diferencia {brief.title}? Os detalhes. {brief.brand} pensou em tudo para voce ter a melhor experiencia possivel."
        p3 = f"E tem mais: quem segue {brief.brand} sempre fica sabendo primeiro. Fique de olho para nao perder as novidades!"

        return SEOgramCaption(
            caption_id=str(uuid.uuid4())[:8],
            brief_id=brief.brief_id,
            hook=hook,
            paragraph_1=p1,
            paragraph_2=p2,
            paragraph_3=p3,
            cta=brief.cta or "Salve esse post para consultar depois!",
            hashtags=hashtags + [f"#{k}" for k in brief.keywords[:3] if not k.startswith("#")],
            keywords_used=brief.keywords[:5],
            approval_status="draft",
        )

    def _detect_niche(self, keywords: list[str]) -> str:
        text = " ".join(keywords).lower()
        if any(w in text for w in ["turismo", "viagem", "praia", "destino", "passeio"]):
            return "turismo"
        if any(w in text for w in ["hotel", "hospedagem", "resort", "pousada"]):
            return "hotel"
        if any(w in text for w in ["gastronomia", "restaurante", "comida", "chef"]):
            return "gastronomia"
        if any(w in text for w in ["familia", "crianca", "filho", "pais"]):
            return "familia"
        return "default"
