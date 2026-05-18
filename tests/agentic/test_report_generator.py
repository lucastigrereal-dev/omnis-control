"""Tests for ReportGenerator and MissionReport."""
import pytest
from pathlib import Path

from src.agentic.mission_engine import MissionEngine, MissionContract
from src.agentic.mission_intake import MissionIntake
from src.agentic.deliverable_mapper import DeliverableMapper
from src.reports.report_generator import ReportGenerator, MissionReport


class TestMissionReport:
    def test_to_markdown_basic(self):
        r = MissionReport(mission_id="MIS-001")
        md = r.to_markdown()
        assert "# Relatório Final — MIS-001" in md
        assert "Gerado em:" in md

    def test_to_markdown_with_contract(self, tmp_path):
        engine = MissionEngine(missions_root=tmp_path)
        contract = engine.open_mission("criar campanha", setor="marketing")
        r = MissionReport(mission_id=contract.mission_id, contract=contract)
        md = r.to_markdown()
        assert "criar campanha" in md
        assert "marketing" in md

    def test_to_markdown_with_intake(self, tmp_path):
        intake = MissionIntake().parse("cria campanha hotel urgente")
        r = MissionReport(mission_id="MIS-001", intake=intake)
        md = r.to_markdown()
        assert "Risco:" in md
        assert "Prazo:" in md

    def test_to_markdown_with_manifest(self, tmp_path):
        intake = MissionIntake().parse("cria campanha hotel")
        manifest = DeliverableMapper().map(intake)
        r = MissionReport(mission_id="MIS-001", manifest=manifest)
        md = r.to_markdown()
        assert "Entregáveis" in md
        assert "calendario_30_dias.csv" in md

    def test_to_markdown_full(self, tmp_path):
        engine = MissionEngine(missions_root=tmp_path)
        contract = engine.open_mission("campanha completa 30 dias", setor="marketing")
        intake = MissionIntake().parse("campanha completa 30 dias")
        manifest = DeliverableMapper().map(intake)

        r = MissionReport(
            mission_id=contract.mission_id,
            contract=contract,
            intake=intake,
            manifest=manifest,
            execution_notes="Todas as tasks concluídas com sucesso.",
            next_action="Revisar legendas antes de postar.",
        )
        md = r.to_markdown()
        assert "campanha completa 30 dias" in md
        assert "Todas as tasks" in md
        assert "Revisar legendas" in md

    def test_to_dict(self, tmp_path):
        engine = MissionEngine(missions_root=tmp_path)
        contract = engine.open_mission("teste")
        r = MissionReport(mission_id=contract.mission_id, contract=contract)
        d = r.to_dict()
        assert d["mission_id"] == contract.mission_id
        assert d["contract"] is not None


class TestReportGenerator:
    def test_generate_writes_file(self, tmp_path):
        engine = MissionEngine(missions_root=tmp_path)
        contract = engine.open_mission("teste relatorio", setor="tech")
        generator = ReportGenerator()
        report = generator.generate(contract)
        assert report.mission_id == contract.mission_id

        report_path = tmp_path / contract.mission_id / "relatorio_final.md"
        assert report_path.exists()
        content = report_path.read_text(encoding="utf-8")
        assert "teste relatorio" in content

    def test_generate_with_intake_and_manifest(self, tmp_path):
        engine = MissionEngine(missions_root=tmp_path)
        contract = engine.open_mission("cria campanha hotel")
        intake = MissionIntake().parse("cria campanha hotel")
        manifest = DeliverableMapper().map(intake)

        generator = ReportGenerator()
        report = generator.generate(contract, intake=intake, manifest=manifest)
        assert report.manifest is not None
        assert report.intake is not None

        report_path = tmp_path / contract.mission_id / "relatorio_final.md"
        content = report_path.read_text(encoding="utf-8")
        assert "Entregáveis" in content

    def test_generate_summary(self, tmp_path):
        engine = MissionEngine(missions_root=tmp_path)
        contract = engine.open_mission("fazer X", setor="ops")
        generator = ReportGenerator()
        summary = generator.generate_summary(contract)
        assert contract.mission_id in summary
        assert "fazer X" in summary
        assert "ops" in summary
