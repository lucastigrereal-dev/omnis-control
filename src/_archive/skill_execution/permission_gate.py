from src.skill_execution.request import SkillExecutionRequest, SkillExecutionRisk
from src.skill_execution.result import SkillExecutionResult, ExecutionStatus


FORBIDDEN_ACTIONS = {
    "external_api_write",
    "deploy",
    "push",
    "force_push",
    "delete_production",
    "drop_table",
    "rm_rf",
    "shell_destructive",
}

FORBIDDEN_ZONES = [
    ".env",
    ".env.",
    "secrets/",
    "*.key",
    "*.pem",
    "credentials.json",
    ".kratos/",
    "/etc/",
    "/proc/",
    "C:\\Windows\\",
]

ALWAYS_ALLOWED_ZONES = [
    "src/",
    "tests/",
    "docs/",
    "config/",
]

ALWAYS_FORBIDDEN_ACTIONS = [
    "read_env",
    "read_secrets",
    "push_origin",
    "merge_external",
    "deploy_production",
    "delete_repository",
]


class PermissionGate:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self._custom_forbidden: set[str] = set()

    def add_forbidden(self, action: str) -> None:
        self._custom_forbidden.add(action.lower())

    def evaluate(self, request: SkillExecutionRequest) -> SkillExecutionResult:
        result = SkillExecutionResult(
            request_id=request.request_id,
            skill_id=request.skill_id,
        )

        if request.risk_level == SkillExecutionRisk.CRITICAL:
            result.status = ExecutionStatus.BLOCKED
            result.errors.append("CRITICAL: blocked by permission gate")
            return result

        if request.forbidden_paths:
            for path in request.forbidden_paths:
                for forbidden in FORBIDDEN_ZONES:
                    if forbidden.replace("*", "") in path.lower():
                        result.status = ExecutionStatus.BLOCKED
                        result.errors.append(f"Forbidden zone detected: {path}")
                        return result

        intent_lower = request.intent.lower()
        for action in ALWAYS_FORBIDDEN_ACTIONS:
            if action in intent_lower:
                result.status = ExecutionStatus.BLOCKED
                result.errors.append(f"Always forbidden action: {action}")
                return result

        for action in FORBIDDEN_ACTIONS:
            if action in intent_lower:
                result.status = ExecutionStatus.BLOCKED
                result.errors.append(f"Forbidden action: {action}")
                return result

        if request.intent.lower() in self._custom_forbidden:
            result.status = ExecutionStatus.BLOCKED
            result.errors.append(f"Custom forbidden: {request.intent}")
            return result

        if request.risk_level == SkillExecutionRisk.HIGH:
            result.status = ExecutionStatus.NEEDS_APPROVAL
            result.summary = "HIGH risk: requires human approval"
            return result

        if not request.dry_run and request.risk_level == SkillExecutionRisk.MEDIUM:
            result.status = ExecutionStatus.NEEDS_APPROVAL
            result.summary = "MEDIUM non-dry-run: requires approval"
            return result

        result.status = ExecutionStatus.DRY_RUN_OK
        result.summary = f"Permission gate passed for {request.skill_id}"
        return result
