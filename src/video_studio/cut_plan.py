"""W105 — Cut Plan Generator extending existing CutPlan/CutInstruction."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.video_studio.models import (
    CutInstruction,
    CutPlan,
    CutType,
    HookCandidate,
    TranscriptSegment,
    VideoSource,
)


@dataclass
class CutSegment:
    """High-level cut segment for Reels/Shorts with hook and metadata."""

    cut_id: str
    start_seconds: float
    end_seconds: float
    hook: str = ""
    title: str = ""
    reason: str = ""
    platform: str = "instagram"
    target_duration: float = 30.0

    @property
    def duration(self) -> float:
        return self.end_seconds - self.start_seconds

    def to_dict(self) -> dict:
        return {
            "cut_id": self.cut_id,
            "start_seconds": self.start_seconds,
            "end_seconds": self.end_seconds,
            "hook": self.hook,
            "title": self.title,
            "reason": self.reason,
            "duration": self.duration,
            "platform": self.platform,
            "target_duration": self.target_duration,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CutSegment":
        return cls(
            cut_id=d["cut_id"],
            start_seconds=d.get("start_seconds", 0),
            end_seconds=d.get("end_seconds", 0),
            hook=d.get("hook", ""),
            title=d.get("title", ""),
            reason=d.get("reason", ""),
            platform=d.get("platform", "instagram"),
            target_duration=d.get("target_duration", 30.0),
        )


class CutPlanGenerator:
    """Deterministic cut plan generator for Reels/Shorts. Extends existing CutPlan."""

    def generate(
        self,
        source: VideoSource,
        segments: list[TranscriptSegment],
        hooks: list[HookCandidate],
        target_duration: float = 30.0,
        platform: str = "instagram",
    ) -> list[CutSegment]:
        """Generate cut segments based on hook positions and transcript timing."""
        import uuid

        if not segments or not hooks:
            return []

        cut_segments: list[CutSegment] = []
        hook_texts = {h.hook_text for h in hooks}

        for seg in segments:
            if seg.text not in hook_texts:
                continue
            duration = seg.duration
            if duration > target_duration:
                mid = seg.start_seconds + (duration / 2)
                half = target_duration / 2
                start = max(seg.start_seconds, mid - half)
                end = min(seg.end_seconds, mid + half)
                title = seg.text[:50]
            else:
                start = seg.start_seconds
                end = min(seg.end_seconds, start + target_duration)
                title = seg.text[:50]

            hook_match = next((h for h in hooks if h.hook_text == seg.text), None)
            reason = hook_match.rationale if hook_match else "segmento selecionado"

            cs = CutSegment(
                cut_id=str(uuid.uuid4())[:8],
                start_seconds=start,
                end_seconds=end,
                hook=seg.text,
                title=title,
                reason=reason,
                platform=platform,
                target_duration=target_duration,
            )
            cut_segments.append(cs)

            if len(cut_segments) >= 5:
                break

        cut_segments.sort(key=lambda c: c.start_seconds)
        return cut_segments

    def to_cut_plan(
        self,
        source: VideoSource,
        cut_segments: list[CutSegment],
    ) -> CutPlan:
        """Convert CutSegments to a CutPlan (integrates with existing models)."""
        plan = CutPlan.new(source_id=source.source_id)
        for cs in cut_segments:
            plan.add_cut(CutInstruction.new(
                start_seconds=cs.start_seconds,
                end_seconds=cs.end_seconds,
                cut_type=CutType.KEEP,
                label=cs.title,
            ))
        return plan

    def export_markdown(self, cut_segments: list[CutSegment]) -> str:
        lines = [
            "# Cut Plan",
            f"**Total Cuts:** {len(cut_segments)}",
            "",
            "| # | Start | End | Duration | Hook | Platform |",
            "|---|---|---|---|---|---|",
        ]
        for i, cs in enumerate(cut_segments, 1):
            lines.append(
                f"| {i} | {cs.start_seconds:.1f}s | {cs.end_seconds:.1f}s | "
                f"{cs.duration:.1f}s | {cs.hook[:40]} | {cs.platform} |"
            )
        return "\n".join(lines)
