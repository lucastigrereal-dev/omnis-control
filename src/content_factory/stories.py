"""W095 — Stories Package model."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.content_factory.brief import ContentBrief


@dataclass
class StoryFrame:
    index: int
    title: str = ""
    image_description: str = ""
    overlay_text: str = ""
    sticker_type: str = ""  # poll, question, quiz, countdown, mention, link
    link_url: str = ""

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "title": self.title,
            "image_description": self.image_description,
            "overlay_text": self.overlay_text,
            "sticker_type": self.sticker_type,
            "link_url": self.link_url,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "StoryFrame":
        return cls(
            index=d["index"],
            title=d.get("title", ""),
            image_description=d.get("image_description", ""),
            overlay_text=d.get("overlay_text", ""),
            sticker_type=d.get("sticker_type", ""),
            link_url=d.get("link_url", ""),
        )


@dataclass
class StoriesPackage:
    package_id: str
    brief_id: str
    title: str = ""
    frames: list[StoryFrame] = field(default_factory=list)
    swipe_up_link: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    dry_run: bool = True

    @property
    def frame_count(self) -> int:
        return len(self.frames)

    def to_dict(self) -> dict:
        return {
            "package_id": self.package_id,
            "brief_id": self.brief_id,
            "title": self.title,
            "frames": [f.to_dict() for f in self.frames],
            "swipe_up_link": self.swipe_up_link,
            "frame_count": self.frame_count,
            "created_at": self.created_at,
            "dry_run": self.dry_run,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "StoriesPackage":
        pkg = cls(
            package_id=d["package_id"],
            brief_id=d.get("brief_id", ""),
            title=d.get("title", ""),
            swipe_up_link=d.get("swipe_up_link", ""),
            created_at=d.get("created_at", ""),
            dry_run=d.get("dry_run", True),
        )
        for f in d.get("frames", []):
            pkg.frames.append(StoryFrame.from_dict(f))
        return pkg

    def to_markdown(self) -> str:
        lines = [
            f"# Stories: {self.title}",
            f"**ID:** {self.package_id} | **Frames:** {self.frame_count}",
            "",
        ]
        for f in self.frames:
            lines.append(f"## Frame {f.index}: {f.title}")
            if f.image_description:
                lines.append(f"_Visual: {f.image_description}_")
            if f.overlay_text:
                lines.append(f"**Overlay:** {f.overlay_text}")
            if f.sticker_type:
                lines.append(f"**Sticker:** {f.sticker_type}")
            if f.link_url:
                lines.append(f"**Link:** {f.link_url}")
            lines.append("")
        if self.swipe_up_link:
            lines.append(f"**Swipe Up:** {self.swipe_up_link}")
        return "\n".join(lines)


class StoriesBuilder:
    """Deterministic Stories builder from a ContentBrief. No LLM, no API."""

    MIN_FRAMES = 4

    def build(self, brief: ContentBrief) -> StoriesPackage:
        import uuid

        link = brief.cta if "http" in (brief.cta or "") else ""

        frames = [
            StoryFrame(
                index=1,
                title="Teaser",
                image_description=f"Imagem misteriosa/curiosa sobre {brief.title}",
                overlay_text=f"Voce sabe o que e {brief.title}?",
                sticker_type="poll",
            ),
            StoryFrame(
                index=2,
                title="Contexto",
                image_description=f"Foto do local/produto {brief.title}",
                overlay_text=f"{brief.brand} tem algo especial...",
                sticker_type="",
            ),
            StoryFrame(
                index=3,
                title="Revelacao",
                image_description=f"Melhor foto de {brief.title}",
                overlay_text=f"E isso: {brief.title} com {brief.brand}",
                sticker_type="quiz",
            ),
            StoryFrame(
                index=4,
                title="CTA",
                image_description="Imagem com CTA e seta swipe-up",
                overlay_text=brief.cta or "Quer saber mais?",
                sticker_type="",
                link_url=link,
            ),
        ]

        return StoriesPackage(
            package_id=str(uuid.uuid4())[:8],
            brief_id=brief.brief_id,
            title=f"Stories: {brief.title}",
            frames=frames,
            swipe_up_link=link,
        )
