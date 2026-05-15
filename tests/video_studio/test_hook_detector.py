"""Tests for W104 — Hook Detector."""
from __future__ import annotations

import pytest

from src.video_studio.models import TranscriptSegment, HookCandidate, HookStrength
from src.video_studio.hooks import HookDetector, HookCriteria


class TestHookCriteria:
    def test_create_criteria(self):
        cr = HookCriteria(segment_id="s1", text="test")
        assert cr.segment_id == "s1"
        assert cr.has_question is False
        assert cr.score == 0.0

    def test_criteria_with_patterns(self):
        cr = HookCriteria(
            segment_id="s2",
            text="Voce ja imaginou isso?",
            has_question=True,
            has_location=True,
            score=0.5,
        )
        assert cr.has_question is True
        assert cr.has_location is True
        assert cr.score == 0.5

    def test_to_dict(self):
        cr = HookCriteria(segment_id="s3", text="test", has_question=True)
        d = cr.to_dict()
        assert d["segment_id"] == "s3"
        assert d["has_question"] is True


class TestHookDetector:
    def setup_method(self):
        self.detector = HookDetector(max_hooks=10)

    def _make_segments(self, texts: list[str]) -> list[TranscriptSegment]:
        segs = []
        for i, t in enumerate(texts):
            segs.append(TranscriptSegment.new(
                start_seconds=i * 5.0,
                end_seconds=(i + 1) * 5.0,
                text=t,
                confidence=0.95,
            ))
        return segs

    def test_detect_question_hook(self):
        segs = self._make_segments([
            "Voce ja imaginou acordar com essa vista paradisiaca em Natal?",
            "Aqui tudo e mais bonito e tranquilo para sua familia.",
        ])
        hooks = self.detector.detect(segs)
        assert len(hooks) > 0
        assert any("Voce ja imaginou" in h.hook_text for h in hooks)

    def test_detect_shock_hook(self):
        segs = self._make_segments([
            "O segredo que ninguem te conta sobre viajar para o Nordeste.",
        ])
        hooks = self.detector.detect(segs)
        assert len(hooks) > 0

    def test_detect_number_hook(self):
        segs = self._make_segments([
            "Mais de 3 milhoes de turistas visitaram Natal no ultimo ano.",
        ])
        hooks = self.detector.detect(segs)
        assert len(hooks) > 0

    def test_detect_location_hook(self):
        segs = self._make_segments([
            "Ponta Negra e o melhor bairro de Natal para se hospedar.",
        ])
        hooks = self.detector.detect(segs)
        assert len(hooks) > 0
        assert any("natal" in h.hook_text.lower() for h in hooks)

    def test_detect_multiple_criteria(self):
        segs = self._make_segments([
            "Voce sabia que mais de 3 milhoes de turistas visitam Natal? O segredo que ninguem te conta!",
        ])
        hooks = self.detector.detect(segs)
        assert len(hooks) > 0
        # Should score high with multiple criteria
        assert hooks[0].score >= 0.4

    def test_ignores_short_segments(self):
        segs = self._make_segments(["Oi.", "La.", "Sim."])
        hooks = self.detector.detect(segs)
        assert len(hooks) == 0

    def test_max_hooks_limit(self):
        detector = HookDetector(max_hooks=2)
        texts = [f"Voce ja pensou em viajar para o destino numero {i}?" for i in range(10)]
        segs = self._make_segments(texts)
        hooks = detector.detect(segs)
        assert len(hooks) <= 2

    def test_empty_segments(self):
        hooks = self.detector.detect([])
        assert hooks == []

    def test_hooks_have_valid_scores(self):
        segs = self._make_segments([
            "Voce ja pensou em viajar? Descubra o paraiso escondido em Natal!",
        ])
        hooks = self.detector.detect(segs)
        for h in hooks:
            assert 0.0 <= h.score <= 1.0

    def test_hook_has_strength(self):
        segs = self._make_segments([
            "Voce ja imaginou isso? O segredo que ninguem te conta sobre Natal! Mais de 3 milhoes ja foram!",
        ])
        hooks = self.detector.detect(segs)
        for h in hooks:
            assert h.strength in HookStrength

    def test_conflict_detection(self):
        segs = self._make_segments([
            "Muita gente acha que viajar e caro mas nao e bem assim que funciona.",
        ])
        hooks = self.detector.detect(segs)
        assert len(hooks) > 0

    def test_promise_detection(self):
        segs = self._make_segments([
            "Eu garanto que depois desse video sua proxima viagem sera para Natal.",
        ])
        hooks = self.detector.detect(segs)
        assert len(hooks) > 0
