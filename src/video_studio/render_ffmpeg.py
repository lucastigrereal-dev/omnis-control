"""FFmpegRenderer — renders video cuts, dry_run=True by default."""
from __future__ import annotations

import json
import logging
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


class FFmpegRenderer:
    """Render video cuts using ffmpeg (optional). dry_run writes a manifest JSON."""

    @staticmethod
    def is_ffmpeg_available() -> bool:
        return shutil.which("ffmpeg") is not None

    def render_cut(
        self,
        video_path: Path,
        start: float,
        end: float,
        output_path: Path,
        dry_run: bool = True,
    ) -> Path:
        if dry_run or not self.is_ffmpeg_available():
            if not dry_run:
                logger.warning("ffmpeg not found — falling back to dry_run manifest")
            manifest = {
                "dry_run": True,
                "video_path": str(video_path),
                "start": start,
                "end": end,
                "output_path": str(output_path),
                "duration": round(end - start, 3),
            }
            manifest_path = output_path.with_suffix(".manifest.json")
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            return manifest_path

        output_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start),
            "-to", str(end),
            "-i", str(video_path),
            "-c", "copy",
            str(output_path),
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as exc:
            logger.warning("ffmpeg render failed (%s) — falling back to manifest", exc)
            return self.render_cut(video_path, start, end, output_path, dry_run=True)

        return output_path
