import pytest
from src.control_tower.boundaries import BoundaryGuard, DEFAULT_BOUNDARIES
from src.control_tower.models import BoundarySystem, BoundaryRule
from src.control_tower.errors import BoundaryViolationError


class TestBoundaryGuard:
    @pytest.fixture
    def guard(self):
        return BoundaryGuard(dry_run=True)

    def test_omnis_can_read_kratos_status(self, guard):
        assert guard.check(
            BoundarySystem.OMNIS, BoundarySystem.KRATOS, "read_status"
        ) is True

    def test_omnis_cannot_write_kratos(self, guard):
        assert guard.check(
            BoundarySystem.OMNIS, BoundarySystem.KRATOS, "write"
        ) is False

    def test_omnis_cannot_delete_kratos(self, guard):
        assert guard.check(
            BoundarySystem.OMNIS, BoundarySystem.KRATOS, "delete"
        ) is False

    def test_omnis_can_query_akasha(self, guard):
        assert guard.check(
            BoundarySystem.OMNIS, BoundarySystem.AKASHA, "query"
        ) is True

    def test_omnis_cannot_delete_akasha(self, guard):
        assert guard.check(
            BoundarySystem.OMNIS, BoundarySystem.AKASHA, "delete_memory"
        ) is False

    def test_omnis_can_dry_run_skill(self, guard):
        assert guard.check(
            BoundarySystem.OMNIS, BoundarySystem.SKILLS, "dry_run_skill"
        ) is True

    def test_omnis_cannot_modify_skill(self, guard):
        assert guard.check(
            BoundarySystem.OMNIS, BoundarySystem.SKILLS, "modify_skill"
        ) is False

    def test_omnis_can_request_approval_from_lucas(self, guard):
        assert guard.check(
            BoundarySystem.OMNIS, BoundarySystem.LUCAS, "request_approval"
        ) is True

    def test_omnis_cannot_decide_for_lucas(self, guard):
        assert guard.check(
            BoundarySystem.OMNIS, BoundarySystem.LUCAS, "decide"
        ) is False

    def test_guard_raises_on_violation(self, guard):
        with pytest.raises(BoundaryViolationError):
            guard.guard(
                BoundarySystem.OMNIS, BoundarySystem.KRATOS, "delete"
            )

    def test_guard_passes_on_allowed(self, guard):
        guard.guard(
            BoundarySystem.OMNIS, BoundarySystem.KRATOS, "health_check"
        )

    def test_get_forbidden_actions(self, guard):
        forbidden = guard.get_forbidden_actions(
            BoundarySystem.OMNIS, BoundarySystem.KRATOS
        )
        assert "write" in forbidden
        assert "delete" in forbidden

    def test_get_allowed_actions(self, guard):
        allowed = guard.get_allowed_actions(
            BoundarySystem.OMNIS, BoundarySystem.SKILLS
        )
        assert "call_skill" in allowed

    def test_default_boundaries_has_entries(self):
        assert len(DEFAULT_BOUNDARIES) >= 5

    def test_custom_boundaries(self):
        custom = [
            BoundaryRule(
                source_system=BoundarySystem.AURORA,
                target_system=BoundarySystem.OMNIS,
                allowed_actions=["create_work_order"],
                forbidden_actions=["execute"],
            ),
        ]
        guard = BoundaryGuard(boundaries=custom)
        assert guard.check(
            BoundarySystem.AURORA, BoundarySystem.OMNIS, "create_work_order"
        ) is True
        assert guard.check(
            BoundarySystem.AURORA, BoundarySystem.OMNIS, "execute"
        ) is False
