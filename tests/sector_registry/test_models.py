"""Tests for Sector and SectorMatchResult models."""
from src.sector_registry.models import Sector, SectorMatchResult


def test_sector_to_dict():
    s = Sector("marketing", "Marketing", ["post", "reels"], ["campaign_package"], "low")
    d = s.to_dict()
    assert d["sector_id"] == "marketing"
    assert d["risk_level"] == "low"
    assert "post" in d["keywords"]


def test_match_result_to_dict():
    r = SectorMatchResult("marketing", "Marketing Premium", ["post"], 0.5, "low", ["campaign_package"])
    d = r.to_dict()
    assert d["sector_id"] == "marketing"
    assert d["confidence"] == 0.5
