"""Tests for DeliverableMapper and DeliverableManifest."""
import pytest

from src.agentic.mission_intake import MissionIntake, MissionIntakeResult
from src.agentic.deliverable_mapper import (
    DeliverableMapper,
    DeliverableManifest,
    DeliverableSpec,
    _DEFAULT_DELIVERABLES,
)


class TestDeliverableManifest:
    def test_to_dict_from_dict_round_trip(self):
        m = DeliverableManifest(
            mission_id="MIS-001",
            setor="marketing",
            tipo="campaign",
            deliverables=[
                DeliverableSpec("a.csv", "desc", "csv"),
                DeliverableSpec("b.md", "desc2", "md", required=False),
            ],
            export_hint="test",
        )
        d = m.to_dict()
        m2 = DeliverableManifest.from_dict(d)
        assert m2.mission_id == "MIS-001"
        assert m2.setor == "marketing"
        assert len(m2.deliverables) == 2
        assert m2.deliverables[0].filename == "a.csv"
        assert m2.deliverables[1].required is False
        assert m2.export_hint == "test"

    def test_empty_manifest(self):
        m = DeliverableManifest(mission_id=None, setor="general", tipo="general")
        assert m.deliverables == []
        assert m.export_hint == ""


class TestDeliverableMapper:
    def test_marketing_campaign(self):
        intake = MissionIntake()
        result = intake.parse("cria campanha hotel nordeste 30 dias")
        mapper = DeliverableMapper()
        manifest = mapper.map(result)
        assert manifest.setor == "marketing"
        assert len(manifest.deliverables) >= 3
        filenames = [d.filename for d in manifest.deliverables]
        assert "calendario_30_dias.csv" in filenames
        assert "legendas_batch.csv" in filenames

    def test_marketing_content(self):
        intake = MissionIntake()
        result = intake.parse("faz carrossel viagem familia")
        mapper = DeliverableMapper()
        manifest = mapper.map(result)
        assert manifest.tipo == "content"
        filenames = [d.filename for d in manifest.deliverables]
        assert "legenda_final.md" in filenames

    def test_sales(self):
        intake = MissionIntake()
        result = intake.parse("qualifica leads SP")
        mapper = DeliverableMapper()
        manifest = mapper.map(result)
        assert manifest.setor == "sales"
        filenames = [d.filename for d in manifest.deliverables]
        assert "lead_list.csv" in filenames
        assert "dm_sequence.md" in filenames
        assert "proposta_comercial.md" in filenames

    def test_app_factory(self):
        intake = MissionIntake()
        result = intake.parse("cria prd de app de delivery")
        mapper = DeliverableMapper()
        manifest = mapper.map(result)
        filenames = [d.filename for d in manifest.deliverables]
        assert "PRD.md" in filenames
        assert "package.zip" in filenames

    def test_computer_ops(self):
        intake = MissionIntake()
        result = intake.parse("faz audit de disco no servidor")
        mapper = DeliverableMapper()
        manifest = mapper.map(result)
        filenames = [d.filename for d in manifest.deliverables]
        assert "audit_report.md" in filenames
        assert "health_check.json" in filenames

    def test_finance(self):
        intake = MissionIntake()
        result = intake.parse("calcula precificacao do pacote growth")
        mapper = DeliverableMapper()
        manifest = mapper.map(result)
        filenames = [d.filename for d in manifest.deliverables]
        assert "pricing_model.csv" in filenames
        assert "revenue_report.md" in filenames

    def test_general_fallback_to_defaults(self):
        intake = MissionIntake()
        result = intake.parse("faz alguma coisa ai")
        mapper = DeliverableMapper()
        manifest = mapper.map(result)
        assert len(manifest.deliverables) == len(_DEFAULT_DELIVERABLES)
        default_names = [d.filename for d in _DEFAULT_DELIVERABLES]
        for d in manifest.deliverables:
            assert d.filename in default_names

    def test_export_hint_for_exports(self):
        intake = MissionIntake()
        result = intake.parse("cria campanha hotel")
        mapper = DeliverableMapper()
        manifest = mapper.map(result)
        assert "06_exports/" in manifest.export_hint

    def test_no_export_hint_when_no_exports(self):
        result = MissionIntakeResult(
            objetivo="faz algo", setor="general", tipo="general"
        )
        mapper = DeliverableMapper()
        manifest = mapper.map(result)
        assert manifest.export_hint == ""
