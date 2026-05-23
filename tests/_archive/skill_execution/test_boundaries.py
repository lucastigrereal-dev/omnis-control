from src.skill_execution.models import (
    SkillExecutionBoundary,
    BoundaryRiskLevel,
    BoundaryAction,
)
from src.skill_execution.boundaries import BoundaryChecker, BUILT_IN_BOUNDARIES


class TestBoundaryChecker:
    def test_has_all_builtin_boundaries(self):
        checker = BoundaryChecker()
        assert len(checker.list_boundaries()) == 6
        assert "filesystem_read" in checker._boundaries
        assert "secrets_access" in checker._boundaries
        assert "external_api" in checker._boundaries

    def test_filesystem_read_allowed(self):
        checker = BoundaryChecker()
        result = checker.check("filesystem_read", zone="src/test.py")
        assert result.passed is True
        assert result.action == BoundaryAction.ALLOW

    def test_external_api_blocked(self):
        checker = BoundaryChecker()
        result = checker.check("external_api")
        assert result.passed is False
        assert result.action == BoundaryAction.BLOCK

    def test_secrets_access_blocked(self):
        checker = BoundaryChecker()
        result = checker.check("secrets_access", zone=".env")
        assert result.passed is False
        assert result.action == BoundaryAction.BLOCK

    def test_shell_execution_requires_approval(self):
        checker = BoundaryChecker()
        result = checker.check("shell_execution", zone="git status", is_destructive=False)
        assert result.action == BoundaryAction.REQUIRE_APPROVAL

    def test_filesystem_write_with_forbidden_zone(self):
        checker = BoundaryChecker()
        result = checker.check("filesystem_write", zone=".env")
        assert result.passed is False

    def test_destructive_filesystem_write(self):
        checker = BoundaryChecker()
        result = checker.check("filesystem_write", zone="src/data.py", is_destructive=True)
        assert result.passed is True
        assert result.action == BoundaryAction.REQUIRE_DRY_RUN

    def test_unknown_boundary(self):
        checker = BoundaryChecker()
        result = checker.check("nonexistent")
        assert result.passed is False
        assert result.action == BoundaryAction.BLOCK

    def test_add_custom_boundary(self):
        checker = BoundaryChecker()
        custom = SkillExecutionBoundary(
            name="custom_test",
            risk=BoundaryRiskLevel.LOW,
            action=BoundaryAction.ALLOW,
        )
        checker.add_boundary(custom)
        result = checker.check("custom_test")
        assert result.passed is True

    def test_shell_with_rm_rf_is_blocked(self):
        checker = BoundaryChecker()
        result = checker.check("shell_execution", zone="rm -rf /")
        assert result.passed is False
        assert result.action == BoundaryAction.BLOCK
