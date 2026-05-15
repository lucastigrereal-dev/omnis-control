"""W106 — On-Screen Captions Brief wrapping CaptionOverlaySpec."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.video_studio.models import CaptionOverlaySpec, CaptionPosition, CaptionStyle


@dataclass
class CaptionLine:
    text: str
    start_seconds: float
    end_seconds: float
    emphasis: str = ""  # bold, italic, highlight, word-by-word
    style_hint: str = "bottom-white"

    @property
    def duration(self) -> float:
        return self.end_seconds - self.start_seconds

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "start_seconds": self.start_seconds,
            "end_seconds": self.end_seconds,
            "emphasis": self.emphasis,
            "style_hint": self.style_hint,
            "duration": self.duration,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CaptionLine":
        return cls(
            text=d["text"],
            start_seconds=d.get("start_seconds", 0),
            end_seconds=d.get("end_seconds", 0),
            emphasis=d.get("emphasis", ""),
            style_hint=d.get("style_hint", "bottom-white"),
        )


@dataclass
class OnScreenCaptionBrief:
    brief_id: str
    source_id: str = ""
    lines: list[CaptionLine] = field(default_factory=list)
    total_duration: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    dry_run: bool = True

    @property
    def line_count(self) -> int:
        return len(self.lines)

    def to_dict(self) -> dict:
        return {
            "brief_id": self.brief_id,
            "source_id": self.source_id,
            "lines": [l.to_dict() for l in self.lines],
            "line_count": self.line_count,
            "total_duration": self.total_duration,
            "created_at": self.created_at,
            "dry_run": self.dry_run,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "OnScreenCaptionBrief":
        brief = cls(
            brief_id=d["brief_id"],
            source_id=d.get("source_id", ""),
            total_duration=d.get("total_duration", 0.0),
            created_at=d.get("created_at", ""),
            dry_run=d.get("dry_run", True),
        )
        for l in d.get("lines", []):
            brief.lines.append(CaptionLine.from_dict(l))
        return brief

    def to_markdown(self) -> str:
        lines = [
            f"# On-Screen Captions Brief: {self.brief_id}",
            f"**Lines:** {self.line_count} | **Duration:** {self.total_duration}s",
            "",
            "| # | Start | End | Text | Emphasis | Style |",
            "|---|---|---|---|---|---|",
        ]
        for i, cl in enumerate(self.lines, 1):
            lines.append(
                f"| {i} | {cl.start_seconds:.1f}s | {cl.end_seconds:.1f}s | "
                f"{cl.text} | {cl.emphasis} | {cl.style_hint} |"
            )
        return "\n".join(lines)

    def to_caption_overlay_specs(self) -> list[CaptionOverlaySpec]:
        """Convert to existing CaptionOverlaySpec models."""
        specs: list[CaptionOverlaySpec] = []
        for cl in self.lines:
            position = CaptionPosition.BOTTOM if "bottom" in cl.style_hint else CaptionPosition.CENTER
            style = CaptionStyle.REGULAR
            if cl.emphasis == "bold":
                style = CaptionStyle.BOLD
            elif cl.emphasis == "highlight":
                style = CaptionStyle.HIGHLIGHT

            specs.append(CaptionOverlaySpec.new(
                text=cl.text,
                position=position,
                style=style,
                font_size_hint=48,
                color_hex="#FFFFFF",
                start_seconds=cl.start_seconds,
                end_seconds=cl.end_seconds,
                animation_hint="fade",
            ))
        return specs


class CaptionBriefBuilder:
    """Deterministic caption brief builder from transcript segments."""

    def build(self, segments: list[dict], source_id: str = "") -> OnScreenCaptionBrief:
        """Build from raw segment dicts [{text, start_seconds, end_seconds}, ...]."""
        import uuid

        brief = OnScreenCaptionBrief(
            brief_id=str(uuid.uuid4())[:8],
            source_id=source_id,
        )

        for seg in segments:
            text = seg.get("text", "")
            if not text.strip():
                continue
            start = seg.get("start_seconds", seg.get("start", 0))
            end = seg.get("end_seconds", seg.get("end", start + 3))

            line = CaptionLine(
                text=text,
                start_seconds=start,
                end_seconds=end,
                emphasis="bold" if len(text.split()) <= 5 else "",
                style_hint="bottom-white",
            )
            brief.lines.append(line)

        if brief.lines:
            brief.total_duration = brief.lines[-1].end_seconds - brief.lines[0].start_seconds
        return brief
