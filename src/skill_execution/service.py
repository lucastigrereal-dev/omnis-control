from src.skill_execution.request import SkillExecutionRequest
from src.skill_execution.result import SkillExecutionResult, ExecutionStatus
from src.skill_execution.boundaries import BoundaryChecker
from src.skill_execution.permission_gate import PermissionGate
from src.skill_execution.dryrun_executor import DryRunExecutor
from src.skill_execution.events import SkillEventBus, SkillExecutionEvent, SkillEventType
from src.skill_execution.artifacts import ArtifactRegistry, SkillArtifact


class SkillExecutionService:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.boundary_checker = BoundaryChecker(dry_run=dry_run)
        self.permission_gate = PermissionGate(dry_run=dry_run)
        self.executor = DryRunExecutor(dry_run=dry_run)
        self.events = SkillEventBus()
        self.artifacts = ArtifactRegistry()

    def execute(self, request: SkillExecutionRequest) -> SkillExecutionResult:
        self.events.emit(SkillExecutionEvent(
            event_type=SkillEventType.REQUEST_RECEIVED,
            request_id=request.request_id,
            skill_id=request.skill_id,
        ))

        perm_result = self.permission_gate.evaluate(request)
        perm_event_type = (
            SkillEventType.EXECUTION_BLOCKED if perm_result.status == ExecutionStatus.BLOCKED
            else SkillEventType.APPROVAL_REQUIRED if perm_result.status == ExecutionStatus.NEEDS_APPROVAL
            else SkillEventType.PERMISSION_CHECKED
        )
        self.events.emit(SkillExecutionEvent(
            event_type=perm_event_type,
            request_id=request.request_id,
            skill_id=request.skill_id,
            detail={"status": perm_result.status.value, "summary": perm_result.summary},
        ))

        if perm_result.status in (ExecutionStatus.BLOCKED, ExecutionStatus.NEEDS_APPROVAL):
            return perm_result

        result = self.executor.execute(request)

        self.events.emit(SkillExecutionEvent(
            event_type=SkillEventType.EXECUTION_COMPLETED,
            request_id=request.request_id,
            skill_id=request.skill_id,
            detail={"status": result.status.value},
        ))

        for artifact_dict in result.artifacts:
            artifact = SkillArtifact(
                execution_result_id=result.result_id,
                artifact_type=artifact_dict.get("type", "generic"),
                data=artifact_dict,
            )
            self.artifacts.register(artifact)

        return result
