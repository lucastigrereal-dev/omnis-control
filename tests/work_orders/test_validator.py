import pytest
from src.work_orders.models import (
    WorkOrder, WorkOrderStatus, WorkOrderDecision,
)
from src.work_orders.validator import WorkOrderValidator
from src.work_orders.errors import InvalidWorkOrderError


class TestWorkOrderValidator:
    @pytest.fixture
    def validator(self):
        return WorkOrderValidator(dry_run=True)

    def _wo(self, **kwargs):
        defaults = {
            "title": "Test",
            "type": "test",
            "status": WorkOrderStatus.READY,
            "risk": "LOW",
            "requires_approval": False,
        }
        defaults.update(kwargs)
        return WorkOrder(**defaults)

    def test_ready_low_risk_returns_ready(self, validator):
        wo = self._wo()
        assert validator.decide(wo) == WorkOrderDecision.READY

    def test_high_risk_returns_needs_approval(self, validator):
        wo = self._wo(risk="HIGH")
        assert validator.decide(wo) == WorkOrderDecision.NEEDS_APPROVAL

    def test_critical_risk_returns_needs_approval(self, validator):
        wo = self._wo(risk="CRITICAL")
        assert validator.decide(wo) == WorkOrderDecision.NEEDS_APPROVAL

    def test_waiting_returns_needs_approval(self, validator):
        wo = self._wo(status=WorkOrderStatus.WAITING)
        assert validator.decide(wo) == WorkOrderDecision.NEEDS_APPROVAL

    def test_blocked_returns_blocked(self, validator):
        wo = self._wo(status=WorkOrderStatus.BLOCKED)
        assert validator.decide(wo) == WorkOrderDecision.BLOCKED

    def test_requires_approval_returns_needs_approval(self, validator):
        wo = self._wo(requires_approval=True)
        assert validator.decide(wo) == WorkOrderDecision.NEEDS_APPROVAL

    def test_invalid_missing_title(self, validator):
        wo = self._wo(title="")
        assert validator.decide(wo) == WorkOrderDecision.INVALID

    def test_invalid_missing_type(self, validator):
        wo = self._wo(type="")
        assert validator.decide(wo) == WorkOrderDecision.INVALID

    def test_draft_returns_needs_review(self, validator):
        wo = self._wo(status=WorkOrderStatus.DRAFT)
        assert validator.decide(wo) == WorkOrderDecision.NEEDS_REVIEW

    def test_paths_conflict_returns_blocked(self, validator):
        wo = self._wo(
            allowed_paths=["src/.kratos/config.yaml"],
            forbidden_paths=["src/.kratos/"],
        )
        assert validator.decide(wo) == WorkOrderDecision.BLOCKED

    def test_validate_raises_on_invalid(self, validator):
        wo = self._wo(title="", type="")
        with pytest.raises(InvalidWorkOrderError, match="INVALID"):
            validator.validate(wo)

    def test_validate_raises_on_blocked(self, validator):
        wo = self._wo(status=WorkOrderStatus.BLOCKED)
        with pytest.raises(InvalidWorkOrderError, match="BLOCKED"):
            validator.validate(wo)

    def test_validate_passes_on_ready(self, validator):
        wo = self._wo()
        validator.validate(wo)
