from src.skill_execution.models import (
    SkillExecutionBoundary,
    ExecutionBoundaryResult,
    BoundaryRiskLevel,
    BoundaryAction,
)


class TestSkillExecutionBoundary:
    def test_default_boundary(self):
        b = SkillExecutionBoundary()
        assert b.boundary_id.startswith("seb_")
        assert b.risk == BoundaryRiskLevel.NONE
        assert b.action == BoundaryAction.ALLOW
        assert b.requires_human is False
        assert b.requires_dry_run is False

    def test_critical_boundary(self):
        b = SkillExecutionBoundary(
            name="secrets",
            risk=BoundaryRiskLevel.CRITICAL,
            action=BoundaryAction.BLOCK,
            requires_human=True,
            requires_dry_run=True,
            forbidden_zones=[".env", "secrets/"],
        )
        assert b.risk == BoundaryRiskLevel.CRITICAL
        assert b.action == BoundaryAction.BLOCK
        assert ".env" in b.forbidden_zones

    def test_roundtrip(self):
        b = SkillExecutionBoundary(
            name="test",
            risk=BoundaryRiskLevel.HIGH,
            action=BoundaryAction.REQUIRE_APPROVAL,
            requires_human=True,
            allowed_zones=["src/"],
            forbidden_zones=[".env"],
        )
        data = b.to_dict()
        b2 = SkillExecutionBoundary.from_dict(data)
        assert b2.name == "test"
        assert b2.risk == BoundaryRiskLevel.HIGH
        assert b2.allowed_zones == ["src/"]
        assert b2.forbidden_zones == [".env"]


class TestExecutionBoundaryResult:
    def test_default_result(self):
        r = ExecutionBoundaryResult()
        assert r.result_id.startswith("ebr_")
        assert r.passed is False
        assert r.action == BoundaryAction.BLOCK

    def test_passed_result(self):
        r = ExecutionBoundaryResult(
            passed=True,
            action=BoundaryAction.ALLOW,
            message="All good",
        )
        assert r.passed is True
        assert r.action == BoundaryAction.ALLOW
        assert r.violations == []

    def test_failed_with_violations(self):
        r = ExecutionBoundaryResult(
            passed=False,
            action=BoundaryAction.BLOCK,
            message="Forbidden zone",
            violations=[".env access denied"],
        )
        assert len(r.violations) == 1

    def test_result_roundtrip(self):
        r = ExecutionBoundaryResult(
            boundary_id="seb_test",
            passed=True,
            action=BoundaryAction.ALLOW,
            message="ok",
        )
        data = r.to_dict()
        assert data["passed"] is True
        assert data["action"] == "ALLOW"
