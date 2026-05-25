"""FFmpegRenderer — renders video cuts, dry_run=True by default."""
from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def _subtitles_filter(srt_path: Path) -> str:
    """Converte Path para argumento subtitles= compatível com FFmpeg.

    No Windows o filtro exige forward slashes e ':' escapado como '\\:'.
    """
    p = str(srt_path.resolve())
    if os.name == "nt":
        p = p.replace("\\", "/")
    p = p.replace(":", "\\:")
    return f"subtitles={p}"


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
        srt_path: Optional[Path] = None,
        remove_silence: bool = False,
    ) -> Path:
        """Render a cut applying scale/crop/fps from a RenderPreset.

        dry_run=True  → manifesto JSON (sem chamar FFmpeg).
        dry_run=False → FFmpeg real; levanta RuntimeError se indisponível ou falhar.

        Camada 2:
          srt_path      — se fornecido e preset.burn_captions=True, queima legenda no vídeo.
          remove_silence — adiciona filtro silenceremove no áudio.
        """
        burn = srt_path is not None and getattr(preset, "burn_captions", False)

        if dry_run:
            manifest = {
                "dry_run": True,
                "video_path": str(video_path),
                "start": start,
                "end": end,
                "output_path": str(output_path),
                "duration": round(end - start, 3),
                "preset_name": getattr(preset, "name", None),
                "burn_captions": burn,
                "srt_path": str(srt_path) if srt_path else None,
                "remove_silence": remove_silence,
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

        # Camada 2: legenda queimada
        if burn:
            vf_parts.append(_subtitles_filter(srt_path))

        cmd = ["ffmpeg", "-y", "-ss", str(start), "-to", str(end), "-i", str(video_path)]

        if vf_parts:
            raw_codec = getattr(preset, "codec", "h264")
            codec_enc = {"h264": "libx264", "h265": "libx265"}.get(raw_codec, raw_codec)
            bitrate = getattr(preset, "bitrate", "5M")
            fps = getattr(preset, "fps", 30)
            cmd += ["-vf", ",".join(vf_parts), "-c:v", codec_enc, "-b:v", bitrate,
                    "-r", str(fps)]
        else:
            cmd += ["-c:v", "copy"]

        # Camada 2: corte de silêncio no áudio
        if remove_silence:
            cmd += ["-af", "silenceremove=stop_periods=-1:stop_duration=0.5:stop_threshold=-50dB",
                    "-c:a", "aac", "-b:a", "128k"]
        elif vf_parts:
            cmd += ["-c:a", "aac", "-b:a", "128k"]

        cmd.append(str(output_path))
        logger.info("[ffmpeg] cmd=%s", " ".join(cmd))
        subprocess.run(cmd, check=True, capture_output=True)
        return output_path
