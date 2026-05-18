"""Tests for template registry populate module."""

import json
from pathlib import Path

import pytest

from src.template_registry.populate import run, _read_json


def test_populate_dry_run():
    """Populate in dry_run should return summary without writing files."""
    result = run(dry_run=True)
    assert result["dry_run"] is True
    assert "total_entries" in result
    assert result["total_entries"] >= 22  # 6 captions + 5 squads + 11 missions min


def test_populate_produces_registry_file():
    """Full populate writes registry and template files."""
    result = run(dry_run=False)
    assert result["dry_run"] is False
    assert result["total_entries"] >= 22

    registry_path = Path(result["registry_path"])
    assert registry_path.is_file()

    data = json.loads(registry_path.read_text(encoding="utf-8"))
    assert "templates" in data
    assert "total" in data
    assert data["total"] == result["total_entries"]


def test_populated_templates_have_files():
    """Templates should have their JSON files created."""
    result = run(dry_run=False)
    templates_dir = Path("templates")

    # Check a few known template files exist
    assert (templates_dir / "marketing" / "marketing_caption_alcance_reels.json").is_file()
    assert (templates_dir / "ops" / "squad_marketing.json").is_file()


def test_read_json_missing():
    assert _read_json(Path("/nonexistent/path.json")) is None
