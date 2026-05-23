"""Tests for Week 2 autonomous local operation — F09."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.weekly.weekly_pack import WeeklyPackOrchestrator
from src.output_factory.factory import OutputFactory


# ------------------------------------------------------------------ #
# Fixtures
# ------------------------------------------------------------------ #

@pytest.fixture
def learnings_file(tmp_path) -> Path:
    """Write a minimal _learnings.jsonl for use in tests."""
    p = tmp_path / "_learnings.jsonl"
    p.write_text(
        json.dumps({
            "mission_id": "MIS-TEST-001",
            "timestamp": "2026-05-18T00:00:00Z",
            "learnings": [
                "Hotéis respondem melhor a dados de CPM comparativo",
                "CTAs com 'responde essa DM' tem 3x mais conversão",
                "Carrosséis com dados geram 40% mais salvos",
            ],
            "tags": ["teste"],
        }),
        encoding="utf-8",
    )
    return p


@pytest.fixture
def week2_orchestrator(tmp_path, monkeypatch):
    """Week 2 orchestrator without learning context, missions inside tmp_path."""
    monkeypatch.chdir(tmp_path)
    return WeeklyPackOrchestrator(
        project="A Gente Viaja Brasil",
        niche="turismo regional interior SP",
        objective="vender collabs hoteis fazenda",
        city="Brotas",
        channel="@agenteviajabrasil",
        dry_run=False,
    )


@pytest.fixture
def week2_orchestrator_with_learnings(tmp_path, monkeypatch, learnings_file):
    """Week 2 orchestrator with learning context loaded."""
    monkeypatch.chdir(tmp_path)
    return WeeklyPackOrchestrator(
        project="A Gente Viaja Brasil",
        niche="turismo regional interior SP",
        objective="vender collabs hoteis fazenda",
        city="Brotas",
        channel="@agenteviajabrasil",
        dry_run=False,
    ).with_learning_context(learnings_file)


# ------------------------------------------------------------------ #
# Week 2 pack — required files
# ------------------------------------------------------------------ #

REQUIRED_FILES = [
    "weekly_manifest.json",
    "posts.md",
    "stories.md",
    "reels.md",
    "carousel.md",
    "proposal.md",
    "learning_update.md",
]


def test_week2_pack_generates_all_required_files(week2_orchestrator, tmp_path):
    week2_orchestrator.run()
    mission_dirs = list((tmp_path / "missions").iterdir())
    assert len(mission_dirs) == 1, "Expected exactly one mission dir"
    d = mission_dirs[0]
    for fname in REQUIRED_FILES:
        assert (d / fname).exists(), f"Missing required file: {fname}"


def test_week2_manifest_has_correct_project(week2_orchestrator, tmp_path):
    week2_orchestrator.run()
    manifests = list(tmp_path.glob("missions/*/weekly_manifest.json"))
    data = json.loads(manifests[0].read_text(encoding="utf-8"))
    assert data["project"] == "A Gente Viaja Brasil"
    assert data["city"] == "Brotas"
    assert data["channel"] == "@agenteviajabrasil"


def test_week2_manifest_has_all_content_keys(week2_orchestrator):
    result = week2_orchestrator.run()
    for key in ("posts", "stories", "reels", "carousel", "proposal", "learning_update"):
        assert key in result, f"Missing key: {key}"


def test_week2_posts_count(week2_orchestrator):
    result = week2_orchestrator.run()
    assert len(result["posts"]) == 7


def test_week2_stories_count(week2_orchestrator):
    result = week2_orchestrator.run()
    assert len(result["stories"]) == 7


def test_week2_reels_count(week2_orchestrator):
    result = week2_orchestrator.run()
    assert len(result["reels"]) == 5


# ------------------------------------------------------------------ #
# OutputFactory on week 2 mission
# ------------------------------------------------------------------ #

def test_output_factory_runs_on_week2_mission(week2_orchestrator, tmp_path):
    week2_orchestrator.run()
    mission_dirs = list((tmp_path / "missions").iterdir())
    result = OutputFactory(dry_run=False).run(mission_dirs[0])
    assert result["validation"]["valid"] is True
    assert len(result["outputs_written"]) >= 4


def test_output_factory_writes_exports(week2_orchestrator, tmp_path):
    week2_orchestrator.run()
    mission_dir = list((tmp_path / "missions").iterdir())[0]
    OutputFactory(dry_run=False).run(mission_dir)
    exports = mission_dir / "06_exports"
    for fname in ["outputs_manifest.json", "files_index.md", "checksums.json", "package_report.md"]:
        assert (exports / fname).exists(), f"Missing export: {fname}"


# ------------------------------------------------------------------ #
# Learning context attachment
# ------------------------------------------------------------------ #

def test_learning_context_is_attached_when_path_provided(week2_orchestrator_with_learnings):
    result = week2_orchestrator_with_learnings.run()
    assert "learning_context" in result
    assert len(result["learning_context"]) == 3


def test_learning_context_content_is_correct(week2_orchestrator_with_learnings):
    result = week2_orchestrator_with_learnings.run()
    ctx = result["learning_context"]
    assert any("CPM" in item for item in ctx)
    assert any("DM" in item for item in ctx)


def test_learning_context_appears_in_posts(week2_orchestrator_with_learnings):
    result = week2_orchestrator_with_learnings.run()
    # Posts should contain "learning_context:" marker
    assert any("learning_context:" in p for p in result["posts"])


def test_learning_context_appears_in_stories(week2_orchestrator_with_learnings):
    result = week2_orchestrator_with_learnings.run()
    assert any("learning_context:" in s for s in result["stories"])


def test_no_learning_context_when_path_not_provided(week2_orchestrator):
    result = week2_orchestrator.run()
    assert result["learning_context"] == []


def test_with_learning_context_returns_self(tmp_path, monkeypatch, learnings_file):
    monkeypatch.chdir(tmp_path)
    orch = WeeklyPackOrchestrator(
        project="Teste", niche="test", objective="obj", city="SP", channel="ch"
    )
    returned = orch.with_learning_context(learnings_file)
    assert returned is orch


# ------------------------------------------------------------------ #
# Improvement vs week 1 noted in manifest
# ------------------------------------------------------------------ #

def test_manifest_notes_improvement_vs_week1_via_learning_context(week2_orchestrator_with_learnings, tmp_path):
    """Week 2 manifest should contain learning_context with non-empty items,
    proving previous week knowledge was reused."""
    result = week2_orchestrator_with_learnings.run()
    manifests = list(tmp_path.glob("missions/*/weekly_manifest.json"))
    data = json.loads(manifests[0].read_text(encoding="utf-8"))
    assert len(data.get("learning_context", [])) > 0, (
        "Manifest must record learning_context to prove improvement over week 1"
    )
