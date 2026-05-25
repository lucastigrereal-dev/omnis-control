"""AgenciaPipeline — vídeo longo → clipes prontos numa pasta de entrega.

Camada 1 (Opus Clip): Whisper real → HookDetector (regex) → CutPlanGenerator
                       → FFmpegRenderer com preset → output/agencia/<perfil>/<data>/

dry_run=True  → manifests JSON, nenhuma chamada Whisper/FFmpeg.
dry_run=False → Whisper real + FFmpeg real.

Uso:
    from src.agencia.pipeline import AgenciaPipeline
    result = AgenciaPipeline(dry_run=False).run(Path("video.mp4"), perfil="lucastigrereal")
"""
from __future__ import annotations

import json
import logging
import re
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.video_studio.hooks import HookDetector
from src.video_studio.cut_plan import CutPlanGenerator, CutSegment
from src.video_studio.render_ffmpeg import FFmpegRenderer
from src.video_studio.render_presets import RenderPresets, RenderPreset
from src.video_studio.models import VideoSource, VideoSourceKind, TranscriptSegment

logger = logging.getLogger("omnis.agencia")

_OUTPUT_BASE = Path("output/agencia")

# Apenas letras, dígitos, _ e - — sem ponto, barra, dois-pontos ou espaço.
_PERFIL_SLUG_RE = re.compile(r"^[a-zA-Z0-9_-]+$")

# Modelo Whisper padrão — pode ser sobreposto via env WHISPER_MODEL_SIZE
_DEFAULT_WHISPER_MODEL = "small"  # tiny=rápido/impreciso, small=bom balanço, medium/large=melhor


@dataclass
class ClipResult:
    clip_id: str
    output_path: Path
    start_seconds: float
    end_seconds: float
    duration: float
    hook: str
    hook_score: float
    hook_reason: str
    dry_run: bool

    def to_dict(self) -> dict:
        return {
            "clip_id": self.clip_id,
            "path": str(self.output_path),
            "start": self.start_seconds,
            "end": self.end_seconds,
            "duration": round(self.duration, 2),
            "hook": self.hook,
            "hook_score": self.hook_score,
            "hook_reason": self.hook_reason,
            "dry_run": self.dry_run,
        }


@dataclass
class AgenciaResult:
    session_id: str
    output_dir: Path
    video_name: str
    perfil: str
    clips: list[ClipResult]
    transcript_segments: int
    hooks_found: int
    preset_name: str
    dry_run: bool
    elapsed_seconds: float
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "output_dir": str(self.output_dir),
            "video_name": self.video_name,
            "perfil": self.perfil,
            "clips": [c.to_dict() for c in self.clips],
            "clip_count": len(self.clips),
            "transcript_segments": self.transcript_segments,
            "hooks_found": self.hooks_found,
            "preset_name": self.preset_name,
            "dry_run": self.dry_run,
            "elapsed_seconds": round(self.elapsed_seconds, 2),
            "error": self.error,
        }

    def summary(self) -> str:
        lines = [
            f"session={self.session_id}  perfil={self.perfil}  preset={self.preset_name}",
            f"vídeo:   {self.video_name}",
            f"output:  {self.output_dir}",
            f"clipes:  {len(self.clips)} gerados  |  hooks encontrados: {self.hooks_found}  |  segmentos: {self.transcript_segments}",
            f"tempo:   {self.elapsed_seconds:.1f}s  |  dry_run={self.dry_run}",
        ]
        for i, c in enumerate(self.clips, 1):
            flag = ".manifest.json" if c.dry_run else ".mp4"
            lines.append(
                f"  clip {i:02d}: [{c.start_seconds:.1f}s -> {c.end_seconds:.1f}s] "
                f"{c.duration:.1f}s | {c.hook[:60]} | {c.output_path.name}"
            )
        if self.error:
            lines.append(f"ERRO: {self.error}")
        return "\n".join(lines)


