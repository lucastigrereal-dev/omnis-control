from src.skill_execution.request import SkillExecutionRequest
from src.skill_execution.result import SkillExecutionResult, ExecutionStatus


class DryRunExecutor:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self._history: list[SkillExecutionResult] = []

    def execute(self, request: SkillExecutionRequest) -> SkillExecutionResult:
        if not self.dry_run:
            return SkillExecutionResult(
                request_id=request.request_id,
                skill_id=request.skill_id,
                status=ExecutionStatus.BLOCKED,
                summary="Real execution not supported (dry_run only)",
            )

        result = SkillExecutionResult(
            request_id=request.request_id,
            skill_id=request.skill_id,
            status=ExecutionStatus.DRY_RUN_OK,
            summary=f"Dry-run: {request.skill_id} with intent '{request.intent}'",
            artifacts=[
                {"type": "dry_run_artifact", "skill": request.skill_id, "echo": request.payload}
            ],
            logs=[
                f"DryRunExecutor: skill={request.skill_id}",
                f"DryRunExecutor: intent={request.intent}",
                f"DryRunExecutor: risk={request.risk_level.value}",
                f"DryRunExecutor: dry_run=True (no real execution)",
            ],
            warnings=[],
            next_action=f"Review dry-run output for {request.skill_id}",
        )

        if request.payload:
            result.artifacts[0]["payload_keys"] = list(request.payload.keys())

        self._history.append(result)
        return result

    @property
    def history(self) -> list[SkillExecutionResult]:
        return list(self._history)

    @property
    def execution_count(self) -> int:
        return len(self._history)
