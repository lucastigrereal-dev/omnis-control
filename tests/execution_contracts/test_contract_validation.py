import pytest
from src.execution_contracts.models import ExecutionContract
from src.execution_contracts.validators import ContractValidator


class TestContractValidator:
    @pytest.fixture
    def validator(self):
        return ContractValidator(dry_run=True)

    def _valid_contract(self):
        return ExecutionContract(
            title="Valid Contract",
            project="omnis",
            target_system="omnis",
            allowed_paths=["src/test/"],
            allowed_actions=["read"],
        )

    def test_valid_contract_passes(self, validator):
        c = self._valid_contract()
        errors = validator.validate(c)
        assert len(errors) == 0
        assert validator.is_valid(c) is True

    def test_missing_title(self, validator):
        c = ExecutionContract(
            title="",
            project="test",
            target_system="omnis",
            allowed_actions=["read"],
        )
        errors = validator.validate(c)
        assert any("title" in e.lower() for e in errors)

    def test_missing_project(self, validator):
        c = ExecutionContract(
            title="Test",
            project="",
            target_system="omnis",
            allowed_actions=["read"],
        )
        errors = validator.validate(c)
        assert any("project" in e.lower() for e in errors)

    def test_missing_target_system(self, validator):
        c = ExecutionContract(
            title="Test",
            project="test",
            target_system="",
            allowed_actions=["read"],
        )
        errors = validator.validate(c)
        assert any("target_system" in e.lower() for e in errors)

    def test_no_actions_or_paths(self, validator):
        c = ExecutionContract(
            title="Test",
            project="test",
            target_system="omnis",
        )
        errors = validator.validate(c)
        assert len(errors) > 0

    def test_allowed_inside_forbidden(self, validator):
        c = ExecutionContract(
            title="Test",
            project="test",
            target_system="omnis",
            allowed_paths=["src/.kratos/config.yaml"],
            forbidden_paths=["src/.kratos/"],
            allowed_actions=["read"],
        )
        errors = validator.validate(c)
        assert len(errors) > 0

    def test_check_path_allowed_inside(self, validator):
        c = ExecutionContract(
            title="Test",
            project="test",
            target_system="omnis",
            allowed_paths=["src/test/"],
        )
        assert validator.check_path_allowed(c, "src/test/file.py") is True

    def test_check_path_allowed_outside(self, validator):
        c = ExecutionContract(
            title="Test",
            project="test",
            target_system="omnis",
            allowed_paths=["src/test/"],
        )
        assert validator.check_path_allowed(c, "src/other/file.py") is False

    def test_check_path_forbidden(self, validator):
        c = ExecutionContract(
            title="Test",
            project="test",
            target_system="omnis",
            allowed_actions=["read"],
            forbidden_paths=["src/.kratos/"],
        )
        assert validator.check_path_forbidden(c, "src/.kratos/file.md") is True

    def test_check_path_not_forbidden(self, validator):
        c = ExecutionContract(
            title="Test",
            project="test",
            target_system="omnis",
            allowed_actions=["read"],
            forbidden_paths=["src/.kratos/"],
        )
        assert validator.check_path_forbidden(c, "src/test/file.py") is False
