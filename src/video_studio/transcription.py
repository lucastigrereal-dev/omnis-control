"""W103 — Transcription Adapter Mock wrapping TranscriptSegment."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol

from src.video_studio.models import TranscriptSegment


class TranscriptionAdapter(Protocol):
    """Protocol for transcription adapters — never real Whisper."""

    def transcribe(self, source_hint: str, duration_seconds: float) -> "VideoTranscript":
        ...


@dataclass
class VideoTranscript:
    """Aggregated transcript from a video source."""

    transcript_id: str
    source_id: str = ""
    segments: list[TranscriptSegment] = field(default_factory=list)
    language_hint: str = "pt"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def total_duration(self) -> float:
        return sum(s.duration for s in self.segments)

    @property
    def segment_count(self) -> int:
        return len(self.segments)

    @property
    def full_text(self) -> str:
        return " ".join(s.text for s in self.segments)

    def to_dict(self) -> dict:
        return {
            "transcript_id": self.transcript_id,
            "source_id": self.source_id,
            "segments": [s.to_dict() for s in self.segments],
            "language_hint": self.language_hint,
            "segment_count": self.segment_count,
            "total_duration": self.total_duration,
            "full_text": self.full_text,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "VideoTranscript":
        t = cls(
            transcript_id=d["transcript_id"],
            source_id=d.get("source_id", ""),
            language_hint=d.get("language_hint", "pt"),
            created_at=d.get("created_at", ""),
        )
        for s in d.get("segments", []):
            t.segments.append(TranscriptSegment.from_dict(s))
        return t

    def to_markdown(self) -> str:
        lines = [
            f"# Video Transcript: {self.transcript_id}",
            f"**Segments:** {self.segment_count} | **Duration:** {self.total_duration}s | **Lang:** {self.language_hint}",
            "",
        ]
        for s in self.segments:
            lines.append(
                f"[{s.start_seconds:.1f}s - {s.end_seconds:.1f}s] {s.text}"
            )
        return "\n".join(lines)


class MockTranscriptionAdapter(TranscriptionAdapter):
    """Deterministic mock transcription — never calls Whisper or any API."""

    TOURISM_TRANSCRIPT: list[dict] = [
        {"start": 0.0, "end": 3.0, "text": "Voce ja imaginou acordar com essa vista?"},
        {"start": 3.0, "end": 8.0, "text": "Natal e um paraiso escondido no nordeste brasileiro."},
        {"start": 8.0, "end": 15.0, "text": "Aqui temos praias paradisiacas, gastronomia incrivel e um povo acolhedor."},
        {"start": 15.0, "end": 22.0, "text": "O que muita gente nao sabe e que da pra viajar gastando menos do que imagina."},
        {"start": 22.0, "end": 28.0, "text": "So esse ano, mais de 3 milhoes de turistas passaram por aqui."},
        {"start": 28.0, "end": 35.0, "text": "E o melhor: tem opcoes para todos os bolsos e estilos de viagem."},
        {"start": 35.0, "end": 42.0, "text": "De resorts all-inclusive a pousadas boutique, Natal tem tudo."},
        {"start": 42.0, "end": 48.0, "text": "A gastronomia local e um capitulo a parte — frutos do mar frescos e precos justos."},
        {"start": 48.0, "end": 55.0, "text": "E a cultura? O forro, o artesanato, as festas tradicionais — tudo vivo e autentico."},
        {"start": 55.0, "end": 60.0, "text": "Entao se voce busca uma experiencia completa, Natal te espera de bracos abertos."},
    ]

    DEFAULT_TRANSCRIPT: list[dict] = [
        {"start": 0.0, "end": 5.0, "text": "Bem-vindo ao nosso video sobre viagem e turismo."},
        {"start": 5.0, "end": 10.0, "text": "Hoje vou mostrar um destino incrivel para suas ferias."},
        {"start": 10.0, "end": 15.0, "text": "Prepare-se para se surpreender com belezas naturais."},
        {"start": 15.0, "end": 20.0, "text": "E o melhor: com precos acessiveis e infraestrutura completa."},
        {"start": 20.0, "end": 25.0, "text": "Fique ate o final que tenho uma dica imperdivel."},
        {"start": 25.0, "end": 30.0, "text": "Curta e compartilhe com quem precisa conhecer esse lugar."},
    ]

    def transcribe(self, source_hint: str, duration_seconds: float = 60.0) -> VideoTranscript:
        import uuid

        raw = self._pick_transcript(source_hint)
        segments: list[TranscriptSegment] = []

        for i, entry in enumerate(raw):
            if entry["start"] >= duration_seconds:
                break
            end = min(entry["end"], duration_seconds)
            segments.append(TranscriptSegment.new(
                start_seconds=entry["start"],
                end_seconds=end,
                text=entry["text"],
                confidence=0.95,
                speaker_label=None,
            ))

        return VideoTranscript(
            transcript_id=str(uuid.uuid4())[:8],
            source_id=source_hint,
            segments=segments,
            language_hint="pt",
        )

    def _pick_transcript(self, source_hint: str) -> list[dict]:
        hint_lower = source_hint.lower()
        if any(w in hint_lower for w in ["turismo", "natal", "praia", "viagem", "destino", "nordeste"]):
            return self.TOURISM_TRANSCRIPT
        return self.DEFAULT_TRANSCRIPT
