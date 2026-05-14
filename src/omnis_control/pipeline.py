from dataclasses import dataclass, field
from typing import Optional

from src.work_orders.parser import WorkOrderParser
from src.work_orders.validator import WorkOrderValidator
from src.work_orders.models import WorkOrderDecision
from src.work_orders.mapper import WorkOrderMapper
from src.execution_contracts.validators import ContractValidator
from src.execution_contracts.permissions import PermissionChecker
from src.execution_contracts.outcomes import OutcomeGenerator
from src.control_tower.decision_engine import DecisionEngine
from src.control_tower.models import TowerRequest, ActionType, BoundarySystem
from src.skills_bridge.selection import SkillSelector
from src.skills_bridge.dryrun import DryRunEngine
from src.skills_bridge.models import SkillCall, SkillIntent
from src.execution_queue.queue import ExecutionQueue
from src.execution_queue.models import QueueItem, QueueItemStatus
from src.decision_log.events import EventFactory
from src.decision_log.writer import LogWriter
from src.decision_log.models import LogEvent


def _target_system_to_enum(target: str) -> BoundarySystem:
    target_upper = target.upper()
    for member in BoundarySystem:
        if member.value == target_upper:
            return member
    return BoundarySystem.OMNIS


@dataclass
class PipelineResult:
    success: bool = False
    work_order_id: str = ""
    contract_id: str = ""
    decision_id: str = ""
    skill_selection_id: str = ""
    queue_item_id: str = ""
    queue_result_status: str = ""
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    events: list[LogEvent] = field(default_factory=list)
    dry_run_output: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "work_order_id": self.work_order_id,
            "contract_id": self.contract_id,
            "decision_id": self.decision_id,
            "skill_selection_id": self.skill_selection_id,
            "queue_item_id": self.queue_item_id,
            "queue_result_status": self.queue_result_status,
            "errors": self.errors,
            "warnings": self.warnings,
            "dry_run_output": self.dry_run_output,
        }


