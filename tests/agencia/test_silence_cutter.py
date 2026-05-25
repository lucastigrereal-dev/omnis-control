"""Testes do SilenceCutter (Camada 2) — detecção de silêncio entre segmentos."""
from __future__ import annotations

import pytest

from src.agencia.silence_cutter import SilenceCutter, SpeechInterval
from src.video_studio.models import TranscriptSegment


def _seg(start: float, end: float, text: str = "fala") -> TranscriptSegment:
    return TranscriptSegment.new(start_seconds=start, end_seconds=end, text=text)


class TestSpeechInterval:
    def test_duration_calculada(self):
        iv = SpeechInterval(start=2.0, end=5.5)
        assert iv.duration == 3.5

    def test_to_dict_round_trip(self):
        iv = SpeechInterval(start=1.0, end=2.0)
        d = iv.to_dict()
        assert d == {"start": 1.0, "end": 2.0, "duration": 1.0}


class TestGetSpeechIntervals:
    def test_lista_vazia_retorna_vazio(self):
        assert SilenceCutter().get_speech_intervals([]) == []

    def test_segmento_unico(self):
        ivs = SilenceCutter().get_speech_intervals([_seg(0.0, 3.0)])
        assert len(ivs) == 1
        assert ivs[0].start == 0.0 and ivs[0].end == 3.0

    def test_gap_pequeno_funde(self):
        # gap de 0.3s entre 3.0 e 3.3 < min_silence_gap=0.5 → funde
        segs = [_seg(0.0, 3.0), _seg(3.3, 6.0)]
        ivs = SilenceCutter(min_silence_gap=0.5).get_speech_intervals(segs)
        assert len(ivs) == 1
        assert ivs[0].start == 0.0 and ivs[0].end == 6.0

    def test_gap_grande_separa(self):
        # gap de 2.0s entre 3.0 e 5.0 > min_silence_gap=0.5 → separa
        segs = [_seg(0.0, 3.0), _seg(5.0, 8.0)]
        ivs = SilenceCutter(min_silence_gap=0.5).get_speech_intervals(segs)
        assert len(ivs) == 2
        assert ivs[0].end == 3.0
        assert ivs[1].start == 5.0

    def test_janela_recorta_segmentos(self):
        # clip_start=1.0, clip_end=4.0 deve recortar segmento [0,6] para [1,4]
        ivs = SilenceCutter().get_speech_intervals([_seg(0.0, 6.0)], clip_start=1.0, clip_end=4.0)
        assert len(ivs) == 1
        assert ivs[0].start == 1.0 and ivs[0].end == 4.0

    def test_fora_da_janela_ignorado(self):
        # segmento [10,12] fora da janela [0,5]
        ivs = SilenceCutter().get_speech_intervals([_seg(10.0, 12.0)], clip_start=0.0, clip_end=5.0)
        assert ivs == []


class TestSilenceRemoveFilter:
    def test_filtro_usa_gap_padrao(self):
        f = SilenceCutter(min_silence_gap=0.5).silenceremove_filter()
        assert "silenceremove" in f
        assert "stop_duration=0.5" in f
        assert "stop_threshold=-50dB" in f

    def test_filtro_aceita_override(self):
        f = SilenceCutter().silenceremove_filter(min_silence_gap=1.2)
        assert "stop_duration=1.2" in f


class TestSilenceReport:
    def test_relatorio_clip_cheio_de_fala(self):
        # clipe [0,3] totalmente preenchido → 100% fala, 0 silêncio
        rep = SilenceCutter().silence_report([_seg(0.0, 3.0)], clip_start=0.0, clip_end=3.0)
        assert rep["total_clip_seconds"] == 3.0
        assert rep["total_speech_seconds"] == 3.0
        assert rep["total_silence_seconds"] == 0.0
        assert rep["speech_pct"] == 100.0
        assert rep["speech_interval_count"] == 1

    def test_relatorio_com_silencio(self):
        # clipe [0,10], fala em [0,2] e [8,10] → 4s fala, 6s silêncio
        segs = [_seg(0.0, 2.0), _seg(8.0, 10.0)]
        rep = SilenceCutter(min_silence_gap=0.5).silence_report(segs, clip_start=0.0, clip_end=10.0)
        assert rep["total_clip_seconds"] == 10.0
        assert rep["total_speech_seconds"] == 4.0
        assert rep["total_silence_seconds"] == 6.0
        assert rep["speech_pct"] == 40.0
        assert rep["speech_interval_count"] == 2

    def test_relatorio_vazio(self):
        rep = SilenceCutter().silence_report([], clip_start=0.0, clip_end=5.0)
        assert rep["speech_interval_count"] == 0
        assert rep["intervals"] == []
