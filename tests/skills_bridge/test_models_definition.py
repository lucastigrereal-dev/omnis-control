from src.skills_bridge.models import (
    SkillDefinition,
    SkillCall,
    SkillSelectorResult,
    SkillRisk,
    SkillIntent,
)


class TestSkillRisk:
    def test_values(self):
        assert SkillRisk.LOW == "LOW"
        assert SkillRisk.CRITICAL == "CRITICAL"
        assert SkillRisk("MEDIUM") == SkillRisk.MEDIUM


class TestSkillDefinition:
    def test_defaults(self):
        sd = SkillDefinition()
        assert sd.skill_id == ""
        assert sd.tier == "core"
        assert sd.risk == SkillRisk.LOW
        assert sd.tags == []

    def test_from_dict(self):
        data = {
            "skill_id": "seogram",
            "name": "SEOgram",
            "description": "Generate SEO-optimized Instagram captions",
            "tier": "core",
            "risk": "LOW",
            "tags": ["instagram", "seo", "caption"],
        }
        sd = SkillDefinition.from_dict(data)
        assert sd.skill_id == "seogram"
        assert sd.name == "SEOgram"
        assert sd.tags == ["instagram", "seo", "caption"]

    def test_from_dict_with_id_alias(self):
        sd = SkillDefinition.from_dict({"id": "alt_id", "name": "Alt"})
        assert sd.skill_id == "alt_id"

    def test_to_dict_round_trip(self):
        sd = SkillDefinition(
            skill_id="s1",
            name="Test",
            description="Desc",
            tier="strategy",
            risk=SkillRisk.HIGH,
            requires_approval=True,
            tags=["a", "b"],
        )
        data = sd.to_dict()
        assert data["skill_id"] == "s1"
        assert data["risk"] == "HIGH"
        assert data["tags"] == ["a", "b"]


class TestSkillCall:
    def test_defaults(self):
        call = SkillCall()
        assert call.call_id.startswith("skc_")
        assert call.dry_run is True
        assert call.payload == {}

    def test_from_dict(self):
        call = SkillCall.from_dict({
            "call_id": "skc_x",
            "skill_id": "seogram",
            "intent": "create",
            "dry_run": False,
        })
        assert call.skill_id == "seogram"
        assert call.intent == SkillIntent.CREATE
        assert call.dry_run is False

    def test_to_dict_round_trip(self):
        call = SkillCall(
            skill_id="test-skill",
            intent="generate",
            payload={"key": "val"},
        )
        data = call.to_dict()
        assert data["skill_id"] == "test-skill"
        assert data["intent"] == "generate"


class TestSkillSelectorResult:
    def test_defaults(self):
        result = SkillSelectorResult()
        assert result.result_id.startswith("ssr_")
        assert result.confidence == 0.0
        assert result.fallback is False

    def test_is_high_confidence(self):
        assert SkillSelectorResult(confidence=0.9).is_high_confidence is True
        assert SkillSelectorResult(confidence=0.5).is_high_confidence is False
        assert SkillSelectorResult(confidence=0.8).is_high_confidence is True

    def test_to_dict(self):
        result = SkillSelectorResult(
            selected_skill_id="s1",
            confidence=0.95,
            alternatives=["s2"],
            reason="matched",
        )
        data = result.to_dict()
        assert data["selected_skill_id"] == "s1"
        assert data["confidence"] == 0.95
        assert data["reason"] == "matched"
