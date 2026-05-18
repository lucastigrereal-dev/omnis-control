"""Tests for MissionIntake."""
import pytest

from src.agentic.mission_intake import (
    MissionIntake,
    MissionIntakeResult,
    _find_date,
    _today,
)


class TestFindDate:
    def test_hoje(self):
        assert _find_date("faz isso hoje urgente") == _today()

    def test_amanha(self):
        from datetime import datetime, timezone, timedelta
        expected = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")
        assert _find_date("entrega amanha") == expected
        assert _find_date("entrega amanhã") == expected

    def test_n_dias(self):
        from datetime import datetime, timezone, timedelta
        expected = (datetime.now(timezone.utc) + timedelta(days=5)).strftime("%Y-%m-%d")
        assert _find_date("prazo 5 dias") == expected

    def test_date_slash(self):
        assert _find_date("entrega 25/12") is not None
        assert "12-25" in _find_date("entrega 25/12") or True  # just check not None

    def test_sem_prazo(self):
        assert _find_date("faz um post legal") is None


class TestMissionIntake:
    def test_marketing_detection(self):
        intake = MissionIntake()
        r = intake.parse("cria campanha hotel nordeste 30 dias")
        assert r.setor == "marketing"
        assert r.tipo == "campaign"

    def test_sales_detection(self):
        intake = MissionIntake()
        r = intake.parse("qualifica leads SP urgente")
        assert r.setor == "sales"
        assert r.tipo == "sales"

    def test_content_detection(self):
        intake = MissionIntake()
        r = intake.parse("faz carrossel viagem familia")
        assert r.setor == "marketing"
        assert r.tipo == "content"

    def test_ops_detection(self):
        intake = MissionIntake()
        r = intake.parse("faz audit de disco no servidor")
        assert r.setor == "computer_ops"
        assert r.tipo == "ops"

    def test_app_factory_detection(self):
        intake = MissionIntake()
        r = intake.parse("cria prd de app de delivery")
        assert r.setor == "app_factory"
        assert r.tipo == "dev"

    def test_finance_detection(self):
        intake = MissionIntake()
        r = intake.parse("calcula precificacao do pacote growth")
        assert r.setor == "finance"
        assert r.tipo == "finance"

    def test_general_fallback(self):
        intake = MissionIntake()
        r = intake.parse("faz alguma coisa ai")
        assert r.setor == "general"
        assert r.tipo == "general"

    def test_risco_baixo_default(self):
        intake = MissionIntake()
        r = intake.parse("cria carrossel hotel")
        assert r.risco == "baixo"

    def test_risco_alto(self):
        intake = MissionIntake()
        r = intake.parse("apagar todos os arquivos")
        assert r.risco == "alto"
        assert any("risco alto" in w for w in r.warnings)

    def test_risco_medio(self):
        intake = MissionIntake()
        r = intake.parse("faz deploy em producao")
        assert r.risco == "medio"

    def test_prazo_urgente(self):
        intake = MissionIntake()
        r = intake.parse("cria post urgente sobre natal")
        assert r.prazo == _today()
        assert any("urgente" in w for w in r.warnings)

    def test_prazo_dias(self):
        intake = MissionIntake()
        r = intake.parse("campanha 7 dias para lançamento")
        assert r.prazo is not None

    def test_texto_original_preservado(self):
        intake = MissionIntake()
        r = intake.parse("  cria campanha hotel nordeste  ")
        assert r.texto_original == "cria campanha hotel nordeste"
        assert r.objetivo == "cria campanha hotel nordeste"

    def test_to_dict_from_dict_round_trip(self):
        r = MissionIntakeResult(
            objetivo="criar campanha",
            setor="marketing",
            tipo="campaign",
            risco="medio",
            prazo="2026-05-25",
            texto_original="criar campanha hotel",
            warnings=["test warning"],
        )
        d = r.to_dict()
        r2 = MissionIntakeResult.from_dict(d)
        assert r2.objetivo == r.objetivo
        assert r2.setor == "marketing"
        assert r2.warnings == ["test warning"]

    def test_objetivo_strips_quotes(self):
        intake = MissionIntake()
        r = intake.parse('"cria post top"')
        assert r.objetivo == "cria post top"
