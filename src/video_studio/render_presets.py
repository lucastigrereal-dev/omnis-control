"""Render presets for multi-aspect-ratio video output (9:16, 1:1, 16:9)."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Optional


class AspectTarget(str, Enum):
    PORTRAIT_9_16 = "9:16"
    SQUARE_1_1 = "1:1"
    LANDSCAPE_16_9 = "16:9"


@dataclass
class RenderPreset:
    name: str
    aspect: AspectTarget
    width: int
    height: int
    fps: int = 30
    codec: str = "h264"
    bitrate: str = "5M"
    burn_captions: bool = True
    scale_filter: str = ""
    crop_filter: str = ""
    output_suffix: str = ""

    def __post_init__(self):
        if not self.output_suffix:
            self.output_suffix = f"_{self.width}x{self.height}"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["aspect"] = self.aspect.value
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "RenderPreset":
        aspect = d.get("aspect", "16:9")
        if isinstance(aspect, str):
            aspect = AspectTarget(aspect)
        return cls(
            name=d.get("name", ""),
            aspect=aspect,
            width=d.get("width", 1080),
            height=d.get("height", 1920),
            fps=d.get("fps", 30),
            codec=d.get("codec", "h264"),
            bitrate=d.get("bitrate", "5M"),
            burn_captions=d.get("burn_captions", True),
            scale_filter=d.get("scale_filter", ""),
            crop_filter=d.get("crop_filter", ""),
            output_suffix=d.get("output_suffix", ""),
        )


class RenderPresets:
    """Factory of standard render presets for Instagram."""

    REEL = RenderPreset(
        name="Instagram Reel",
        aspect=AspectTarget.PORTRAIT_9_16,
        width=1080,
        height=1920,
        bitrate="6M",
        scale_filter="scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
        output_suffix="_reel_1080x1920",
    )

    FEED_SQUARE = RenderPreset(
        name="Instagram Feed Square",
        aspect=AspectTarget.SQUARE_1_1,
        width=1080,
        height=1080,
        bitrate="5M",
        crop_filter="crop=min(iw\\,ih):min(iw\\,ih)",
        scale_filter="scale=1080:1080",
        output_suffix="_feed_1080x1080",
    )

    FEED_LANDSCAPE = RenderPreset(
        name="Instagram Feed Landscape",
        aspect=AspectTarget.LANDSCAPE_16_9,
        width=1920,
        height=1080,
        bitrate="8M",
        output_suffix="_feed_1920x1080",
    )

    STORY = RenderPreset(
        name="Instagram Story",
        aspect=AspectTarget.PORTRAIT_9_16,
        width=1080,
        height=1920,
        bitrate="4M",
        scale_filter="scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
        output_suffix="_story_1080x1920",
    )

    THUMBNAIL = RenderPreset(
        name="Thumbnail/Cover",
        aspect=AspectTarget.SQUARE_1_1,
        width=1080,
        height=1080,
        fps=1,
        bitrate="1M",
        burn_captions=False,
        output_suffix="_thumb_1080x1080",
    )

    ALL: list[RenderPreset] = [REEL, FEED_SQUARE, FEED_LANDSCAPE, STORY, THUMBNAIL]

    @classmethod
    def for_aspect(cls, aspect: AspectTarget) -> list[RenderPreset]:
        return [p for p in cls.ALL if p.aspect == aspect]

    @classmethod
    def default_set(cls) -> list[RenderPreset]:
        """Standard Instagram pack: reel + feed square + thumbnail."""
        return [cls.REEL, cls.FEED_SQUARE, cls.THUMBNAIL]

    @classmethod
    def all_dicts(cls) -> list[dict]:
        return [p.to_dict() for p in cls.ALL]

    @classmethod
    def get(cls, name: str) -> Optional[RenderPreset]:
        for p in cls.ALL:
            if p.name == name:
                return p
        return None
