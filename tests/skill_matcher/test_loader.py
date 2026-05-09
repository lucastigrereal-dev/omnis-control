import pytest
from pathlib import Path
from src.skill_matcher.loader import load_capabilities
from src.skill_matcher.errors import InvalidCapabilitiesConfigError


def test_load_capabilities_default():
    caps = load_capabilities()
    assert len(caps) >= 5


def test_load_capabilities_all_have_fields():
    for c in load_capabilities():
        assert c.capability_id
        assert c.sector
        assert c.risk_level in ("low", "medium", "high")
        assert c.status in ("active", "inactive")


def test_load_capabilities_missing_file():
    with pytest.raises(InvalidCapabilitiesConfigError):
        load_capabilities(Path("/nonexistent/caps.yaml"))


def test_load_capabilities_missing_key(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("other: {}\n", encoding="utf-8")
    with pytest.raises(InvalidCapabilitiesConfigError):
        load_capabilities(bad)
