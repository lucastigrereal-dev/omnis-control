import pytest
from src.execution_contracts.models import ExecutionContract, OutcomeStatus
from src.execution_contracts.outcomes import OutcomeGenerator


class TestOutcomeGenerator:
    @pytest.fixture
    def generator(self):
        return OutcomeGenerator(dry_run=True)

    @pytest.fixture
    def contract(self):
        return ExecutionContract(
            title="Test Contract",
            project="omnis",
            target_system="omnis",
            allowed_actions=["read"],
        )

    def test_planned(self, generator, contract):
        o = generator.planned(contract)
        assert o.status == OutcomeStatus.PLANNED
        assert o.contract_id == contract.contract_id

    def test_dry_run_ok(self, generator, contract):
        o = generator.dry_run_ok(contract, changed_files=["src/test.py"])
        assert o.status == OutcomeStatus.DRY_RUN_OK
        assert "src/test.py" in o.changed_files

    def test_blocked(self, generator, contract):
        o = generator.blocked(contract, reason="Forbidden path detected")
        assert o.status == OutcomeStatus.BLOCKED
        assert len(o.errors) > 0

    def test_executed(self, generator, contract):
        o = generator.executed(
            contract,
            tests_run=10,
            tests_passed=10,
            changed_files=["src/new.py"],
            reports=["docs/report.md"],
        )
        assert o.status == OutcomeStatus.EXECUTED
        assert o.tests_run == 10
        assert o.tests_passed == 10
        assert o.all_tests_passed is True

    def test_needs_approval(self, generator, contract):
        o = generator.needs_approval(contract)
        assert o.status == OutcomeStatus.NEEDS_APPROVAL

    def test_failed(self, generator, contract):
        o = generator.failed(contract, errors=["Connection refused"])
        assert o.status == OutcomeStatus.FAILED
        assert "Connection refused" in o.errors
