"""AudioExtractor — extracts audio from video, dry_run=True by default."""
from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


class AudioExtractor:
    """Extract audio from a video file using ffmpeg (optional)."""

    @staticmethod
    def is_ffmpeg_available() -> bool:
        return shutil.which("ffmpeg") is not None

    def extract(
        self,
        video_path: Path,
        output_dir: Path,
        dry_run: bool = True,
    ) -> Path:
        output_path = output_dir / (video_path.stem + ".wav")

        if dry_run:
            return output_path

        if not self.is_ffmpeg_available():
            logger.warning("ffmpeg not found — returning mock path")
            return output_path

        output_dir.mkdir(parents=True, exist_ok=True)
        cmd = [
            "ffmpeg", "-y", "-i", str(video_path),
            "-vn", "-acodec", "copy", str(output_path),
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as exc:
            logger.warning("ffmpeg failed (%s) — returning mock path", exc)
        return output_path
