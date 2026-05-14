import pytest
from src.skills_bridge.models import SkillCall, SkillIntent
from src.skills_bridge.selection import SkillSelector


class TestSkillSelector:
    @pytest.fixture
    def selector(self):
        return SkillSelector(dry_run=True)

    def test_select_by_id_direct_match(self, selector):
        call = SkillCall(skill_id="jarvis-router")
        sel = selector.select(call)
        assert sel.skill_id == "jarvis-router"
        assert sel.confidence == 1.0
        assert sel.requires_manual_review is False

    def test_select_by_id_not_found(self, selector):
        call = SkillCall(skill_id="nonexistent-skill")
        sel = selector.select(call)
        assert sel.requires_manual_review is True
        assert sel.skill_id == "manual-review"

    def test_select_by_intent_create(self, selector):
        call = SkillCall(intent=SkillIntent.CREATE)
        sel = selector.select(call)
        assert sel.intent == SkillIntent.CREATE
        assert sel.requires_manual_review is False

    def test_select_by_intent_unknown_fallback(self, selector):
        call = SkillCall(intent=SkillIntent.UNKNOWN)
        sel = selector.select(call)
        assert sel.requires_manual_review is True

    def test_select_by_tags_match(self, selector):
        call = SkillCall(tags=["seo", "caption", "instagram"])
        sel = selector.select(call)
        assert sel.skill_id == "generate_seogram_caption"
        assert sel.requires_manual_review is False

    def test_select_by_tags_no_match(self, selector):
        call = SkillCall(tags=["nonexistent-tag"])
        sel = selector.select(call)
        assert sel.requires_manual_review is True

    def test_select_by_tags_carousel(self, selector):
        call = SkillCall(tags=["carousel", "design"])
        sel = selector.select(call)
        assert sel.skill_id == "create_instagram_carousel"

    def test_select_by_project(self, selector):
        sel = selector.select_by_project("finance-revenue", SkillIntent.READ)
        assert sel.intent == SkillIntent.READ
        assert sel.requires_manual_review is False
