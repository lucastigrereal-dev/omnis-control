import pytest
from src.skills_bridge.models import SkillCall, SkillIntent
from src.skills_bridge.adapter import MockSkillAdapter


class TestMockSkillAdapter:
    @pytest.fixture
    def adapter(self):
        return MockSkillAdapter(dry_run=True)

    def test_call_skill_by_id(self, adapter):
        call = SkillCall(skill_id="jarvis-router", intent=SkillIntent.ANALYZE)
        result = adapter.call_skill(call)
        assert result["status"] == "dry_run_completed"

    def test_call_skill_by_intent(self, adapter):
        call = SkillCall(intent=SkillIntent.GENERATE)
        result = adapter.call_skill(call)
        assert result["status"] == "dry_run_completed"

    def test_call_skill_unknown_fallback(self, adapter):
        call = SkillCall(skill_id="does-not-exist")
        result = adapter.call_skill(call)
        assert result["status"] == "needs_manual_review"

    def test_health_check(self, adapter):
        assert adapter.health_check() is True

    def test_calls_accumulate(self, adapter):
        adapter.call_skill(SkillCall(skill_id="jarvis-router"))
        adapter.call_skill(SkillCall(skill_id="jarvis-brain"))
        assert len(adapter.calls) == 2
