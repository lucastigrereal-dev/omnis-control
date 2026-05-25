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
        if dry_run:
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

        if not self.is_ffmpeg_available():
            raise RuntimeError(
                "ffmpeg não encontrado — instale ffmpeg para usar --no-dry-run"
            )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start),
            "-to", str(end),
            "-i", str(video_path),
            "-c", "copy",
            str(output_path),
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return output_path

    def render_with_preset(
        self,
        video_path: Path,
        start: float,
        end: float,
        output_path: Path,
        preset,  # RenderPreset — duck-typed to avoid circular import
        dry_run: bool = True,
    ) -> Path:
        """Render a cut applying scale/crop/fps from a RenderPreset.

        dry_run=True → manifesto JSON (sem chamar FFmpeg).
        dry_run=False → FFmpeg real; levanta RuntimeError se indisponível ou falhar.
        """
        if dry_run:
            manifest = {
                "dry_run": True,
                "video_path": str(video_path),
                "start": start,
                "end": end,
                "output_path": str(output_path),
                "duration": round(end - start, 3),
                "preset_name": getattr(preset, "name", None),
            }
            manifest_path = output_path.with_suffix(".manifest.json")
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            return manifest_path

        if not self.is_ffmpeg_available():
            raise RuntimeError(
                "ffmpeg não encontrado — instale ffmpeg para usar --no-dry-run"
            )

        output_path.parent.mkdir(parents=True, exist_ok=True)

        crop = getattr(preset, "crop_filter", "")
        scale = getattr(preset, "scale_filter", "")
        vf_parts = [f for f in [crop, scale] if f]

        cmd = ["ffmpeg", "-y", "-ss", str(start), "-to", str(end), "-i", str(video_path)]

        if vf_parts:
            raw_codec = getattr(preset, "codec", "h264")
            codec_enc = {"h264": "libx264", "h265": "libx265"}.get(raw_codec, raw_codec)
            bitrate = getattr(preset, "bitrate", "5M")
            fps = getattr(preset, "fps", 30)
            cmd += ["-vf", ",".join(vf_parts), "-c:v", codec_enc, "-b:v", bitrate,
                    "-r", str(fps), "-c:a", "aac", "-b:a", "128k"]
        else:
            cmd += ["-c", "copy"]

        cmd.append(str(output_path))
        subprocess.run(cmd, check=True, capture_output=True)
        return output_path
