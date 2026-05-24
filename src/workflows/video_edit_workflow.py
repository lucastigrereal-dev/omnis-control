"""VideoEditWorkflow — molde ponta a ponta: vídeo → transcrição → legenda → akasha.

Wires existing OMNIS pieces without adding new algorithms:
  - RunContext (Onda 7)    → run_id único + teto de custo
  - VideoProcessorLego     → Whisper transcreve, FFmpeg corta
  - AkashaSinkAdapter      → persiste evento com run_id no payload
  - cost_local_pct = 100   → Whisper roda sempre local, zero custo cloud

Pipeline do workflow:
  1. transcribe   → texto completo via VideoProcessorLego
  2. build_srt    → formata SRT a partir do texto (utility, sem ML)
  3. akasha write → evento gravado com run_id + preview da legenda
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.utils.run_context import RunContext
from src.interfaces.video_processor import VideoSpec, VideoResult
from src.legos.video_processor_lego import VideoProcessorLego
from src.akasha_event_sink.adapter import AkashaSinkAdapter, FileAkashaSink
from src.akasha_event_sink.models import SinkEvent

_logger = logging.getLogger("omnis.workflows.video_edit")

# Whisper é 100% local — custo cloud zero
_COST_LOCAL_PCT = 100


def _secs_to_srt(secs: float) -> str:
    h = int(secs // 3600)
    m = int((secs % 3600) // 60)
    s = secs % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")


def _build_srt(transcript: str, segment_count: int = 0) -> str:
    """Constrói SRT mínimo a partir do texto transcrito.

    dry_run / sem texto real: retorna placeholder de 1 segmento.
    Com texto: divide em sentenças e atribui timestamps heurísticos
    (3s por segmento) — sem ML, só formatação de string.
    """
    if not transcript or "[dry_run]" in transcript:
        return "1\n00:00:00,000 --> 00:00:10,000\n[dry_run — legenda placeholder]\n"

    sentences = [s.strip() for s in transcript.replace("\n", " ").split(".") if s.strip()]
    if not sentences:
        return "1\n00:00:00,000 --> 00:00:05,000\n[sem conteúdo]\n"

    lines = []
    for i, sent in enumerate(sentences[:60], 1):
        start = _secs_to_srt(float((i - 1) * 3))
        end = _secs_to_srt(float(i * 3))
        lines.append(f"{i}\n{start} --> {end}\n{sent}.\n")
    return "\n".join(lines)


@dataclass
class VideoEditResult:
    """Resultado consolidado do workflow de edição de vídeo."""

    run_id: str
    success: bool
    video_path: str = ""
    transcript: str = ""
    srt: str = ""
    files_created: list[str] = field(default_factory=list)
    akasha_event_id: str = ""
    dry_run: bool = True
    cost_local_pct: int = _COST_LOCAL_PCT
    error: str | None = None
    artifacts: dict[str, Any] = field(default_factory=dict)

    @property
    def segment_count(self) -> int:
        return int(self.artifacts.get("segments", 0))

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "success": self.success,
            "video_path": self.video_path,
            "transcript_chars": len(self.transcript),
            "srt_chars": len(self.srt),
            "segment_count": self.segment_count,
            "files_created": self.files_created,
            "akasha_event_id": self.akasha_event_id,
            "dry_run": self.dry_run,
            "cost_local_pct": self.cost_local_pct,
            "error": self.error,
            "artifacts": self.artifacts,
        }


class VideoEditWorkflow:
    """Workflow ponta a ponta: vídeo → transcrição → legenda → akasha.

    Injeção de dependências para facilitar testes:
      lego          → VideoProcessorLego (default: instância padrão)
      akasha_sink   → AkashaSinkAdapter (default: FileAkashaSink dry_run=True)
    """

    def __init__(
        self,
        lego: VideoProcessorLego | None = None,
        akasha_sink: AkashaSinkAdapter | None = None,
        output_dir: str = "output/video/",
        akasha_dir: str = "output/akasha/video/",
        budget_usd: float = 0.0,
    ) -> None:
        self._lego = lego or VideoProcessorLego()
        self._sink = akasha_sink or FileAkashaSink(target_dir=akasha_dir, dry_run=True)
        self._output_dir = output_dir
        self._budget_usd = budget_usd

    def run(
        self,
        video_path: str,
        language: str = "pt",
        dry_run: bool = True,
    ) -> VideoEditResult:
        """Executa o pipeline completo para um arquivo de vídeo.

        Args:
            video_path: Caminho do vídeo a processar.
            language: Idioma para transcrição Whisper (default: "pt").
            dry_run: True → retorna plano sem carregar Whisper nem criar arquivos.
        """
        ctx = RunContext.new(budget_usd=self._budget_usd)
        _logger.info(
            "%s VideoEditWorkflow.run: video='%s', lang=%s, dry_run=%s",
            ctx.log_prefix(), video_path, language, dry_run,
        )

        # Passo 1 — Transcrever
        spec = VideoSpec(
            video_path=video_path,
            goal="transcrever",
            dry_run=dry_run,
            output_dir=self._output_dir,
            language=language,
            extra={"run_id": ctx.run_id},
        )
        video_result = self._lego.execute(spec)

        if not video_result.success:
            _logger.warning("%s transcription failed: %s", ctx.log_prefix(), video_result.error)
            return VideoEditResult(
                run_id=ctx.run_id,
                success=False,
                video_path=video_path,
                dry_run=dry_run,
                error=video_result.error,
            )

        transcript = video_result.output
        segments = video_result.artifacts.get("segments", 0)
        language_detected = video_result.artifacts.get("language", language)
        _logger.info(
            "%s transcription OK — %d chars, %d segments, lang=%s",
            ctx.log_prefix(), len(transcript), segments, language_detected,
        )

        # Passo 2 — Gerar legenda SRT (string formatting, sem ML)
        srt = _build_srt(transcript, segment_count=segments)
        _logger.info("%s SRT built — %d chars", ctx.log_prefix(), len(srt))

        # Passo 3 — Gravar no akasha
        event = SinkEvent(
            event_type="video_edit_completed",
            source=ctx.run_id,
            payload={
                "run_id": ctx.run_id,
                "video_path": video_path,
                "transcript": transcript,
                "transcript_chars": len(transcript),
                "segments": segments,
                "language": language_detected,
                "srt_preview": srt[:300],
                "cost_local_pct": _COST_LOCAL_PCT,
                "files_created": video_result.files_created,
                "dry_run": dry_run,
            },
        )
        written = self._sink.write_event(event)
        _logger.info("%s akasha write: event_id=%s, ok=%s", ctx.log_prefix(), event.event_id, written)

        return VideoEditResult(
            run_id=ctx.run_id,
            success=True,
            video_path=video_path,
            transcript=transcript,
            srt=srt,
            files_created=video_result.files_created,
            akasha_event_id=event.event_id,
            dry_run=dry_run,
            cost_local_pct=_COST_LOCAL_PCT,
            artifacts={
                **video_result.artifacts,
                "run_id": ctx.run_id,
                "akasha_event_id": event.event_id,
                "srt_chars": len(srt),
            },
        )
