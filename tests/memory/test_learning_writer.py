"""Tests for LearningWriter — learning generation, markdown, writeback."""
from __future__ import annotations

import pytest

from src.memory.learning_writer import (
    LearningWriter,
    LearningEntry,
    LearningReport,
)


# ── fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def writer():
    return LearningWriter(dry_run=True)


@pytest.fixture
def execution_summary():
    return {
        "executor": "publisher",
        "total_deliverables": 4,
        "dry_run": True,
        "skills_matched": ["generate_seogram_caption", "create_instagram_carousel"],
        "skills_fallback": 1,
        "risk": "baixo",
    }


# ── LearningEntry ──────────────────────────────────────────────────────

class TestLearningEntry:
    def test_defaults(self):
        entry = LearningEntry()
        assert entry.id.startswith("LRN-")
        assert entry.confidence == "medium"

    def test_to_markdown(self):
        entry = LearningEntry(
            topic="Teste",
            insight="Um insight relevante",
            evidence="Evidência observada",
            confidence="high",
            action_item="Fazer algo",
            tags=["test", "qa"],
        )
        md = entry.to_markdown()
        assert "### Teste" in md
        assert "Um insight relevante" in md
        assert "Evidência observada" in md
        assert "Fazer algo" in md

    def test_to_dict(self):
        entry = LearningEntry(
            topic="Routing",
            insight="Setor mapeado",
            evidence="Log de dispatch",
        )
        d = entry.to_dict()
        assert d["topic"] == "Routing"
        assert d["insight"] == "Setor mapeado"
        assert "tags" in d


# ── LearningReport ─────────────────────────────────────────────────────

class TestLearningReport:
    def test_defaults(self):
        report = LearningReport(mission_id="MIS-001")
        assert report.mission_id == "MIS-001"
        assert report.total == 0
        assert report.writeback_status == "pending"

    def test_to_dict(self):
        entry = LearningEntry(topic="T", insight="I", evidence="E")
        report = LearningReport(
            mission_id="MIS-001",
            entries=[entry],
            sector="marketing",
            total=1,
        )
        d = report.to_dict()
        assert d["mission_id"] == "MIS-001"
        assert len(d["entries"]) == 1
        assert d["sector"] == "marketing"


# ── LearningWriter.generate ────────────────────────────────────────────

class TestLearningWriterGenerate:
    def test_generates_learnings(self, writer, execution_summary):
        report = writer.generate(
            mission_id="MIS-001",
            sector="marketing",
            objectives=["criar campanha"],
            execution_summary=execution_summary,
        )
        assert report.total >= 5
        assert report.sector == "marketing"
        assert report.mission_id == "MIS-001"

    def test_includes_routing_topic(self, writer, execution_summary):
        report = writer.generate("MIS-001", "sales", ["vender"], execution_summary)
        routing = [e for e in report.entries if "Roteamento" in e.topic]
        assert len(routing) == 1
        assert "sales" in routing[0].tags

    def test_includes_deliverable_observation(self, writer, execution_summary):
        report = writer.generate("MIS-001", "marketing", ["x"], execution_summary)
        mapping = [e for e in report.entries if "Deliverables" in e.topic]
        assert len(mapping) == 1
        assert "4" in mapping[0].insight

    def test_includes_dry_run_observation(self, writer, execution_summary):
        report = writer.generate("MIS-001", "marketing", ["x"], execution_summary)
        dry = [e for e in report.entries if "Modo Seguro" in e.topic]
        assert len(dry) == 1

    def test_includes_skill_matches(self, writer, execution_summary):
        report = writer.generate("MIS-001", "marketing", ["x"], execution_summary)
        skills = [e for e in report.entries if "Skills Encontradas" in e.topic]
        assert len(skills) == 1
        assert "generate_seogram_caption" in skills[0].insight

    def test_includes_skill_gaps(self, writer, execution_summary):
        report = writer.generate("MIS-001", "marketing", ["x"], execution_summary)
        gaps = [e for e in report.entries if "Gaps" in e.topic]
        assert len(gaps) == 1

    def test_includes_objectives(self, writer, execution_summary):
        report = writer.generate("MIS-001", "marketing", ["obj1", "obj2"], execution_summary)
        obj = [e for e in report.entries if "Objetivos" in e.topic]
        assert len(obj) == 1

    def test_includes_risk_when_not_baixo(self, writer):
        summary = {"executor": "publisher", "risk": "alto", "dry_run": True,
                    "total_deliverables": 1, "skills_matched": [], "skills_fallback": 0}
        report = writer.generate("MIS-001", "marketing", ["x"], summary)
        risk_entries = [e for e in report.entries if "Risco" in e.topic]
        assert len(risk_entries) == 1

    def test_no_risk_when_baixo(self, writer, execution_summary):
        report = writer.generate("MIS-001", "marketing", ["x"], execution_summary)
        risk_entries = [e for e in report.entries if "Risco" in e.topic]
        assert len(risk_entries) == 0

    def test_includes_execution_mode(self, writer, execution_summary):
        report = writer.generate("MIS-001", "marketing", ["x"], execution_summary)
        mode = [e for e in report.entries if e.topic == "Modo de Execução"]
        assert len(mode) == 1
        assert "dry-run" in mode[0].insight.lower()


# ── markdown generation ────────────────────────────────────────────────

class TestMarkdownGeneration:
    def test_writes_learnings_md(self, writer, execution_summary, tmp_path):
        mission_path = tmp_path / "MIS-001"
        writer.generate(
            mission_id="MIS-001",
            sector="marketing",
            objectives=["criar campanha"],
            execution_summary=execution_summary,
            mission_path=mission_path,
        )
        md_file = mission_path / "10_learnings.md"
        assert md_file.exists()

        content = md_file.read_text(encoding="utf-8")
        assert "# Aprendizados — MIS-001" in content
        assert "## 1." in content

    def test_dry_run_sets_writeback_status(self, writer, execution_summary, tmp_path):
        report = writer.generate(
            "MIS-001", "marketing", ["x"], execution_summary,
            mission_path=tmp_path / "MIS-001",
        )
        assert "dry_run" in report.writeback_status

    def test_no_mission_path_no_file(self, writer, execution_summary, tmp_path):
        report = writer.generate(
            "MIS-001", "marketing", ["x"], execution_summary,
            mission_path=None,
        )
        assert report.total >= 4  # still generates, just doesn't write file


# ── empty/minimal summaries ────────────────────────────────────────────

class TestEdgeCases:
    def test_minimal_summary(self, writer):
        report = writer.generate(
            "MIS-MIN", "general", ["fazer algo"],
            {"executor": "skill_runner", "total_deliverables": 0,
             "dry_run": True, "skills_matched": [], "skills_fallback": 0,
             "risk": "baixo"},
        )
        assert report.total > 0
        # No deliverables topic when count is 0
        mapping = [e for e in report.entries if "Deliverables" in e.topic]
        assert len(mapping) == 0

    def test_empty_objectives(self, writer):
        report = writer.generate(
            "MIS-EMP", "general", [],
            {"executor": "skill_runner", "total_deliverables": 1,
             "dry_run": True, "skills_matched": [], "skills_fallback": 0,
             "risk": "baixo"},
        )
        # objectives list empty → no coverage entry
        obj = [e for e in report.entries if "Objetivos" in e.topic]
        assert len(obj) == 0

    def test_all_entries_have_ids(self, writer, execution_summary):
        report = writer.generate("MIS-001", "sales", ["x"], execution_summary)
        ids = {e.id for e in report.entries}
        assert len(ids) == report.total
        assert all(i.startswith("LRN-") for i in ids)
