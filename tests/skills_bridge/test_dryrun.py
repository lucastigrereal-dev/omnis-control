import pytest
from src.skills_bridge.models import SkillCall, SkillIntent
from src.skills_bridge.dryrun import DryRunEngine
from src.skills_bridge.errors import DryRunError


class TestDryRunEngine:
    @pytest.fixture
    def engine(self):
        return DryRunEngine(dry_run=True)

    def test_execute_dry_run(self, engine):
        call = SkillCall(
            skill_id="jarvis-router",
            intent=SkillIntent.ANALYZE,
            dry_run=True,
            risk_level="LOW",
            expected_artifacts=["route_decision.json"],
            input_payload={"text": "test"},
        )
        result = engine.execute(call)
        assert result["status"] == "dry_run_completed"
        assert result["dry_run"] is True
        assert len(engine.get_records()) == 1

    def test_execute_non_dry_run_low_risk(self, engine):
        call = SkillCall(
            skill_id="jarvis-router",
            intent=SkillIntent.READ,
            dry_run=False,
            risk_level="LOW",
        )
        result = engine.execute(call)
        assert result["status"] == "dry_run_completed"
        assert result["dry_run"] is False

    def test_execute_non_dry_run_high_risk_raises(self, engine):
        call = SkillCall(
            skill_id="critical-skill",
            intent=SkillIntent.DELETE,
            dry_run=False,
            risk_level="HIGH",
        )
        with pytest.raises(DryRunError, match="HIGH"):
            engine.execute(call)

    def test_records_accumulate(self, engine):
        for i in range(3):
            engine.execute(SkillCall(skill_id=f"skill-{i}", intent=SkillIntent.READ))
        assert len(engine.get_records()) == 3

    def test_clear_records(self, engine):
        engine.execute(SkillCall(skill_id="test", intent=SkillIntent.READ))
        assert len(engine.get_records()) == 1
        engine.clear()
        assert len(engine.get_records()) == 0

    def test_artifacts_in_result(self, engine):
        call = SkillCall(
            skill_id="create_carousel",
            intent=SkillIntent.CREATE,
            expected_artifacts=["carousel.html", "manifest.json"],
        )
        result = engine.execute(call)
        assert "carousel.html" in result["artifacts_simulated"]
