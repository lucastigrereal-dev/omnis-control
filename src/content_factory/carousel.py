"""W093 — Carousel Package model."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.content_factory.brief import ContentBrief


@dataclass
class CarouselSlide:
    index: int
    title: str = ""
    content: str = ""
    image_description: str = ""
    overlay_text: str = ""

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "title": self.title,
            "content": self.content,
            "image_description": self.image_description,
            "overlay_text": self.overlay_text,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CarouselSlide":
        return cls(
            index=d["index"],
            title=d.get("title", ""),
            content=d.get("content", ""),
            image_description=d.get("image_description", ""),
            overlay_text=d.get("overlay_text", ""),
        )


@dataclass
class CarouselPackage:
    package_id: str
    brief_id: str
    title: str = ""
    slides: list[CarouselSlide] = field(default_factory=list)
    cta_final: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    dry_run: bool = True

    @property
    def slide_count(self) -> int:
        return len(self.slides)

    def to_dict(self) -> dict:
        return {
            "package_id": self.package_id,
            "brief_id": self.brief_id,
            "title": self.title,
            "slides": [s.to_dict() for s in self.slides],
            "cta_final": self.cta_final,
            "created_at": self.created_at,
            "dry_run": self.dry_run,
            "slide_count": self.slide_count,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CarouselPackage":
        pkg = cls(
            package_id=d["package_id"],
            brief_id=d.get("brief_id", ""),
            title=d.get("title", ""),
            cta_final=d.get("cta_final", ""),
            created_at=d.get("created_at", ""),
            dry_run=d.get("dry_run", True),
        )
        for s in d.get("slides", []):
            pkg.slides.append(CarouselSlide.from_dict(s))
        return pkg

    def to_markdown(self) -> str:
        lines = [
            f"# Carousel: {self.title}",
            f"**ID:** {self.package_id} | **Slides:** {self.slide_count}",
            "",
        ]
        for s in self.slides:
            lines.append(f"## Slide {s.index}: {s.title}")
            lines.append(s.content)
            if s.image_description:
                lines.append(f"_Visual: {s.image_description}_")
            if s.overlay_text:
                lines.append(f"**Overlay:** {s.overlay_text}")
            lines.append("")
        lines.append(f"## CTA Final: {self.cta_final}")
        return "\n".join(lines)


class CarouselBuilder:
    """Deterministic carousel builder from a ContentBrief. No LLM, no API."""

    MIN_SLIDES = 5

    def build(self, brief: ContentBrief) -> CarouselPackage:
        import uuid

        slides = [
            CarouselSlide(
                index=1,
                title="Hook",
                content=f"Voce ja pensou em {brief.title}?",  # noqa
                image_description=f"Foto principal de {brief.title}",
                overlay_text=f"{brief.brand}: {brief.title}",
            ),
            CarouselSlide(
                index=2,
                title="O Problema",
                content=f"Muita gente nao sabe por onde comecar quando se trata de {brief.title}.",
                image_description="Pessoa confusa ou pesquisando",
                overlay_text="O desafio",
            ),
            CarouselSlide(
                index=3,
                title="A Solucao",
                content=f"{brief.brand} resolve isso com excelencia. Aqui esta como funciona:",
                image_description=f"Foto do produto/servico {brief.title}",
                overlay_text="A solucao que faltava",
            ),
            CarouselSlide(
                index=4,
                title="Beneficios",
                content=f"1. Qualidade garantida\n2. Atendimento excepcional\n3. Experiencia transformadora",
                image_description="Infografico com beneficios",
                overlay_text="Por que escolher",
            ),
            CarouselSlide(
                index=5,
                title="Resultado",
                content=f"Quem experimenta {brief.title} com {brief.brand} nunca mais quer outra coisa.",
                image_description="Cliente feliz / antes e depois",
                overlay_text="O resultado fala por si",
            ),
            CarouselSlide(
                index=6,
                title="CTA",
                content=brief.cta or "Garanta sua experiencia agora!",
                image_description="Imagem com CTA e contato",
                overlay_text="Nao perca essa oportunidade",
            ),
        ]

        return CarouselPackage(
            package_id=str(uuid.uuid4())[:8],
            brief_id=brief.brief_id,
            title=f"Carrossel: {brief.title}",
            slides=slides,
            cta_final=brief.cta or "Fale com a gente agora mesmo!",
        )
