"""VideoProcessorLego — implementação do contrato VideoProcessor.

Usa:
- Whisper (já instalado) para transcrição
- FFmpegRenderer (já em video_studio/) para cortes
- dry_run=True por padrão — produz manifesto/transcrição sem modificar arquivos

Regras OMNIS:
- 1 tarefa pesada por vez (Whisper carrega modelo na RAM)
- Approval gate antes de publicação/envio
- health_check() verifica whisper + ffmpeg
"""
from __future__ import annotations

import logging
import os
import shutil
import threading
from pathlib import Path

from src.interfaces.video_processor import VideoProcessor, VideoSpec, VideoResult
from src.video_studio.render_ffmpeg import FFmpegRenderer

_logger = logging.getLogger("omnis.legos.video")

# 1 operação pesada por vez (Whisper consome RAM)
_VIDEO_SEMAPHORE = threading.Semaphore(1)

_PUBLISH_KEYWORDS = frozenset({
    "publicar", "publish", "upload", "postar", "post",
    "enviar", "send", "share", "compartilhar",
})


def _requires_publish_approval(goal: str) -> bool:
    return any(kw in goal.lower() for kw in _PUBLISH_KEYWORDS)


class VideoProcessorLego:
    """Implementação do Protocol VideoProcessor.

    Whisper para transcrição + FFmpegRenderer para cortes.
    Carrega o modelo Whisper sob demanda (lazy) — nunca na importação.
    """

    _whisper_model = None
    _whisper_lock = threading.Lock()

    def health_check(self) -> bool:
        """Retorna True se whisper e ffmpeg estão disponíveis."""
        try:
            import whisper  # noqa: F401
            has_whisper = True
        except ImportError:
            has_whisper = False
        has_ffmpeg = shutil.which("ffmpeg") is not None
        return has_whisper and has_ffmpeg

    def execute(self, spec: VideoSpec) -> VideoResult:
        """Processa vídeo de acordo com spec.goal."""
        if not spec.dry_run and _requires_publish_approval(spec.goal):
            _logger.warning("[video] APPROVAL REQUIRED for goal: '%s'", spec.goal[:80])
            return VideoResult(
                success=False, output="", files_created=[],
                dry_run=spec.dry_run, error="approval_required",
                artifacts={"approval_required": True, "goal": spec.goal},
            )

        goal = spec.goal.lower()

        if "transcri" in goal or "transcrev" in goal:
            return self._transcribe(spec)
        elif "cut" in goal or "corte" in goal:
            return self._cut(spec)
        elif "audio" in goal:
            return self._extract_audio(spec)
        else:
            return VideoResult(
                success=False, output="", files_created=[],
                dry_run=spec.dry_run,
                error=f"goal desconhecido: '{spec.goal}'. Use: transcribe, cut, extract_audio",
            )

    def _transcribe(self, spec: VideoSpec) -> VideoResult:
        """Transcreve vídeo/áudio usando Whisper."""
        if spec.dry_run:
            _logger.info("[video] DRY transcribe: %s", spec.video_path)
            return VideoResult(
                success=True,
                output=f"[dry_run] Transcrição planejada para: {spec.video_path}",
                files_created=[],
                dry_run=True,
                artifacts={"mode": "dry_run", "language": spec.language},
            )

        acquired = _VIDEO_SEMAPHORE.acquire(timeout=120)
        if not acquired:
            return VideoResult(
                success=False, output="", files_created=[],
                dry_run=False, error="video_semaphore_timeout",
            )

        try:
            import whisper
            model = self._get_whisper_model()
            _logger.info("[video] Transcribing: %s", spec.video_path)
            result = model.transcribe(spec.video_path, language=spec.language)
            text = result.get("text", "").strip()
            segments = result.get("segments", [])

            out_path = os.path.join(spec.output_dir, Path(spec.video_path).stem + "_transcript.txt")
            Path(spec.output_dir).mkdir(parents=True, exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(text)

            return VideoResult(
                success=True,
                output=text[:500],
                files_created=[out_path],
                dry_run=False,
                artifacts={
                    "segments": len(segments),
                    "language": result.get("language", spec.language),
                    "transcript_path": out_path,
                },
            )
        except Exception as e:
            _logger.error("[video] transcribe failed: %s", e)
            return VideoResult(
                success=False, output="", files_created=[],
                dry_run=False, error=str(e),
            )
        finally:
            _VIDEO_SEMAPHORE.release()

    def _cut(self, spec: VideoSpec) -> VideoResult:
        """Corta trecho de vídeo usando FFmpegRenderer."""
        renderer = FFmpegRenderer()
        video = Path(spec.video_path)
        out = Path(spec.output_dir) / f"{video.stem}_cut.mp4"

        result_path = renderer.render_cut(
            video_path=video,
            start=spec.start_seconds,
            end=spec.end_seconds or spec.start_seconds + 30,
            output_path=out,
            dry_run=spec.dry_run,
        )
        return VideoResult(
            success=True,
            output=f"Cut: {spec.start_seconds}s → {spec.end_seconds}s",
            files_created=[str(result_path)],
            dry_run=spec.dry_run,
            artifacts={"output_path": str(result_path)},
        )

    def _extract_audio(self, spec: VideoSpec) -> VideoResult:
        """Extrai áudio de vídeo via FFmpeg."""
        if spec.dry_run:
            return VideoResult(
                success=True,
                output=f"[dry_run] Extração de áudio planejada: {spec.video_path}",
                files_created=[],
                dry_run=True,
            )

        out_path = os.path.join(spec.output_dir, Path(spec.video_path).stem + "_audio.mp3")
        Path(spec.output_dir).mkdir(parents=True, exist_ok=True)

        import subprocess
        result = subprocess.run(
            ["ffmpeg", "-y", "-i", spec.video_path, "-q:a", "0", "-map", "a", out_path],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            return VideoResult(
                success=False, output="", files_created=[],
                dry_run=False, error=result.stderr[-300:],
            )
        return VideoResult(
            success=True,
            output=f"Áudio extraído: {out_path}",
            files_created=[out_path],
            dry_run=False,
        )

    @classmethod
    def _get_whisper_model(cls, model_size: str = "tiny"):
        """Lazy load do modelo Whisper — tiny = ~150MB RAM."""
        with cls._whisper_lock:
            if cls._whisper_model is None:
                import whisper
                _logger.info("[video] Loading Whisper model '%s'...", model_size)
                cls._whisper_model = whisper.load_model(model_size)
        return cls._whisper_model
