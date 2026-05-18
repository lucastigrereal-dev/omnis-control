"""VideoStudioPipeline — orchestrates the full video processing pipeline."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from src.video_studio.audio_extract import AudioExtractor
from src.video_studio.ingest import VideoIngestor
from src.video_studio.render_ffmpeg import FFmpegRenderer
from src.video_studio.srt_generator import SRTGenerator

logger = logging.getLogger(__name__)

_MOCK_TRANSCRIPTION = (
    "Este video mostra um destino incrivel no Brasil. "
    "Confira as melhores praias e restaurantes da regiao. "
    "Nao perca as dicas exclusivas para aproveitar ao maximo sua viagem."
)


class VideoStudioPipeline:
    """End-to-end local video pipeline. dry_run=True never calls ffmpeg."""

    def __init__(
        self,
        ingestor: VideoIngestor | None = None,
        extractor: AudioExtractor | None = None,
        srt_gen: SRTGenerator | None = None,
        renderer: FFmpegRenderer | None = None,
    ) -> None:
        self.ingestor = ingestor or VideoIngestor()
        self.extractor = extractor or AudioExtractor()
        self.srt_gen = srt_gen or SRTGenerator()
        self.renderer = renderer or FFmpegRenderer()

    def run(self, video_path: Path, output_dir: Path, dry_run: bool = True) -> dict:
        output_dir.mkdir(parents=True, exist_ok=True)

        # 1. Ingest
        ingest_result = self.ingestor.ingest(video_path)
        logger.info("Ingest: %s (%d bytes)", ingest_result.format, ingest_result.size_bytes)

        # 2. Extract audio
        audio_path = self.extractor.extract(video_path, output_dir, dry_run=dry_run)

        # 3. Mock transcription
        transcription = _MOCK_TRANSCRIPTION
        duration = ingest_result.duration_estimate_seconds or 30.0

        # 4. Generate cut plan (simple: one cut for entire duration)
        cuts = [{"start": 0.0, "end": duration, "text": transcription}]

        # 5. SRT
        srt_path = output_dir / (video_path.stem + ".srt")
        srt_segments = self.srt_gen.from_transcription(transcription, duration)
        if srt_segments:
            self.srt_gen.generate(srt_segments, srt_path)

        # 6. Render first cut
        render_output = output_dir / (video_path.stem + "_cut.mp4")
        rendered = self.renderer.render_cut(
            video_path, 0.0, duration, render_output, dry_run=dry_run
        )

        manifest = {
            "video_path": str(video_path),
            "output_dir": str(output_dir),
            "dry_run": dry_run,
            "ingest": ingest_result.to_dict(),
            "audio_path": str(audio_path),
            "transcription": transcription,
            "cuts": cuts,
            "srt_path": str(srt_path) if srt_segments else None,
            "rendered_path": str(rendered),
            "ffmpeg_available": FFmpegRenderer.is_ffmpeg_available(),
        }

        manifest_path = output_dir / "export_manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        logger.info("Manifest saved: %s", manifest_path)

        return manifest
