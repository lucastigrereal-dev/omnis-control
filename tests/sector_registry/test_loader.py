"""Tests for sector loader."""
import pytest
from pathlib import Path
from src.sector_registry.loader import load_sectors
from src.sector_registry.errors import InvalidSectorConfigError


def test_load_sectors_default():
    sectors = load_sectors()
    assert len(sectors) >= 5
    ids = [s.sector_id for s in sectors]
    assert "marketing" in ids
    assert "sales" in ids


def test_load_sectors_all_have_required_fields():
    sectors = load_sectors()
    for s in sectors:
        assert s.sector_id
        assert s.name
        assert isinstance(s.keywords, list)
        assert len(s.keywords) > 0
        assert s.risk_level in ("low", "medium", "high")


def test_load_sectors_missing_file():
    with pytest.raises(InvalidSectorConfigError):
        load_sectors(Path("/nonexistent/sectors.yaml"))


def test_load_sectors_invalid_yaml(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("sectors: [broken: yaml", encoding="utf-8")
    with pytest.raises(InvalidSectorConfigError):
        load_sectors(bad)


def test_load_sectors_missing_sectors_key(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("other_key:\n  foo: bar\n", encoding="utf-8")
    with pytest.raises(InvalidSectorConfigError):
        load_sectors(bad)
