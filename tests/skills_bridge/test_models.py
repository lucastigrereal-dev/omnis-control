import pytest
from src.skills_bridge.models import SkillCall, SkillSelection, SkillIntent


class TestSkillCall:
    def test_new_call_defaults(self):
        c = SkillCall()
        assert c.call_id.startswith("skc_")
        assert c.dry_run is True
        assert c.risk_level == "LOW"
        assert c.requires_approval is False

    def test_call_with_intent(self):
        c = SkillCall(
            skill_id="jarvis-router",
            intent=SkillIntent.ANALYZE,
            input_payload={"text": "route this"},
            risk_level="MEDIUM",
            tags=["router", "classify"],
        )
        assert c.intent == SkillIntent.ANALYZE
        assert c.risk_level == "MEDIUM"
        assert "router" in c.tags

    def test_to_dict(self):
        c = SkillCall(skill_id="test-skill", intent=SkillIntent.CREATE)
        d = c.to_dict()
        assert d["skill_id"] == "test-skill"
        assert d["intent"] == "create"


class TestSkillSelection:
    def test_new_selection_defaults(self):
        s = SkillSelection()
        assert s.selection_id.startswith("sks_")
        assert s.confidence == 0.0
        assert s.requires_manual_review is False

    def test_direct_match(self):
        s = SkillSelection(
            skill_id="jarvis-router",
            skill_name="Jarvis Router",
            confidence=1.0,
            reason="Direct match",
        )
        assert s.skill_id == "jarvis-router"
        assert s.confidence == 1.0

    def test_fallback_selection(self):
        s = SkillSelection(
            skill_id="manual-review",
            skill_name="Manual Review",
            requires_manual_review=True,
            reason="No match",
        )
        assert s.requires_manual_review is True
        assert s.confidence == 0.0

    def test_to_dict(self):
        s = SkillSelection(
            skill_id="test-skill",
            skill_name="Test Skill",
            intent=SkillIntent.GENERATE,
            confidence=0.8,
            fallback_skill_id="manual-review",
        )
        d = s.to_dict()
        assert d["skill_id"] == "test-skill"
        assert d["confidence"] == 0.8
