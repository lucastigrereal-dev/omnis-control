"""Tests for sector matcher."""
import pytest
from src.sector_registry.matcher import match_sector, list_sectors, get_sector


def test_match_marketing_carrossel():
    result = match_sector("cria um carrossel com reels e post para campanha")
    assert result is not None
    assert result.sector_id == "marketing"


def test_match_marketing_reels():
    result = match_sector("quero um reels instagram stories carrossel")
    assert result is not None
    assert result.sector_id == "marketing"


def test_match_apps():
    result = match_sector("desenvolver um sistema de dashboard para o app")
    assert result is not None
    assert result.sector_id == "apps"


def test_match_returns_none_no_keywords():
    result = match_sector("xyzzy nonsense blah")
    assert result is None


def test_match_confidence_between_0_and_1():
    result = match_sector("cria um post de campanha")
    if result is not None:
        assert 0.0 <= result.confidence <= 1.0


def test_match_risk_level_valid():
    result = match_sector("reels hotel instagram")
    if result:
        assert result.risk_level in ("low", "medium", "high")


def test_list_sectors_returns_all():
    sectors = list_sectors()
    assert len(sectors) >= 5


def test_get_sector_found():
    s = get_sector("marketing")
    assert s is not None
    assert s.sector_id == "marketing"


def test_get_sector_not_found():
    assert get_sector("nonexistent_sector") is None


def test_match_accent_insensitive():
    result = match_sector("publicação de conteúdo")
    assert result is not None
    assert result.sector_id == "marketing"
