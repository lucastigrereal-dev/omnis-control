"""SRTGenerator — produces valid .srt subtitle files from cut data."""
from __future__ import annotations

import math
from pathlib import Path


def _format_ts(seconds: float) -> str:
    """Convert float seconds to SRT timestamp HH:MM:SS,mmm."""
    total_ms = int(round(seconds * 1000))
    ms = total_ms % 1000
    s = (total_ms // 1000) % 60
    m = (total_ms // 60000) % 60
    h = total_ms // 3600000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


class SRTGenerator:
    """Generate SRT subtitle files."""

    def generate(self, cuts: list[dict], output_path: Path) -> Path:
        """Write a valid .srt file from a list of cut dicts.

        Each dict must have: start (float), end (float), text (str).
        """
        lines: list[str] = []
        for idx, cut in enumerate(cuts, start=1):
            start = float(cut["start"])
            end = float(cut["end"])
            text = str(cut["text"])
            lines.append(str(idx))
            lines.append(f"{_format_ts(start)} --> {_format_ts(end)}")
            lines.append(text)
            lines.append("")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(lines), encoding="utf-8")
        return output_path

    @staticmethod
    def from_segments_in_window(
        segments: list,  # list[TranscriptSegment]
        clip_start: float,
        clip_end: float,
    ) -> list[dict]:
        """Filtra segmentos dentro de [clip_start, clip_end] e ajusta timestamps.

        Os timestamps no SRT gerado são relativos ao início do clipe (t=0),
        pois o vídeo renderizado começa do zero, não de clip_start.
        """
        result: list[dict] = []
        for seg in segments:
            # Ignora segmentos fora da janela
            if seg.end_seconds <= clip_start or seg.start_seconds >= clip_end:
                continue
            # Clipa às bordas da janela e ajusta para tempo relativo
            adj_start = max(seg.start_seconds - clip_start, 0.0)
            adj_end = min(seg.end_seconds - clip_start, clip_end - clip_start)
            if adj_end <= adj_start:
                continue
            result.append({
                "start": round(adj_start, 3),
                "end": round(adj_end, 3),
                "text": seg.text,
            })
        return result

    @staticmethod
    def from_transcription(transcription_text: str, duration: float) -> list[dict]:
        """Split transcription_text into timed segments spread across duration."""
        if not transcription_text.strip() or duration <= 0:
            return []

        words = transcription_text.strip().split()
        if not words:
            return []

        # Aim for ~10 words per segment
        chunk_size = 10
        chunks: list[list[str]] = []
        for i in range(0, len(words), chunk_size):
            chunks.append(words[i : i + chunk_size])

        seg_duration = duration / len(chunks)
        segments: list[dict] = []
        for i, chunk in enumerate(chunks):
            segments.append({
                "start": round(i * seg_duration, 3),
                "end": round((i + 1) * seg_duration, 3),
                "text": " ".join(chunk),
            })
        return segments
