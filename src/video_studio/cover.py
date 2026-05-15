"""W107 — Cover Brief (thumbnail spec)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class CoverBrief:
    brief_id: str
    source_id: str = ""
    title: str = ""
    subtitle: str = ""
    visual_direction: str = ""
    subject: str = ""
    color_mood: str = ""  # warm, cool, vibrant, dark, light
    safe_text_area: str = "center-bottom"  # where text is safe to overlay
    platform: str = "instagram"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    dry_run: bool = True

    def to_dict(self) -> dict:
        return {
            "brief_id": self.brief_id,
            "source_id": self.source_id,
            "title": self.title,
            "subtitle": self.subtitle,
            "visual_direction": self.visual_direction,
            "subject": self.subject,
            "color_mood": self.color_mood,
            "safe_text_area": self.safe_text_area,
            "platform": self.platform,
            "created_at": self.created_at,
            "dry_run": self.dry_run,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CoverBrief":
        return cls(
            brief_id=d["brief_id"],
            source_id=d.get("source_id", ""),
            title=d.get("title", ""),
            subtitle=d.get("subtitle", ""),
            visual_direction=d.get("visual_direction", ""),
            subject=d.get("subject", ""),
            color_mood=d.get("color_mood", ""),
            safe_text_area=d.get("safe_text_area", "center-bottom"),
            platform=d.get("platform", "instagram"),
            created_at=d.get("created_at", ""),
            dry_run=d.get("dry_run", True),
        )

    def to_markdown(self) -> str:
        lines = [
            f"# Cover Brief: {self.brief_id}",
            f"**Title:** {self.title}",
            f"**Subtitle:** {self.subtitle}",
            f"**Subject:** {self.subject}",
            f"**Visual Direction:** {self.visual_direction}",
            f"**Color Mood:** {self.color_mood}",
            f"**Safe Text Area:** {self.safe_text_area}",
            f"**Platform:** {self.platform}",
        ]
        return "\n".join(lines)


class CoverBriefBuilder:
    """Deterministic cover brief builder. No image generation, no API."""

    COLOR_MOODS = {
        "turismo": "vibrant",
        "gastronomia": "warm",
        "hotel": "warm",
        "familia": "light",
        "aventura": "cool",
    }

    def build(
        self,
        source_id: str,
        title: str,
        tags: list[str] | None = None,
        city: str = "",
        platform: str = "instagram",
    ) -> CoverBrief:
        import uuid

        tags = tags or []
        mood = self._detect_mood(tags)
        location_str = f" em {city}" if city else ""

        return CoverBrief(
            brief_id=str(uuid.uuid4())[:8],
            source_id=source_id,
            title=title,
            subtitle=f"Descubra{location_str} — veja o video completo",
            visual_direction=f"Foto principal de {title}{location_str} com composicao central e alto contraste",
            subject=title,
            color_mood=mood,
            safe_text_area="center-bottom",
            platform=platform,
        )

    def build_from_hook(self, source_id: str, hook_text: str, city: str = "", platform: str = "instagram") -> CoverBrief:
        title_words = hook_text.split()[:5]
        title = " ".join(title_words).rstrip("?!")

        return self.build(
            source_id=source_id,
            title=title,
            city=city,
            platform=platform,
        )

    def _detect_mood(self, tags: list[str]) -> str:
        for tag in tags:
            tag_lower = tag.lower()
            for key, mood in self.COLOR_MOODS.items():
                if key in tag_lower:
                    return mood
        return "vibrant"
