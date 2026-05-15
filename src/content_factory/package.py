"""W100 — Content Package Builder (E2E facade for Content Factory)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.content_factory.brief import ContentBrief
from src.content_factory.seogram import SEOgramCaption, SEOgramGenerator
from src.content_factory.carousel import CarouselPackage, CarouselBuilder
from src.content_factory.reels import ReelScriptPackage, ReelScriptBuilder
from src.content_factory.stories import StoriesPackage, StoriesBuilder
from src.content_factory.calendar import ContentCalendar, CalendarGenerator
from src.content_factory.approval_flow import ApprovalRequest, ApprovalFlow


@dataclass
class ContentPackage:
    """Single content package — wraps all generated assets for one brief."""

    package_id: str
    brief: ContentBrief | None = None
    caption: SEOgramCaption | None = None
    carousel: CarouselPackage | None = None
    reels: ReelScriptPackage | None = None
    stories: StoriesPackage | None = None
    approval: ApprovalRequest | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    dry_run: bool = True

    @property
    def generated_formats(self) -> list[str]:
        formats: list[str] = []
        if self.caption is not None:
            formats.append("caption")
        if self.carousel is not None:
            formats.append("carousel")
        if self.reels is not None:
            formats.append("reels")
        if self.stories is not None:
            formats.append("stories")
        return formats

    def to_dict(self) -> dict:
        return {
            "package_id": self.package_id,
            "brief": self.brief.to_dict() if self.brief else None,
            "caption": self.caption.to_dict() if self.caption else None,
            "carousel": self.carousel.to_dict() if self.carousel else None,
            "reels": self.reels.to_dict() if self.reels else None,
            "stories": self.stories.to_dict() if self.stories else None,
            "approval": self.approval.to_dict() if self.approval else None,
            "generated_formats": self.generated_formats,
            "created_at": self.created_at,
            "dry_run": self.dry_run,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ContentPackage":
        pkg = cls(
            package_id=d["package_id"],
            created_at=d.get("created_at", ""),
            dry_run=d.get("dry_run", True),
        )
        if d.get("brief"):
            pkg.brief = ContentBrief.from_dict(d["brief"])
        if d.get("caption"):
            pkg.caption = SEOgramCaption.from_dict(d["caption"])
        if d.get("carousel"):
            pkg.carousel = CarouselPackage.from_dict(d["carousel"])
        if d.get("reels"):
            pkg.reels = ReelScriptPackage.from_dict(d["reels"])
        if d.get("stories"):
            pkg.stories = StoriesPackage.from_dict(d["stories"])
        if d.get("approval"):
            pkg.approval = ApprovalRequest.from_dict(d["approval"])
        return pkg

    def to_markdown(self) -> str:
        lines = [
            f"# Content Package: {self.package_id}",
            f"**Generated:** {', '.join(self.generated_formats) or 'none'}",
            f"**Created:** {self.created_at}",
            "",
        ]
        if self.brief:
            lines.append(self.brief.to_markdown())
            lines.append("")
        if self.caption:
            lines.append(self.caption.to_markdown())
            lines.append("")
        if self.carousel:
            lines.append(self.carousel.to_markdown())
            lines.append("")
        if self.reels:
            lines.append(self.reels.to_markdown())
            lines.append("")
        if self.stories:
            lines.append(self.stories.to_markdown())
            lines.append("")
        if self.approval:
            lines.append(f"## Approval: {self.approval.current_stage}")
        return "\n".join(lines)


class ContentPackageBuilder:
    """Deterministic content package builder — facade over Content Factory modules."""

    def __init__(self):
        self.seogram = SEOgramGenerator()
        self.carousel = CarouselBuilder()
        self.reels = ReelScriptBuilder()
        self.stories = StoriesBuilder()
        self.calendar = CalendarGenerator()
        self.approval_flow = ApprovalFlow()

    def build_from_brief(self, brief: ContentBrief, formats: list[str] | None = None) -> ContentPackage:
        import uuid

        pkg = ContentPackage(
            package_id=str(uuid.uuid4())[:8],
            brief=brief,
        )

        if formats is None:
            formats = ["caption", "carousel", "reels", "stories"]

        if "caption" in formats:
            pkg.caption = self.seogram.generate(brief)

        if "carousel" in formats:
            pkg.carousel = self.carousel.build(brief)

        if "reels" in formats:
            pkg.reels = self.reels.build(brief)

        if "stories" in formats:
            pkg.stories = self.stories.build(brief)

        return pkg

    def build_with_approval(
        self,
        brief: ContentBrief,
        formats: list[str] | None = None,
        reviewer: str = "dry-run-bot",
    ) -> ContentPackage:
        pkg = self.build_from_brief(brief, formats)

        if pkg.caption:
            pkg.approval = self.approval_flow.create_request(
                content_id=pkg.caption.caption_id,
                content_type="caption",
            )
            self.approval_flow.advance_full_flow(pkg.approval, reviewer=reviewer)

        return pkg

    def build_batch(
        self,
        briefs: list[ContentBrief],
        formats: list[str] | None = None,
    ) -> list[ContentPackage]:
        return [self.build_from_brief(b, formats) for b in briefs]
