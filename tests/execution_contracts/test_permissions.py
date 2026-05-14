import pytest
from src.execution_contracts.models import ExecutionContract, ContractStatus
from src.execution_contracts.permissions import PermissionChecker
from src.execution_contracts.errors import PermissionError


class TestPermissionChecker:
    @pytest.fixture
    def checker(self):
        return PermissionChecker(dry_run=True)

    def _contract(self, **kwargs):
        defaults = {
            "title": "Test",
            "project": "omnis",
            "target_system": "omnis",
            "allowed_actions": ["read", "test", "build"],
            "forbidden_actions": ["delete", "push"],
            "requires_approval": False,
            "dry_run_required": True,
        }
        defaults.update(kwargs)
        return ExecutionContract(**defaults)

    def test_allowed_action_passes(self, checker):
        c = self._contract()
        assert checker.check_action(c, "read") is True

    def test_forbidden_action_blocked(self, checker):
        c = self._contract()
        assert checker.check_action(c, "delete") is False

    def test_unknown_action_blocked_when_allowlist(self, checker):
        c = self._contract()
        assert checker.check_action(c, "unknown") is False

    def test_approval_required_not_approved_raises(self, checker):
        c = self._contract(requires_approval=True, status=ContractStatus.DRAFT)
        with pytest.raises(PermissionError):
            checker.check_approval(c)

    def test_approval_executing_passes(self, checker):
        c = self._contract(requires_approval=True, status=ContractStatus.EXECUTING)
        checker.check_approval(c)

    def test_dry_run_required_not_executed_raises(self, checker):
        c = self._contract(dry_run_required=True, status=ContractStatus.DRAFT)
        with pytest.raises(PermissionError):
            checker.check_dry_run(c)

    def test_dry_run_executing_passes(self, checker):
        c = self._contract(dry_run_required=True, status=ContractStatus.EXECUTING)
        checker.check_dry_run(c)

    def test_check_all_good(self, checker):
        c = self._contract(status=ContractStatus.EXECUTING)
        issues = checker.check_all(c, action="read")
        assert len(issues) == 0

    def test_check_all_forbidden_action(self, checker):
        c = self._contract()
        issues = checker.check_all(c, action="delete")
        assert any("not permitted" in i for i in issues)
