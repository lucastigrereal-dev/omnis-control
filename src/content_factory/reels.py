"""W094 — Reel Script Package model."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.content_factory.brief import ContentBrief


@dataclass
class Scene:
    index: int
    description: str = ""
    narration: str = ""
    on_screen_text: str = ""
    b_roll_suggestion: str = ""
    duration_seconds: float = 3.0

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "description": self.description,
            "narration": self.narration,
            "on_screen_text": self.on_screen_text,
            "b_roll_suggestion": self.b_roll_suggestion,
            "duration_seconds": self.duration_seconds,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Scene":
        return cls(
            index=d["index"],
            description=d.get("description", ""),
            narration=d.get("narration", ""),
            on_screen_text=d.get("on_screen_text", ""),
            b_roll_suggestion=d.get("b_roll_suggestion", ""),
            duration_seconds=d.get("duration_seconds", 3.0),
        )


@dataclass
class ReelScriptPackage:
    package_id: str
    brief_id: str
    title: str = ""
    hook: str = ""
    scenes: list[Scene] = field(default_factory=list)
    cta: str = ""
    target_duration_seconds: float = 30.0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    dry_run: bool = True

    @property
    def total_duration(self) -> float:
        return sum(s.duration_seconds for s in self.scenes)

    @property
    def scene_count(self) -> int:
        return len(self.scenes)

    def to_dict(self) -> dict:
        return {
            "package_id": self.package_id,
            "brief_id": self.brief_id,
            "title": self.title,
            "hook": self.hook,
            "scenes": [s.to_dict() for s in self.scenes],
            "cta": self.cta,
            "target_duration_seconds": self.target_duration_seconds,
            "total_duration": self.total_duration,
            "scene_count": self.scene_count,
            "created_at": self.created_at,
            "dry_run": self.dry_run,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ReelScriptPackage":
        pkg = cls(
            package_id=d["package_id"],
            brief_id=d.get("brief_id", ""),
            title=d.get("title", ""),
            hook=d.get("hook", ""),
            cta=d.get("cta", ""),
            target_duration_seconds=d.get("target_duration_seconds", 30.0),
            created_at=d.get("created_at", ""),
            dry_run=d.get("dry_run", True),
        )
        for s in d.get("scenes", []):
            pkg.scenes.append(Scene.from_dict(s))
        return pkg

    def to_markdown(self) -> str:
        lines = [
            f"# Reel Script: {self.title}",
            f"**ID:** {self.package_id} | **Scenes:** {self.scene_count} | **Target:** {self.target_duration_seconds}s",
            "",
            f"## Hook (0-3s): {self.hook}",
            "",
        ]
        for s in self.scenes:
            lines.append(f"## Scene {s.index} ({s.duration_seconds}s)")
            lines.append(f"**Narration:** {s.narration}")
            if s.on_screen_text:
                lines.append(f"**On-Screen:** {s.on_screen_text}")
            if s.description:
                lines.append(f"_Visual: {s.description}_")
            if s.b_roll_suggestion:
                lines.append(f"_B-Roll: {s.b_roll_suggestion}_")
            lines.append("")
        lines.append(f"## CTA: {self.cta}")
        lines.append(f"_Total: {self.total_duration}s / Target: {self.target_duration_seconds}s_")
        return "\n".join(lines)


class ReelScriptBuilder:
    """Deterministic Reel script builder from a ContentBrief. No LLM, no API."""

    MIN_SCENES = 4
    TARGET_DURATION = 30.0

    def build(self, brief: ContentBrief) -> ReelScriptPackage:
        import uuid

        scenes = [
            Scene(
                index=1,
                description=f"Abertura impactante de {brief.title}",
                narration=f"Voce ja viveu {brief.title} assim?",
                on_screen_text=f"{brief.brand} apresenta",
                b_roll_suggestion="Drone ou plano cinematografico",
                duration_seconds=3.0,
            ),
            Scene(
                index=2,
                description="Mostrar o problema ou desejo",
                narration=f"Muita gente sonha com {brief.title} mas acha que e dificil.",
                on_screen_text="O sonho que parece distante",
                b_roll_suggestion="Close-up expressao ou contraste antes/depois",
                duration_seconds=5.0,
            ),
            Scene(
                index=3,
                description=f"Apresentar {brief.brand} como solucao",
                narration=f"A {brief.brand} tornou {brief.title} acessivel, simples e inesquecivel.",
                on_screen_text="A solucao existe",
                b_roll_suggestion="Mostrar produto/servico em acao, detalhes",
                duration_seconds=7.0,
            ),
            Scene(
                index=4,
                description="Climax — experiencia transformadora",
                narration=f"Olha so a experiencia completa de {brief.title} com a {brief.brand}:",
                on_screen_text="Olha isso!",
                b_roll_suggestion="Sequencia rapida de melhores momentos (fast cut)",
                duration_seconds=8.0,
            ),
            Scene(
                index=5,
                description="Depoimento ou prova social",
                narration="Quem veio antes ja esta vivendo isso. E amando.",
                on_screen_text="Eles ja estao la",
                b_roll_suggestion="Cliente feliz, reacao genuina",
                duration_seconds=5.0,
            ),
            Scene(
                index=6,
                description="CTA final com urgencia",
                narration=brief.cta or "Garanta sua experiencia agora. Corre que ainda da tempo!",
                on_screen_text="Link na bio / Arrasta pra cima",
                b_roll_suggestion="Texto CTA com fundo epico ou logo animado",
                duration_seconds=2.0,
            ),
        ]

        return ReelScriptPackage(
            package_id=str(uuid.uuid4())[:8],
            brief_id=brief.brief_id,
            title=f"Reel: {brief.title}",
            hook=(
                f"Voce ja pensou em {brief.title}?"
                if brief.objective == "alcance"
                else f"O segredo de {brief.title} que ninguem te conta"
                if brief.objective == "autoridade"
                else f"{brief.title} como voce nunca viu!"
            ),
            scenes=scenes,
            cta=brief.cta or "Arrasta pra cima e vem viver isso!",
            target_duration_seconds=self.TARGET_DURATION,
        )
