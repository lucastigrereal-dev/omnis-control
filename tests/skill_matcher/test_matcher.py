"""Tests for skill matcher."""
import pytest
from src.skill_matcher.matcher import match_capabilities, list_capabilities, get_capability


def test_match_carrossel_returns_carousel():
    results = match_capabilities("cria um carrossel para instagram")
    assert any(r.capability_id == "offline_package_carousel" for r in results)


def test_match_campaign():
    results = match_capabilities("quero uma campanha de 10 posts")
    assert any(r.capability_id == "campaign_package" for r in results)


def test_match_no_results_unknown_text():
    results = match_capabilities("xyzzy nonsense blah")
    assert results == []


def test_match_inactive_excluded():
    results = match_capabilities("app sistema dashboard api software saas plataforma")
    for r in results:
        assert r.requires_approval or r.risk_level != "inactive"


def test_match_high_risk_requires_approval():
    results = match_capabilities("app sistema api software")
    high_risk = [r for r in results if r.risk_level == "high"]
    for r in high_risk:
        assert r.requires_approval is True


def test_match_sector_filter():
    results = match_capabilities("campanha reels carrossel post", sector_filter="marketing")
    for r in results:
        assert r.sector == "marketing"


def test_list_capabilities_active_only():
    caps = list_capabilities(active_only=True)
    for c in caps:
        assert c.status == "active"


def test_get_capability_found():
    c = get_capability("offline_package_carousel")
    assert c is not None
    assert c.sector == "marketing"


def test_get_capability_not_found():
    assert get_capability("nonexistent_cap") is None


def test_match_returns_sorted_by_confidence():
    results = match_capabilities("campanha carrossel post instagram reels")
    if len(results) >= 2:
        for i in range(len(results) - 1):
            assert results[i].confidence >= results[i + 1].confidence
