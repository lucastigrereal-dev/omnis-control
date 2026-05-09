from src.skill_matcher.models import Capability, SkillMatchResult


def test_capability_to_dict():
    c = Capability("offline_package_carousel", "marketing", "jarvis offline", "carousel_package", "low", "active", ["carrossel"])
    d = c.to_dict()
    assert d["capability_id"] == "offline_package_carousel"
    assert d["risk_level"] == "low"


def test_skill_match_result_requires_approval_high():
    r = SkillMatchResult("app_factory_spec", "apps", "cmd", "spec", "high", ["app"], 0.5, True)
    assert r.requires_approval is True


def test_skill_match_result_no_approval_low():
    r = SkillMatchResult("offline_package_carousel", "marketing", "cmd", "carousel", "low", ["carrossel"], 0.5, False)
    assert r.requires_approval is False
