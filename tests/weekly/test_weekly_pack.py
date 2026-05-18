"""Tests for WeeklyPackOrchestrator."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.weekly.weekly_pack import WeeklyPackOrchestrator


@pytest.fixture
def orchestrator(tmp_path, monkeypatch):
    """Return a WeeklyPackOrchestrator with missions dir inside tmp_path."""
    monkeypatch.chdir(tmp_path)
    return WeeklyPackOrchestrator(
        project="test_proj",
        niche="gastronomia",
        objective="gerar_leads",
        city="Natal",
        channel="instagram",
        dry_run=True,
    )


def test_run_returns_all_keys(orchestrator):
    result = orchestrator.run()
    expected_keys = {"project", "niche", "objective", "city", "channel", "dry_run",
                     "generated_at", "posts", "stories", "reels", "carousel", "proposal", "learning_update"}
    assert expected_keys.issubset(result.keys())


def test_posts_has_7_items(orchestrator):
    result = orchestrator.run()
    assert len(result["posts"]) == 7


def test_stories_has_7_items(orchestrator):
    result = orchestrator.run()
    assert len(result["stories"]) == 7


def test_reels_has_5_items(orchestrator):
    result = orchestrator.run()
    assert len(result["reels"]) == 5


def test_manifest_json_created(orchestrator, tmp_path):
    orchestrator.run()
    manifests = list(tmp_path.glob("missions/*/weekly_manifest.json"))
    assert len(manifests) == 1
    data = json.loads(manifests[0].read_text(encoding="utf-8"))
    assert data["project"] == "test_proj"


def test_dry_run_no_http_calls(orchestrator, monkeypatch):
    """Verify run() completes without any HTTP calls (urllib/requests/httpx)."""
    import urllib.request

    def mock_urlopen(*args, **kwargs):
        raise AssertionError("HTTP call made during dry_run!")

    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)
    result = orchestrator.run()
    assert result["dry_run"] is True


def test_all_output_files_created(orchestrator, tmp_path):
    orchestrator.run()
    mission_dirs = list((tmp_path / "missions").iterdir())
    assert len(mission_dirs) == 1
    d = mission_dirs[0]
    for fname in ["weekly_manifest.json", "posts.md", "stories.md", "reels.md",
                  "carousel.md", "proposal.md", "learning_update.md"]:
        assert (d / fname).exists(), f"Missing: {fname}"


def test_carousel_has_slides(orchestrator):
    result = orchestrator.run()
    carousel = result["carousel"]
    assert "slides" in carousel
    assert len(carousel["slides"]) >= 1


def test_proposal_has_packages(orchestrator):
    result = orchestrator.run()
    proposal = result["proposal"]
    assert "packages" in proposal
    assert len(proposal["packages"]) >= 1


def test_learning_update_has_learnings(orchestrator):
    result = orchestrator.run()
    lu = result["learning_update"]
    assert "learnings" in lu
    assert len(lu["learnings"]) >= 1
