"""Tests for Role Registry models."""
from src.role_registry.models import Role, RoleMatchResult


def test_role_matches_sector():
    r = Role("copywriter", "Copywriter", ["marketing", "sales"], [], [], "low")
    assert r.matches_sector("marketing") is True
    assert r.matches_sector("apps") is False


def test_role_matches_output():
    r = Role("copywriter", "Copywriter", ["marketing"], [], ["caption", "script"], "low")
    assert r.matches_output("caption") is True
    assert r.matches_output("prd") is False


def test_role_match_result_fields():
    rm = RoleMatchResult("qa_auditor", "QA Auditor", ["apps"], ["quality_report"], "low", "covers sector 'apps'")
    assert rm.role_id == "qa_auditor"
    assert rm.reason == "covers sector 'apps'"
