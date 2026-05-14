import pytest
from src.execution_contracts.models import (
    ExecutionContract, ContractOutcome, ContractStatus, OutcomeStatus,
)


class TestExecutionContract:
    def test_new_contract_defaults(self):
        c = ExecutionContract(title="Test")
        assert c.contract_id.startswith("exc_")
        assert c.status == ContractStatus.DRAFT
        assert c.dry_run_required is True
        assert c.requires_approval is False

    def test_allowed_and_forbidden_paths(self):
        c = ExecutionContract(
            title="Test",
            project="omnis",
            target_system="omnis",
            allowed_paths=["src/omnis_os/", "tests/omnis_os/"],
            forbidden_paths=["src/.kratos/", "C:\\Users\\lucas\\.kratos"],
            allowed_actions=["read", "test", "build"],
            forbidden_actions=["delete", "push", "merge"],
        )
        assert len(c.allowed_paths) == 2
        assert len(c.forbidden_paths) == 2
        assert len(c.allowed_actions) == 3
        assert len(c.forbidden_actions) == 3

    def test_to_dict_roundtrip(self):
        c = ExecutionContract(
            title="Full Contract",
            project="test",
            target_system="skills",
            allowed_paths=["src/test/"],
            forbidden_paths=["src/.kratos/"],
            allowed_actions=["read", "dry_run"],
            forbidden_actions=["delete"],
            requires_approval=True,
            dry_run_required=True,
            rollback_hint="git restore",
            report_path="docs/report.md",
        )
        data = c.to_dict()
        restored = ExecutionContract.from_dict(data)
        assert restored.title == c.title
        assert restored.project == c.project
        assert restored.requires_approval is True
        assert restored.allowed_paths == c.allowed_paths
        assert restored.forbidden_actions == c.forbidden_actions

    def test_acceptance_criteria(self):
        c = ExecutionContract(
            title="Test",
            project="omnis",
            target_system="omnis",
            acceptance_criteria=[
                "All tests pass",
                "No external files modified",
                "Report generated",
            ],
        )
        assert len(c.acceptance_criteria) == 3

    def test_expected_outputs(self):
        c = ExecutionContract(
            title="Test",
            project="omnis",
            target_system="omnis",
            expected_outputs=["Test report", "Decision log"],
        )
        assert "Decision log" in c.expected_outputs


class TestContractOutcome:
    def test_new_outcome_defaults(self):
        o = ContractOutcome()
        assert o.outcome_id.startswith("exo_")
        assert o.status == OutcomeStatus.PLANNED

    def test_all_tests_passed_true(self):
        o = ContractOutcome(tests_run=10, tests_passed=10)
        assert o.all_tests_passed is True

    def test_all_tests_passed_false(self):
        o = ContractOutcome(tests_run=10, tests_passed=8)
        assert o.all_tests_passed is False

    def test_all_tests_passed_zero(self):
        o = ContractOutcome(tests_run=0, tests_passed=0)
        assert o.all_tests_passed is False

    def test_to_dict(self):
        o = ContractOutcome(
            contract_id="exc_test",
            status=OutcomeStatus.DRY_RUN_OK,
            summary="Dry run OK",
            changed_files=["src/test.py"],
            tests_run=5,
            tests_passed=5,
            reports_generated=["docs/test.md"],
            next_recommendation="Proceed",
        )
        d = o.to_dict()
        assert d["status"] == "DRY_RUN_OK"
        assert d["tests_run"] == 5
