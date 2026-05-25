"""Testes de SRTGenerator.from_segments_in_window (Camada 2 — SRT por clipe)."""
from __future__ import annotations

from src.video_studio.srt_generator import SRTGenerator
from src.video_studio.models import TranscriptSegment


def _seg(start: float, end: float, text: str = "legenda") -> TranscriptSegment:
    return TranscriptSegment.new(start_seconds=start, end_seconds=end, text=text)


class TestFromSegmentsInWindow:
    def test_vazio_retorna_vazio(self):
        assert SRTGenerator.from_segments_in_window([], 0.0, 10.0) == []

    def test_ajusta_timestamps_para_tempo_relativo(self):
        # segmento em [12,15] num clipe que começa em 10 → SRT relativo [2,5]
        cuts = SRTGenerator.from_segments_in_window([_seg(12.0, 15.0)], 10.0, 20.0)
        assert len(cuts) == 1
        assert cuts[0]["start"] == 2.0
        assert cuts[0]["end"] == 5.0
        assert cuts[0]["text"] == "legenda"

    def test_ignora_segmentos_fora_da_janela(self):
        segs = [_seg(0.0, 2.0), _seg(50.0, 52.0)]  # ambos fora de [10,20]
        assert SRTGenerator.from_segments_in_window(segs, 10.0, 20.0) == []

    def test_clipa_segmento_que_cruza_borda(self):
        # segmento [8,14] num clipe [10,20] → recorta para relativo [0,4]
        cuts = SRTGenerator.from_segments_in_window([_seg(8.0, 14.0)], 10.0, 20.0)
        assert len(cuts) == 1
        assert cuts[0]["start"] == 0.0
        assert cuts[0]["end"] == 4.0

    def test_multiplos_segmentos_na_janela(self):
        segs = [_seg(10.0, 12.0), _seg(13.0, 15.0)]
        cuts = SRTGenerator.from_segments_in_window(segs, 10.0, 20.0)
        assert len(cuts) == 2
        assert cuts[0]["start"] == 0.0
        assert cuts[1]["start"] == 3.0

    def test_gera_srt_valido_a_partir_da_janela(self, tmp_path):
        cuts = SRTGenerator.from_segments_in_window([_seg(10.0, 13.0, "Oi")], 10.0, 20.0)
        out = SRTGenerator().generate(cuts, tmp_path / "c.srt")
        content = out.read_text(encoding="utf-8")
        assert "00:00:00,000 --> 00:00:03,000" in content
        assert "Oi" in content
