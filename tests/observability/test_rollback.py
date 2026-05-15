from src.observability.rollback import RollbackEngine
from src.observability.models import RollbackStatus


class TestRollbackEngine:
    def test_plan_reversible(self):
        engine = RollbackEngine()
        plan = engine.plan("exc_1", rollback_hint="revert commit abc123")
        assert plan.contract_id == "exc_1"
        assert plan.status == RollbackStatus.POSSIBLE
        assert plan.is_reversible is True
        assert "revert commit abc123" in plan.steps

    def test_plan_irreversible(self):
        engine = RollbackEngine()
        plan = engine.plan("exc_2", rollback_hint="This action is irreversible")
        assert plan.status == RollbackStatus.NOT_POSSIBLE
        assert plan.is_reversible is False

    def test_plan_no_hint(self):
        engine = RollbackEngine()
        plan = engine.plan("exc_3")
        assert plan.steps == []
        assert plan.is_reversible is False

    def test_can_rollback(self):
        engine = RollbackEngine()
        engine.plan("exc_ok", "git reset HEAD~1")
        engine.plan("exc_bad", "irreversible")
        assert engine.can_rollback("exc_ok") is True
        assert engine.can_rollback("exc_bad") is False
        assert engine.can_rollback("nonexistent") is False

    def test_get_plan(self):
        engine = RollbackEngine()
        engine.plan("exc_x", "undo migration")
        plan = engine.get_plan("exc_x")
        assert plan is not None
        assert plan.contract_id == "exc_x"
        assert engine.get_plan("missing") is None
