import pytest
from src.control_tower.decision_engine import DecisionEngine
from src.control_tower.models import (
    TowerRequest, Decision, RiskLevel, ActionType, BoundarySystem,
)


class TestDecisionEngine:
    @pytest.fixture
    def engine(self):
        return DecisionEngine(dry_run=True)

    def test_evaluate_low_risk_local(self, engine):
        req = TowerRequest(
            title="Read status",
            action="read_status",
            source_system=BoundarySystem.OMNIS,
            target_system=BoundarySystem.OMNIS,
            is_external=False,
            is_destructive=False,
        )
        d = engine.evaluate(req)
        assert d.risk_level == RiskLevel.LOW
        assert d.requires_human_approval is False

    def test_evaluate_high_risk_push(self, engine):
        req = TowerRequest(
            title="Push changes",
            action="push_to_origin",
            source_system=BoundarySystem.OMNIS,
            target_system=BoundarySystem.OMNIS,
            is_external=True,
            is_destructive=False,
        )
        d = engine.evaluate(req)
        assert d.risk_level == RiskLevel.HIGH
        assert d.requires_human_approval is True
        assert d.action_type == ActionType.EXECUTE_WITH_APPROVAL

    def test_evaluate_critical_delete(self, engine):
        req = TowerRequest(
            title="Delete records",
            action="delete_records",
            source_system=BoundarySystem.OMNIS,
            target_system=BoundarySystem.OMNIS,
            is_external=False,
            is_destructive=True,
        )
        d = engine.evaluate(req)
        assert d.risk_level == RiskLevel.CRITICAL
        assert d.action_type == ActionType.BLOCK
        assert d.requires_human_approval is True

    def test_evaluate_boundary_violation(self, engine):
        req = TowerRequest(
            title="Write to KRATOS",
            action="write",
            source_system=BoundarySystem.OMNIS,
            target_system=BoundarySystem.KRATOS,
            is_external=False,
            is_destructive=False,
        )
        d = engine.evaluate(req)
        assert d.action_type == ActionType.BLOCK
        assert d.requires_human_approval is True

    def test_evaluate_medium_dry_run(self, engine):
        req = TowerRequest(
            title="Configure settings",
            action="configure_settings",
            source_system=BoundarySystem.OMNIS,
            target_system=BoundarySystem.OMNIS,
            is_external=False,
            is_destructive=False,
        )
        d = engine.evaluate(req)
        assert d.risk_level == RiskLevel.MEDIUM
        assert d.action_type == ActionType.DRY_RUN

    def test_evaluate_includes_do_not_do(self, engine):
        req = TowerRequest(
            title="Skill action",
            action="call_skill",
            source_system=BoundarySystem.OMNIS,
            target_system=BoundarySystem.SKILLS,
            is_external=False,
            is_destructive=False,
        )
        d = engine.evaluate(req)
        assert len(d.do_not_do) > 0
        assert "modify_skill" in d.do_not_do or "delete_skill" in d.do_not_do

    def test_history_accumulates(self, engine):
        req1 = TowerRequest(title="First", action="read_status")
        req2 = TowerRequest(title="Second", action="push_to_origin",
                            is_external=True)
        engine.evaluate(req1)
        engine.evaluate(req2)
        assert len(engine.get_history()) == 2

    def test_last_decision(self, engine):
        req = TowerRequest(title="Test", action="read_status")
        engine.evaluate(req)
        last = engine.last_decision()
        assert last is not None
        assert last.title == "Test"

    def test_last_decision_none_when_empty(self, engine):
        assert engine.last_decision() is None

    def test_evaluate_external_read_is_low(self, engine):
        req = TowerRequest(
            title="External read",
            action="read_external_status",
            source_system=BoundarySystem.OMNIS,
            target_system=BoundarySystem.OMNIS,
            is_external=True,
            is_destructive=False,
        )
        d = engine.evaluate(req)
        assert d.risk_level == RiskLevel.LOW
