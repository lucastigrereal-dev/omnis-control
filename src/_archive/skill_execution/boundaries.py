from src.skill_execution.models import (
    SkillExecutionBoundary,
    ExecutionBoundaryResult,
    BoundaryRiskLevel,
    BoundaryAction,
)

BUILT_IN_BOUNDARIES = {
    "filesystem_read": SkillExecutionBoundary(
        name="filesystem_read",
        risk=BoundaryRiskLevel.LOW,
        action=BoundaryAction.ALLOW,
        requires_permission_check=False,
        allowed_zones=["src/", "tests/", "docs/", "config/"],
        description="Leitura de arquivos do projeto",
    ),
    "filesystem_write": SkillExecutionBoundary(
        name="filesystem_write",
        risk=BoundaryRiskLevel.MEDIUM,
        action=BoundaryAction.REQUIRE_DRY_RUN,
        requires_human=False,
        requires_dry_run=True,
        requires_permission_check=True,
        allowed_zones=["src/", "tests/", "docs/"],
        forbidden_zones=[".env", "secrets/", ".kratos/"],
        description="Escrita em arquivos do projeto",
    ),
    "shell_execution": SkillExecutionBoundary(
        name="shell_execution",
        risk=BoundaryRiskLevel.HIGH,
        action=BoundaryAction.REQUIRE_APPROVAL,
        requires_human=True,
        requires_dry_run=True,
        requires_permission_check=True,
        forbidden_zones=["rm -rf", "git push", "git reset --hard", "docker rm"],
        description="Execucao de comandos shell",
    ),
    "external_api": SkillExecutionBoundary(
        name="external_api",
        risk=BoundaryRiskLevel.CRITICAL,
        action=BoundaryAction.BLOCK,
        requires_human=True,
        requires_dry_run=True,
        requires_permission_check=True,
        description="Chamadas a APIs externas — bloqueado por default",
    ),
    "secrets_access": SkillExecutionBoundary(
        name="secrets_access",
        risk=BoundaryRiskLevel.CRITICAL,
        action=BoundaryAction.BLOCK,
        requires_human=True,
        requires_dry_run=True,
        requires_permission_check=True,
        forbidden_zones=[".env", "*.key", "*.pem", "secrets/", "credentials.json"],
        description="Acesso a secrets e credenciais — bloqueado",
    ),
    "destructive_action": SkillExecutionBoundary(
        name="destructive_action",
        risk=BoundaryRiskLevel.CRITICAL,
        action=BoundaryAction.BLOCK,
        requires_human=True,
        requires_dry_run=True,
        requires_permission_check=True,
        description="Acoes destrutivas — bloqueado sem aprovacao",
    ),
}


class BoundaryChecker:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self._boundaries: dict[str, SkillExecutionBoundary] = dict(BUILT_IN_BOUNDARIES)

    def add_boundary(self, boundary: SkillExecutionBoundary) -> None:
        self._boundaries[boundary.name] = boundary

    def check(self, boundary_name: str, zone: str = "", is_destructive: bool = False) -> ExecutionBoundaryResult:
        boundary = self._boundaries.get(boundary_name)
        if boundary is None:
            return ExecutionBoundaryResult(
                boundary_id="",
                passed=False,
                action=BoundaryAction.BLOCK,
                message=f"Unknown boundary: {boundary_name}",
            )

        result = ExecutionBoundaryResult(boundary_id=boundary.boundary_id)

        if boundary.action == BoundaryAction.BLOCK:
            result.passed = False
            result.action = BoundaryAction.BLOCK
            result.message = f"{boundary_name}: blocked by policy"
            result.violations.append(boundary.description)
            return result

        if zone and boundary.forbidden_zones:
            for forbidden in boundary.forbidden_zones:
                if forbidden in zone or (forbidden.endswith("*") and zone.startswith(forbidden[:-1])):
                    result.passed = False
                    result.action = BoundaryAction.BLOCK
                    result.message = f"{boundary_name}: zone '{zone}' is forbidden"
                    result.violations.append(f"Forbidden zone: {forbidden}")
                    return result

        if is_destructive and boundary.action in (BoundaryAction.REQUIRE_APPROVAL, BoundaryAction.BLOCK):
            result.passed = False
            result.action = BoundaryAction.REQUIRE_APPROVAL
            result.message = f"{boundary_name}: destructive action requires approval"
            return result

        result.passed = True
        result.action = boundary.action
        result.message = f"{boundary_name}: allowed"
        return result

    def list_boundaries(self) -> list[SkillExecutionBoundary]:
        return list(self._boundaries.values())
