"""VideoProcessor — contrato para o Lego de processamento de vídeo.

Uso previsto (Onda 3):
    from src.interfaces.video_processor import VideoProcessor, VideoSpec, VideoResult
    proc: VideoProcessor = VideoProcessorLego()
    result = proc.execute(VideoSpec(video_path="clip.mp4", goal="transcribe"))
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, Any


@dataclass
class VideoSpec:
    """Especificação de uma tarefa de processamento de vídeo."""
    video_path: str
    goal: str  # "transcribe" | "cut" | "extract_audio"
    dry_run: bool = True
    output_dir: str = "output/"
    start_seconds: float = 0.0
    end_seconds: float = 0.0
    language: str = "pt"
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class VideoResult:
    """Resultado estruturado de uma tarefa de vídeo."""
    success: bool
    output: str
    files_created: list[str]
    dry_run: bool
    error: str | None = None
    artifacts: dict[str, Any] = field(default_factory=dict)


class VideoProcessor(Protocol):
    """Contrato do processador de vídeo. O Lego implementa este Protocol."""

    def execute(self, spec: VideoSpec) -> VideoResult:
        """Processa um vídeo e retorna resultado estruturado."""
        ...

    def health_check(self) -> bool:
        """Retorna True se whisper e ffmpeg estão disponíveis."""
        ...
