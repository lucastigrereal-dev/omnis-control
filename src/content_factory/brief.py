"""W091 — Content Brief Model for Content Factory."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class ContentBrief:
    """Canonical content brief — the single source of truth for content generation."""

    brief_id: str
    title: str
    brand: str = ""
    audience: str = ""
    objective: str = "alcance"  # alcance, autoridade, conversao, relacionamento
    platform: str = "instagram"
    format: str = "feed"  # feed, carousel, reels, stories
    pillar: str = ""  # educacional, entretenimento, vendas, autoridade
    tone: str = "conversational"  # conversational, formal, casual, inspirational
    keywords: list[str] = field(default_factory=list)
    cta: str = ""
    constraints: str = ""
    dry_run: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "brief_id": self.brief_id,
            "title": self.title,
            "brand": self.brand,
            "audience": self.audience,
            "objective": self.objective,
            "platform": self.platform,
            "format": self.format,
            "pillar": self.pillar,
            "tone": self.tone,
            "keywords": self.keywords,
            "cta": self.cta,
            "constraints": self.constraints,
            "dry_run": self.dry_run,
            "created_at": self.created_at,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ContentBrief":
        return cls(
            brief_id=d["brief_id"],
            title=d.get("title", ""),
            brand=d.get("brand", ""),
            audience=d.get("audience", ""),
            objective=d.get("objective", "alcance"),
            platform=d.get("platform", "instagram"),
            format=d.get("format", "feed"),
            pillar=d.get("pillar", ""),
            tone=d.get("tone", "conversational"),
            keywords=d.get("keywords", []),
            cta=d.get("cta", ""),
            constraints=d.get("constraints", ""),
            dry_run=d.get("dry_run", True),
            created_at=d.get("created_at", ""),
            notes=d.get("notes", ""),
        )

    def to_markdown(self) -> str:
        lines = [
            f"# Content Brief: {self.title}",
            f"**ID:** {self.brief_id}",
            f"**Brand:** {self.brand}",
            f"**Audience:** {self.audience}",
            f"**Objective:** {self.objective}",
            f"**Platform:** {self.platform}",
            f"**Format:** {self.format}",
            f"**Pillar:** {self.pillar}",
            f"**Tone:** {self.tone}",
            f"**Keywords:** {', '.join(self.keywords) if self.keywords else 'none'}",
            f"**CTA:** {self.cta}",
            f"**Constraints:** {self.constraints or 'none'}",
            f"**Dry Run:** {self.dry_run}",
            f"**Created:** {self.created_at}",
        ]
        if self.notes:
            lines.append(f"\n**Notes:** {self.notes}")
        return "\n".join(lines)
