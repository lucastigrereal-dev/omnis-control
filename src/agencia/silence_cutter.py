"""SilenceCutter — detecta e remove silêncio entre segmentos de transcrição.

Camada 2 da Agência: opera sobre TranscriptSegment para identificar janelas
de fala real e gerar filtro FFmpeg silenceremove.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class SpeechInterval:
    """Intervalo de fala contínua dentro de um clipe."""
    start: float
    end: float

    @property
    def duration(self) -> float:
        return round(self.end - self.start, 3)

    def to_dict(self) -> dict:
        return {"start": self.start, "end": self.end, "duration": self.duration}


class SilenceCutter:
    """Identifica silêncios entre segmentos de transcrição.

    Uso:
        cutter = SilenceCutter(min_silence_gap=0.5)
        intervals = cutter.get_speech_intervals(segments, clip_start=0.0, clip_end=30.0)
        af_filter = cutter.silenceremove_filter()
    """

    DEFAULT_MIN_SILENCE_GAP: float = 0.5  # segundos

    def __init__(self, min_silence_gap: float = DEFAULT_MIN_SILENCE_GAP) -> None:
        self.min_silence_gap = min_silence_gap

    def get_speech_intervals(
        self,
        segments: list,  # list[TranscriptSegment]
        clip_start: float = 0.0,
        clip_end: Optional[float] = None,
    ) -> list[SpeechInterval]:
        """Retorna intervalos de fala dentro de [clip_start, clip_end].

        Segmentos separados por gap <= min_silence_gap são fundidos.
        Silêncios maiores geram novo intervalo separado.
        """
        if not segments:
            return []

        # Filtra segmentos que se sobrepõem à janela do clipe
        effective_end = clip_end if clip_end is not None else float("inf")
        window = [
            s for s in segments
            if s.start_seconds < effective_end and s.end_seconds > clip_start
        ]
        if not window:
            return []

        window = sorted(window, key=lambda s: s.start_seconds)

        current_start = max(window[0].start_seconds, clip_start)
        current_end = min(window[0].end_seconds, effective_end)
        intervals: list[SpeechInterval] = []

        for seg in window[1:]:
            seg_start = seg.start_seconds
            seg_end = min(seg.end_seconds, effective_end)
            gap = seg_start - current_end

            if gap <= self.min_silence_gap:
                # Silêncio pequeno — funde no intervalo atual
                current_end = max(current_end, seg_end)
            else:
                # Silêncio real — fecha intervalo e abre novo
                intervals.append(SpeechInterval(current_start, current_end))
                current_start = seg_start
                current_end = seg_end

        intervals.append(SpeechInterval(current_start, current_end))
        return intervals

    def silenceremove_filter(self, min_silence_gap: Optional[float] = None) -> str:
        """Retorna filtro FFmpeg silenceremove para áudio.

        stop_periods=-1  = remove todos os silêncios internos do clipe.
        stop_duration    = duração mínima de silêncio para remover.
        stop_threshold   = -50dB = silêncio prático.
        """
        gap = min_silence_gap if min_silence_gap is not None else self.min_silence_gap
        return f"silenceremove=stop_periods=-1:stop_duration={gap}:stop_threshold=-50dB"

    def silence_report(
        self,
        segments: list,
        clip_start: float = 0.0,
        clip_end: Optional[float] = None,
    ) -> dict:
        """Relatório de silêncio no clipe — útil para manifest e logs."""
        speech_intervals = self.get_speech_intervals(segments, clip_start, clip_end)
        effective_end = clip_end if clip_end is not None else (
            segments[-1].end_seconds if segments else clip_start
        )
        total_clip = max(effective_end - clip_start, 0.0)
        total_speech = sum(i.duration for i in speech_intervals)
        total_silence = max(total_clip - total_speech, 0.0)

        return {
            "total_clip_seconds": round(total_clip, 2),
            "total_speech_seconds": round(total_speech, 2),
            "total_silence_seconds": round(total_silence, 2),
            "speech_pct": round(100 * total_speech / total_clip, 1) if total_clip > 0 else 0.0,
            "speech_interval_count": len(speech_intervals),
            "intervals": [i.to_dict() for i in speech_intervals],
        }
