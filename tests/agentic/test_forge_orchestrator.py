"""Tests for ForgeOrchestrator — gap detection, forge, registration, rollback."""
from __future__ import annotations

import pytest

from src.agentic.forge_orchestrator import (
    ForgeOrchestrator,
    GapReport,
    ForgeResult,
    SkillVersion,
)


@pytest.fixture
def forge():
    return ForgeOrchestrator(dry_run=True)


@pytest.fixture
def live_forge():
    return ForgeOrchestrator(dry_run=False)


# ── GapReport ──────────────────────────────────────────────────────────

class TestGapReport:
    def test_defaults(self):
        g = GapReport()
        assert g.gap_id.startswith("GAP-")

    def test_to_dict(self):
        g = GapReport(
            mission_id="MIS-001",
            missing_capability="Falta skill X",
            sector="marketing",
            suggested_skill_name="marketing_x",
            suggested_tags=["marketing", "x"],
        )
        d = g.to_dict()
        assert d["mission_id"] == "MIS-001"
        assert d["sector"] == "marketing"
        assert "x" in d["suggested_tags"]


# ── ForgeResult ────────────────────────────────────────────────────────

class TestForgeResult:
    def test_dry_run_is_success(self):
        r = ForgeResult(status="dry_run")
        assert r.success is True

    def test_failed_is_not_success(self):
        r = ForgeResult(status="failed", errors=["boom"])
        assert r.success is False

    def test_to_dict(self):
        r = ForgeResult(
            skill_name="test_skill",
            status="scaffolded",
            version="0.1.0",
            test_count=3,
        )
        d = r.to_dict()
        assert d["skill_name"] == "test_skill"
        assert d["version"] == "0.1.0"


# ── SkillVersion ───────────────────────────────────────────────────────

class TestSkillVersion:
    def test_to_dict(self):
        sv = SkillVersion(skill_name="s1", version="0.2.0", rollback_from="0.3.0")
        d = sv.to_dict()
        assert d["version"] == "0.2.0"
        assert d["rollback_from"] == "0.3.0"


# ── detect_gaps ────────────────────────────────────────────────────────

class TestDetectGaps:
    def test_detects_each_missing_skill(self, forge):
        gaps = forge.detect_gaps(
            "MIS-001", "marketing",
            ["skill_a", "skill_b"],
            ["deliverable_1.md"],
        )
        assert len(gaps) == 2

    def test_empty_missing_returns_empty(self, forge):
        gaps = forge.detect_gaps("MIS-001", "sales", [], ["d.md"])
        assert gaps == []

    def test_gap_has_sector(self, forge):
        gaps = forge.detect_gaps("MIS-001", "finance", ["x"], ["d.md"])
        assert gaps[0].sector == "finance"

    def test_finance_gaps_are_high_severity(self, forge):
        gaps = forge.detect_gaps("MIS-001", "finance", ["missing"], ["d.md"])
        assert gaps[0].severity == "high"

    def test_marketing_gaps_are_medium(self, forge):
        gaps = forge.detect_gaps("MIS-001", "marketing", ["x"], ["d.md"])
        assert gaps[0].severity == "medium"

    def test_stores_in_gaps_list(self, forge):
        assert len(forge.gaps) == 0
        forge.detect_gaps("MIS-001", "sales", ["a", "b"], ["d.md"])
        assert len(forge.gaps) == 2


# ── forge ──────────────────────────────────────────────────────────────

class TestForge:
    def test_dry_run_creates_dry_result(self, forge):
        gap = GapReport(
            mission_id="MIS-001",
            missing_capability="Falta X",
            sector="marketing",
            suggested_skill_name="marketing_x",
        )
        result = forge.forge(gap)
        assert result.status == "dry_run"
        assert result.success is True

    def test_live_creates_scaffolded(self, live_forge, tmp_path):
        gap = GapReport(
            mission_id="MIS-001",
            missing_capability="Falta X",
            sector="app_factory",
            suggested_skill_name="app_factory_x",
        )
        output = tmp_path / "skills"
        result = live_forge.forge(gap, output_dir=output)
        assert result.status == "scaffolded"
        assert result.skill_name == "app_factory_x"

    def test_stores_in_results_list(self, forge):
        gap = GapReport(suggested_skill_name="x")
        forge.forge(gap)
        assert len(forge.results) == 1


# ── register_skill ─────────────────────────────────────────────────────

class TestRegisterSkill:
    def test_registers_version(self, forge):
        result = ForgeResult(skill_name="my_skill", status="scaffolded")
        sv = forge.register_skill(result)
        assert sv.skill_name == "my_skill"
        assert sv.version == "0.1.0"
        assert sv.status == "active"

    def test_multiple_versions(self, forge):
        r1 = ForgeResult(skill_name="skill_x")
        forge.register_skill(r1, version="0.1.0")
        forge.register_skill(r1, version="0.2.0")
        assert forge.version_count == 2


# ── rollback ───────────────────────────────────────────────────────────

class TestRollback:
    def test_no_versions_returns_broken(self, forge):
        sv = forge.rollback("nonexistent")
        assert sv.status == "broken"

    def test_single_version_returns_broken(self, forge):
        r = ForgeResult(skill_name="skill_x")
        forge.register_skill(r, version="0.1.0")
        sv = forge.rollback("skill_x")
        assert sv.status == "broken"

    def test_two_versions_rolls_back(self, forge):
        r = ForgeResult(skill_name="skill_x")
        forge.register_skill(r, version="0.1.0")
        forge.register_skill(r, version="0.2.0")
        sv = forge.rollback("skill_x")
        assert sv.status == "active"
        assert sv.version == "0.1.0"
        assert sv.rollback_from == "0.2.0"


# ── process_gaps ───────────────────────────────────────────────────────

class TestProcessGaps:
    def test_full_pipeline(self, forge):
        results = forge.process_gaps(
            mission_id="MIS-001",
            sector="marketing",
            missing_skills=["skill_a", "skill_b"],
            deliverables=["deliv.md"],
        )
        assert len(results) == 2
        assert all(r.status == "dry_run" for r in results)
        assert forge.version_count == 2

    def test_empty_gaps_returns_empty(self, forge):
        results = forge.process_gaps("MIS-001", "sales", [], ["d.md"])
        assert results == []
