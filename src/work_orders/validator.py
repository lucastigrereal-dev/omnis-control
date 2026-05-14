from src.work_orders.models import (
    WorkOrder, WorkOrderStatus, WorkOrderDecision,
)
from src.work_orders.errors import InvalidWorkOrderError


class WorkOrderValidator:

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run

    def decide(self, work_order: WorkOrder) -> WorkOrderDecision:
        if not work_order.title or not work_order.type:
            return WorkOrderDecision.INVALID

        if not work_order.title.strip() or not work_order.type.strip():
            return WorkOrderDecision.INVALID

        if work_order.status == WorkOrderStatus.WAITING:
            return WorkOrderDecision.NEEDS_APPROVAL

        if work_order.status == WorkOrderStatus.BLOCKED:
            return WorkOrderDecision.BLOCKED

        if work_order.is_high_risk:
            return WorkOrderDecision.NEEDS_APPROVAL

        has_forbidden = bool(work_order.forbidden_paths)
        paths_conflict = False
        if has_forbidden:
            for allowed in work_order.allowed_paths:
                for forbidden in work_order.forbidden_paths:
                    if allowed.startswith(forbidden):
                        paths_conflict = True
                        break

        if paths_conflict:
            return WorkOrderDecision.BLOCKED

        if work_order.requires_approval:
            return WorkOrderDecision.NEEDS_APPROVAL

        if work_order.status == WorkOrderStatus.READY:
            return WorkOrderDecision.READY

        if work_order.status == WorkOrderStatus.DRAFT:
            return WorkOrderDecision.NEEDS_REVIEW

        return WorkOrderDecision.READY

    def validate(self, work_order: WorkOrder) -> None:
        decision = self.decide(work_order)
        if decision == WorkOrderDecision.INVALID:
            raise InvalidWorkOrderError(
                f"Work order '{work_order.order_id}' is INVALID: "
                f"missing title or type"
            )
        if decision == WorkOrderDecision.BLOCKED:
            raise InvalidWorkOrderError(
                f"Work order '{work_order.order_id}' is BLOCKED"
            )
