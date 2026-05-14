import pytest
from src.work_orders.models import WorkOrder, WorkOrderStatus
from src.work_orders.mapper import WorkOrderMapper
from src.execution_contracts.models import ContractStatus


class TestWorkOrderMapper:
    @pytest.fixture
    def mapper(self):
        return WorkOrderMapper(dry_run=True)

    def test_to_contract_basic(self, mapper):
        wo = WorkOrder(
            title="Test Order",
            aba="aba-1",
            type="test",
            project="omnis-control",
            allowed_paths=["src/test/"],
            forbidden_paths=["src/.kratos/"],
        )
        contract = mapper.to_contract(wo)
        assert contract.title == "Test Order"
        assert contract.project == "omnis-control"
        assert contract.requested_by == "aba-1"
        assert contract.target_system == "test"
        assert contract.dry_run_required is True
        assert contract.allowed_paths == ["src/test/"]
        assert contract.forbidden_paths == ["src/.kratos/"]

    def test_to_contract_high_risk(self, mapper):
        wo = WorkOrder(
            title="Deploy",
            risk="HIGH",
            requires_approval=True,
            dry_run=False,
            aba="aba-0",
            type="deploy",
            project="omnis",
        )
        contract = mapper.to_contract(wo)
        assert contract.requires_approval is True
        assert contract.dry_run_required is False
        assert "rollback" in contract.rollback_hint.lower()

    def test_to_contract_defaults(self, mapper):
        wo = WorkOrder(title="", aba="", type="", project="")
        contract = mapper.to_contract(wo)
        assert contract.project == "omnis"
        assert contract.target_system == "omnis"
