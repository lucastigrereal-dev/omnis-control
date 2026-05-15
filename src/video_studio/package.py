"""W108 — Video-to-Content Package integrating with existing VideoPackage + Content Factory."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.video_studio.models import (
    HookCandidate,
    ReelFormat,
    TranscriptSegment,
    VideoPackage,
    VideoSource,
)
from src.video_studio.service import VideoStudioPlanner
from src.video_studio.assets import VideoAsset
from src.video_studio.transcription import VideoTranscript
from src.video_studio.hooks import HookDetector
from src.video_studio.cut_plan import CutSegment, CutPlanGenerator
from src.video_studio.captions import OnScreenCaptionBrief, CaptionBriefBuilder
from src.video_studio.cover import CoverBrief, CoverBriefBuilder


@dataclass
class VideoContentPackage:
    """High-level content package wrapping video analysis into exportable assets."""

    package_id: str
    asset: VideoAsset | None = None
    transcript: VideoTranscript | None = None
    hooks: list[HookCandidate] = field(default_factory=list)
    cut_segments: list[CutSegment] = field(default_factory=list)
    captions_brief: OnScreenCaptionBrief | None = None
    cover_brief: CoverBrief | None = None
    reel_package: VideoPackage | None = None  # existing VideoPackage
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    dry_run: bool = True

    @property
    def cut_count(self) -> int:
        return len(self.cut_segments)

    @property
    def hook_count(self) -> int:
        return len(self.hooks)

    def to_dict(self) -> dict:
        return {
            "package_id": self.package_id,
            "asset": self.asset.to_dict() if self.asset else None,
            "transcript": self.transcript.to_dict() if self.transcript else None,
            "hooks": [h.to_dict() for h in self.hooks],
            "cut_segments": [c.to_dict() for c in self.cut_segments],
            "captions_brief": self.captions_brief.to_dict() if self.captions_brief else None,
            "cover_brief": self.cover_brief.to_dict() if self.cover_brief else None,
            "reel_package": self.reel_package.to_dict() if self.reel_package else None,
            "cut_count": self.cut_count,
            "hook_count": self.hook_count,
            "notes": self.notes,
            "created_at": self.created_at,
            "dry_run": self.dry_run,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "VideoContentPackage":
        pkg = cls(
            package_id=d["package_id"],
            notes=d.get("notes", ""),
            created_at=d.get("created_at", ""),
            dry_run=d.get("dry_run", True),
        )
        if d.get("asset"):
            pkg.asset = VideoAsset.from_dict(d["asset"])
        if d.get("transcript"):
            pkg.transcript = VideoTranscript.from_dict(d["transcript"])
        for h in d.get("hooks", []):
            pkg.hooks.append(HookCandidate.from_dict(h))
        for c in d.get("cut_segments", []):
            pkg.cut_segments.append(CutSegment.from_dict(c))
        if d.get("captions_brief"):
            pkg.captions_brief = OnScreenCaptionBrief.from_dict(d["captions_brief"])
        if d.get("cover_brief"):
            pkg.cover_brief = CoverBrief.from_dict(d["cover_brief"])
        if d.get("reel_package"):
            pkg.reel_package = VideoPackage.from_dict(d["reel_package"])
        return pkg

    def to_markdown(self) -> str:
        lines = [
            f"# Video Content Package: {self.package_id}",
            f"**Hooks:** {self.hook_count} | **Cuts:** {self.cut_count}",
            f"**Created:** {self.created_at}",
            "",
        ]
        if self.asset:
            lines.append(self.asset.to_markdown())
            lines.append("")
        if self.transcript:
            lines.append(f"## Transcript — {self.transcript.segment_count} segments, {self.transcript.total_duration}s")
            lines.append("")
        if self.cut_segments:
            lines.append(CutPlanGenerator().export_markdown(self.cut_segments))
            lines.append("")
        if self.captions_brief:
            lines.append(self.captions_brief.to_markdown())
            lines.append("")
        if self.cover_brief:
            lines.append(self.cover_brief.to_markdown())
            lines.append("")
        return "\n".join(lines)


class VideoContentPackageBuilder:
    """Deterministic builder — pipeline from video asset to content package."""

    def __init__(self):
        self.planner = VideoStudioPlanner()
        self.hook_detector = HookDetector(max_hooks=10)
        self.cut_generator = CutPlanGenerator()
        self.caption_builder = CaptionBriefBuilder()
        self.cover_builder = CoverBriefBuilder()

    def build(
        self,
        asset: VideoAsset,
        transcript: VideoTranscript,
        target_duration: float = 30.0,
        platform: str = "instagram",
    ) -> VideoContentPackage:
        import uuid

        pkg = VideoContentPackage(
            package_id=str(uuid.uuid4())[:8],
            asset=asset,
            transcript=transcript,
        )

        pkg.hooks = self.hook_detector.detect(transcript.segments)

        if asset.source:
            pkg.cut_segments = self.cut_generator.generate(
                asset.source,
                transcript.segments,
                pkg.hooks,
                target_duration=target_duration,
                platform=platform,
            )

        segments_raw = [s.to_dict() for s in transcript.segments]
        pkg.captions_brief = self.caption_builder.build(
            segments_raw,
            source_id=asset.source.source_id if asset.source else "",
        )

        hook_text = pkg.hooks[0].hook_text if pkg.hooks else asset.filename
        pkg.cover_brief = self.cover_builder.build_from_hook(
            source_id=asset.source.source_id if asset.source else "",
            hook_text=hook_text,
            city=asset.city,
            platform=platform,
        )

        if asset.source and pkg.cut_segments:
            try:
                cut_plan = self.cut_generator.to_cut_plan(asset.source, pkg.cut_segments)
                reel_script = self.planner.build_reel_script(
                    asset.source, cut_plan, format=ReelFormat.SHORT, title=asset.filename
                )
                reel_pkg = VideoPackage.new(
                    source=asset.source,
                    cut_plan=cut_plan,
                    reel_script=reel_script,
                    notes="Dry-run video content package",
                )
                for h in pkg.hooks:
                    reel_pkg.add_hook(h)
                pkg.reel_package = reel_pkg
            except Exception:
                pass  # dry-run tolerates missing source/cuts

        return pkg