class AgenciaPipeline:
    """Pipeline Camada 1: cortes inteligentes.

    Parâmetros:
        dry_run:              False = Whisper + FFmpeg reais.
        max_hooks:            Limite de hooks detectados por vídeo.
        transcription_adapter: Inject para testes — None usa Whisper real.
    """

    def __init__(
        self,
        dry_run: bool = True,
        max_hooks: int = 10,
        transcription_adapter=None,
    ) -> None:
        self.dry_run = dry_run
        self._hook_detector = HookDetector(max_hooks=max_hooks)
        self._cut_generator = CutPlanGenerator()
        self._renderer = FFmpegRenderer()
        self._transcription_adapter = transcription_adapter

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_perfil(perfil: str) -> None:
        """Rejeita qualquer valor que não seja um slug seguro [a-zA-Z0-9_-]."""
        if not _PERFIL_SLUG_RE.match(perfil):
            raise ValueError(
                f"perfil inválido {perfil!r} — use apenas letras, números, _ e - "
                "(sem /, \\, .., :, espaço)"
            )

    @staticmethod
    def _validate_output_dir(output_dir: Path) -> None:
        """Garante que o path resolvido fica dentro de _OUTPUT_BASE."""
        base = _OUTPUT_BASE.resolve()
        resolved = output_dir.resolve()
        try:
            resolved.relative_to(base)
        except ValueError:
            raise ValueError(
                f"output_dir {resolved} escapa de {base} — operação bloqueada por segurança"
            )

    def run(
        self,
        video_path: Path,
        perfil: str = "lucastigrereal",
        preset_name: str = "reel",
        target_duration: float = 30.0,
        max_clips: int = 5,
    ) -> AgenciaResult:
        """Roda o pipeline completo e devolve AgenciaResult com os clipes."""
        t0 = time.monotonic()
        session_id = str(uuid.uuid4())[:8]
        video_path = Path(video_path)

        self._validate_perfil(perfil)
        preset = self._resolve_preset(preset_name)
        output_dir = _OUTPUT_BASE / perfil / datetime.now().strftime("%Y-%m-%d") / video_path.stem
        self._validate_output_dir(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            "[agencia %s] video=%s perfil=%s preset=%s dry_run=%s",
            session_id, video_path.name, perfil, preset_name, self.dry_run,
        )

        try:
            # 1 — Transcrição
            segments = self._transcribe(video_path)
            logger.info("[agencia %s] %d segmentos transcritos", session_id, len(segments))

            # 2 — Detecção de hooks
            hooks = self._hook_detector.detect(segments)
            logger.info("[agencia %s] %d hooks detectados", session_id, len(hooks))
            hook_score_map = {h.hook_text: (h.score, h.rationale) for h in hooks}

            # 3 — Plano de cortes
            duration = segments[-1].end_seconds if segments else max(target_duration, 1.0)
            source = VideoSource.new(
                kind=VideoSourceKind.IMPORTED,
                uri_hint=str(video_path),
                duration_seconds=max(duration, 1.0),
            )
            cut_segments = self._cut_generator.generate(
                source, segments, hooks,
                target_duration=target_duration,
                platform="instagram",
            )[:max_clips]
            logger.info("[agencia %s] %d cortes planejados", session_id, len(cut_segments))

            # 4 — Renderização
            clips = self._render_clips(cut_segments, video_path, output_dir, preset, hook_score_map)

            result = AgenciaResult(
                session_id=session_id,
                output_dir=output_dir,
                video_name=video_path.name,
                perfil=perfil,
                clips=clips,
                transcript_segments=len(segments),
                hooks_found=len(hooks),
                preset_name=preset_name,
                dry_run=self.dry_run,
                elapsed_seconds=time.monotonic() - t0,
            )

        except Exception as exc:  # noqa: BLE001
            logger.error("[agencia %s] falha: %s", session_id, exc)
            result = AgenciaResult(
                session_id=session_id,
                output_dir=output_dir,
                video_name=video_path.name,
                perfil=perfil,
                clips=[],
                transcript_segments=0,
                hooks_found=0,
                preset_name=preset_name,
                dry_run=self.dry_run,
                elapsed_seconds=time.monotonic() - t0,
                error=str(exc),
            )

        # 5 — Manifesto na pasta de entrega
        manifest_path = output_dir / "manifest.json"
        manifest_path.write_text(
            json.dumps(result.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _transcribe(self, video_path: Path) -> list[TranscriptSegment]:
        """Retorna lista de TranscriptSegment. Adapter injetado ou Whisper real."""
        if self._transcription_adapter is not None:
            transcript = self._transcription_adapter.transcribe(
                str(video_path), duration_seconds=60.0
            )
            return transcript.segments

        if self.dry_run:
            from src.video_studio.transcription import MockTranscriptionAdapter
            mock = MockTranscriptionAdapter()
            return mock.transcribe("turismo natal", duration_seconds=60.0).segments

        # Whisper real — reutiliza o lazy loader do VideoProcessorLego
        from src.legos.video_processor_lego import VideoProcessorLego
        model = VideoProcessorLego._get_whisper_model()
        logger.info("[agencia] Whisper transcrevendo %s …", video_path.name)
        whisper_result = model.transcribe(str(video_path), language="pt")
        raw_segs = whisper_result.get("segments", [])
        logger.info("[agencia] Whisper retornou %d segmentos brutos", len(raw_segs))
        return self._whisper_to_segments(raw_segs)

    @staticmethod
    def _whisper_to_segments(raw_segs: list[dict]) -> list[TranscriptSegment]:
        """Converte dicts do Whisper em TranscriptSegment (com validação)."""
        out: list[TranscriptSegment] = []
        for seg in raw_segs:
            text = seg.get("text", "").strip()
            start = float(seg.get("start", 0.0))
            end = float(seg.get("end", start + 1.0))
            if not text or end <= start:
                continue
            confidence = max(0.0, min(1.0, 1.0 - float(seg.get("no_speech_prob", 0.0))))
            try:
                out.append(TranscriptSegment.new(
                    start_seconds=start,
                    end_seconds=end,
                    text=text,
                    confidence=confidence,
                ))
            except ValueError:
                logger.debug("[agencia] segmento ignorado: %s (%.2f→%.2f)", text[:30], start, end)
        return out

    def _render_clips(
        self,
        cut_segments: list[CutSegment],
        video_path: Path,
        output_dir: Path,
        preset: Optional[RenderPreset],
        hook_score_map: dict,
    ) -> list[ClipResult]:
        clips: list[ClipResult] = []
        for i, cs in enumerate(cut_segments, start=1):
            suffix = preset.output_suffix if preset else ""
            clip_path = output_dir / f"clip_{i:03d}{suffix}.mp4"

            has_filters = preset and (preset.scale_filter or preset.crop_filter)
            if has_filters:
                rendered = self._renderer.render_with_preset(
                    video_path, cs.start_seconds, cs.end_seconds, clip_path,
                    preset=preset, dry_run=self.dry_run,
                )
            else:
                rendered = self._renderer.render_cut(
                    video_path, cs.start_seconds, cs.end_seconds, clip_path,
                    dry_run=self.dry_run,
                )

            score, reason = hook_score_map.get(cs.hook, (0.0, cs.reason))
            clips.append(ClipResult(
                clip_id=cs.cut_id,
                output_path=rendered,
                start_seconds=cs.start_seconds,
                end_seconds=cs.end_seconds,
                duration=cs.duration,
                hook=cs.hook,
                hook_score=score,
                hook_reason=reason,
                dry_run=self.dry_run,
            ))
        return clips

    @staticmethod
    def _resolve_preset(name: str) -> Optional[RenderPreset]:
        mapping = {
            "reel": RenderPresets.REEL,
            "feed": RenderPresets.FEED_SQUARE,
            "story": RenderPresets.STORY,
            "thumbnail": RenderPresets.THUMBNAIL,
            "original": None,
        }
        return mapping.get(name.lower(), RenderPresets.REEL)