class OmnisPipeline:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.parser = WorkOrderParser(dry_run=dry_run)
        self.wo_validator = WorkOrderValidator(dry_run=dry_run)
        self.mapper = WorkOrderMapper(dry_run=dry_run)
        self.contract_validator = ContractValidator(dry_run=dry_run)
        self.permission_checker = PermissionChecker(dry_run=dry_run)
        self.decision_engine = DecisionEngine(dry_run=dry_run)
        self.skill_selector = SkillSelector(dry_run=dry_run)
        self.dry_run_engine = DryRunEngine(dry_run=dry_run)
        self.queue = ExecutionQueue(dry_run=dry_run)
        self.writer = LogWriter()

    def execute(self, work_order_content: str, project: str = "omnis") -> PipelineResult:
        result = PipelineResult()

        # Step 1: Parse Work Order
        try:
            work_order = self.parser.parse(work_order_content)
            result.work_order_id = work_order.order_id
            self.writer.write(
                EventFactory.work_order_parsed(
                    order_id=work_order.order_id,
                    summary=f"Parsed work order: {work_order.title}",
                    project=project,
                )
            )
        except Exception as e:
            result.errors.append(f"Parse error: {e}")
            self.writer.write(
                EventFactory.risk_blocked(
                    risk_level="HIGH",
                    reason=f"Parse failed: {e}",
                    summary="Work order parse failure",
                    project=project,
                )
            )
            return result

        # Step 2: Validate Work Order
        wo_decision = self.wo_validator.decide(work_order)
        try:
            self.wo_validator.validate(work_order)
        except Exception as e:
            result.errors.append(f"Work order validation failed: {e}")
            self.writer.write(
                EventFactory.risk_blocked(
                    risk_level="HIGH",
                    reason=str(e),
                    summary="Work order validation blocked",
                    project=project,
                )
            )
            return result

        if wo_decision == WorkOrderDecision.NEEDS_APPROVAL:
            result.errors.append("Work order requires approval before execution")
            self.writer.write(
                EventFactory.approval_required(
                    item_id=work_order.order_id,
                    risk_level=work_order.risk.upper() if work_order.risk else "MEDIUM",
                    summary=f"Work order '{work_order.title}' requires approval",
                    project=project,
                )
            )
            return result

        if wo_decision == WorkOrderDecision.NEEDS_REVIEW:
            result.errors.append("Work order needs manual review")
            self.writer.write(
                EventFactory.approval_required(
                    item_id=work_order.order_id,
                    risk_level="LOW",
                    summary=f"Work order '{work_order.title}' needs review",
                    project=project,
                )
            )
            return result

        # Step 3: Map to Execution Contract
        contract = self.mapper.to_contract(work_order)
        result.contract_id = contract.contract_id

        # Step 4: Validate Contract
        contract_errors = self.contract_validator.validate(contract)
        if contract_errors:
            result.errors.extend(contract_errors)
            self.writer.write(
                EventFactory.contract_validated(
                    contract_id=contract.contract_id,
                    summary="Contract validation failed",
                    project=project,
                )
            )
            return result

        self.writer.write(
            EventFactory.contract_validated(
                contract_id=contract.contract_id,
                summary="Contract validated successfully",
                project=project,
            )
        )

        # Step 5: Check Permissions
        perm_issues = self.permission_checker.check_all(contract, action="execute")
        if perm_issues:
            result.warnings.extend(perm_issues)

        # Step 6: Control Tower Decision
        target_enum = _target_system_to_enum(contract.target_system or "OMNIS")
        tower_request = TowerRequest(
            action="execute",
            target_system=target_enum,
            is_external=target_enum not in (BoundarySystem.OMNIS, BoundarySystem.SKILLS),
            paths_touched=list(contract.allowed_paths) if contract.allowed_paths else [],
        )
        decision = self.decision_engine.evaluate(tower_request)
        result.decision_id = decision.decision_id

        if decision.is_blocked:
            result.errors.append(f"Decision blocked: {decision.rationale}")
            risk_str = decision.risk_level.value if hasattr(decision.risk_level, 'value') else str(decision.risk_level)
            self.writer.write(
                EventFactory.risk_blocked(
                    risk_level=risk_str,
                    reason=decision.rationale,
                    summary="Control Tower blocked execution",
                    project=project,
                    correlation_id=result.decision_id,
                )
            )
            return result

        if decision.requires_human_approval:
            result.warnings.append("Requires human approval")
            risk_str = decision.risk_level.value if hasattr(decision.risk_level, 'value') else str(decision.risk_level)
            self.writer.write(
                EventFactory.approval_required(
                    item_id=result.work_order_id,
                    risk_level=risk_str,
                    summary="Human approval required",
                    project=project,
                    correlation_id=result.decision_id,
                )
            )

        # Step 7: Skill Selection
        skill_call = SkillCall(
            intent=SkillIntent.GENERATE,
            tags=[work_order.type or project],
        )
        skill_selection = self.skill_selector.select(skill_call)
        result.skill_selection_id = skill_selection.selection_id

        # Step 8: Dry Run
        try:
            dry_run_output = self.dry_run_engine.execute(skill_call)
            result.dry_run_output = dry_run_output
            self.writer.write(
                EventFactory.dry_run_completed(
                    request_id=skill_call.call_id,
                    summary=f"Dry run completed for {skill_selection.skill_id}",
                    project=project,
                    evidence=dry_run_output,
                )
            )
        except Exception as e:
            result.errors.append(f"Dry run failed: {e}")
            self.writer.write(
                EventFactory.execution_failed(
                    item_id=skill_call.call_id,
                    error=str(e),
                    summary="Dry run execution failed",
                    project=project,
                )
            )
            return result

        # Step 9: Execution Queue
        risk_str = decision.risk_level.value if hasattr(decision.risk_level, 'value') else str(decision.risk_level)
        queue_item = QueueItem(
            contract_id=contract.contract_id,
            title=work_order.title,
            risk_level=risk_str,
            requires_approval=decision.requires_human_approval,
            dry_run_required=self.dry_run,
        )
        self.queue.enqueue(queue_item)

        if queue_item.status == QueueItemStatus.BLOCKED:
            result.errors.append("Queue item blocked on enqueue")
            self.writer.write(
                EventFactory.risk_blocked(
                    risk_level=queue_item.risk_level,
                    reason="Auto-blocked by queue on enqueue",
                    summary="Queue item blocked",
                    project=project,
                    correlation_id=queue_item.item_id,
                )
            )
            return result

        result.queue_item_id = queue_item.item_id

        if not decision.requires_human_approval:
            self.queue.validate(queue_item)
            if queue_item.status == QueueItemStatus.DRY_RUN:
                self.queue.state.transition(queue_item, QueueItemStatus.READY)
            queue_result = self.queue.run(queue_item)
            result.queue_result_status = queue_result.status.value

            if queue_result.status == QueueItemStatus.DONE:
                result.success = True
                self.writer.write(
                    EventFactory.execution_completed(
                        item_id=queue_item.item_id,
                        tests_run=queue_result.tests_run,
                        tests_passed=queue_result.tests_passed,
                        summary=f"Execution completed: {work_order.title}",
                        project=project,
                    )
                )
            else:
                self.writer.write(
                    EventFactory.execution_failed(
                        item_id=queue_item.item_id,
                        error="; ".join(queue_result.errors) if queue_result.errors else "Unknown error",
                        summary=f"Execution failed: {work_order.title}",
                        project=project,
                    )
                )

        result.events = self.writer.memory
        return result

    def get_event_log(self) -> list[LogEvent]:
        return self.writer.memory
