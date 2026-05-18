"""Tests for Quality Scorer."""

import pytest

from src.quality_gate.scorer import QualityScorer
from src.quality_gate.models import QualityReport, ScoredDimension


@pytest.fixture
def scorer():
    return QualityScorer()


class TestQualityScorerCaption:
    GOOD_CAPTION = """Voce precisa conhecer esse hotel incrivel em Natal RN!

    Fiquei hospedado no Serhs Natal Grand Hotel e foi uma experiencia surreal.
    Quarto com vista pro mar, cafe da manha completo e area de lazer incrivel.

    O melhor: tem desconto exclusivo pra quem reserva pelo link.
    Arrasta pro lado pra ver todas as fotos!

    .📍 Natal, RN
    .📸 @lucastigrereal
    .🔗 Link na bio para reservar

    #hotel #natalrn #viagem #turismo #nordeste #brasil #resort #praia #hospedagem #ferias"""

    WEAK_CAPTION = "talvez um dia vou ver esse lugar quem sabe"

    def test_good_caption_scores_high(self, scorer):
        report = scorer.score("cap-01", "caption", self.GOOD_CAPTION)
        assert report.overall_score >= 6.5
        assert report.grade in ("A", "B")
        assert report.ready_for_use

    def test_weak_caption_scores_low(self, scorer):
        report = scorer.score("cap-02", "caption", self.WEAK_CAPTION)
        assert report.overall_score < 6.0
        assert not report.ready_for_use

    def test_report_has_all_dimensions(self, scorer):
        report = scorer.score("cap-03", "caption", self.GOOD_CAPTION)
        dim_names = {d.name for d in report.dimensions}
        assert "clarity" in dim_names
        assert "hook_strength" in dim_names
        assert "seo" in dim_names
        assert "cta" in dim_names
        assert "risk" in dim_names

    def test_hook_detection(self, scorer):
        report = scorer.score("hook-01", "caption",
                              "Voce precisa ver isso agora! Conteudo incrivel sobre viagem.")
        hook_dim = next(d for d in report.dimensions if d.name == "hook_strength")
        assert hook_dim.score >= 6.0

    def test_risk_detection(self, scorer):
        report = scorer.score("risk-01", "caption",
                              "Garantimos resultado garantido em 30 dias! Preco imperdivel!")
        risk_dim = next(d for d in report.dimensions if d.name == "risk")
        assert risk_dim.score < 10.0  # Should detect issues
        assert len(risk_dim.issues) > 0

    def test_cta_detection(self, scorer):
        report = scorer.score("cta-01", "caption",
                              "Comenta aqui o que achou! Salva pra ver depois.")
        cta_dim = next(d for d in report.dimensions if d.name == "cta")
        assert cta_dim.score >= 6.0


class TestQualityScorerDM:
    def test_dm_scores(self, scorer):
        report = scorer.score("dm-01", "dm",
                              "Ola Joao, vi que voce trabalha no Hotel Serra Azul. "
                              "Gostaria de conversar sobre parceria de conteudo.",
                              metadata={"recipient_name": "Joao", "company_name": "Hotel Serra Azul"})
        assert report.overall_score > 0
        personalization = next(d for d in report.dimensions if d.name == "personalization")
        assert personalization.score >= 8.0  # Both name and company mentioned

    def test_dm_no_personalization(self, scorer):
        report = scorer.score("dm-02", "dm", "Ola, gostaria de conversar sobre parceria.")
        personalization = next(d for d in report.dimensions if d.name == "personalization")
        assert personalization.score < 8.0


class TestQualityScorerApp:
    APP_CODE = """
import pytest
from main import app
from fastapi.testclient import TestClient
client = TestClient(app)
def test_health():
    assert client.get("/health").status_code == 200
def test_create():
    assert True
def test_list():
    assert True
def test_delete():
    assert True
"""

    def test_app_code_scores(self, scorer):
        report = scorer.score("app-01", "app", self.APP_CODE)
        assert report.overall_score > 0
        tests_dim = next(d for d in report.dimensions if d.name == "tests")
        assert tests_dim.score >= 8.0  # 4 test functions


class TestQualityReport:
    def test_grade_a(self):
        r = QualityReport(output_id="t1", output_type="caption", overall_score=9.2)
        assert r.overall_score == 9.2

    def test_passed_failed(self):
        r = QualityReport(output_id="t1", output_type="caption", dimensions=[
            ScoredDimension(name="a", score=8.0),
            ScoredDimension(name="b", score=5.0),
            ScoredDimension(name="c", score=9.0),
        ])
        assert r.passed_dimensions == 2
        assert r.failed_dimensions == 1
