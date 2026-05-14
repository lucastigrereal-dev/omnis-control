from src.work_orders.models import WorkOrder
from src.execution_contracts.models import ExecutionContract


class WorkOrderMapper:

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run

    def to_contract(self, work_order: WorkOrder) -> ExecutionContract:
        return ExecutionContract(
            title=work_order.title or work_order.order_id,
            project=work_order.project or "omnis",
            requested_by=work_order.aba or "aba-0",
            target_system=work_order.type or "omnis",
            allowed_paths=work_order.allowed_paths,
            forbidden_paths=work_order.forbidden_paths,
            allowed_actions=["read", "test", "build", "dry_run"],
            forbidden_actions=["delete", "push", "merge", "deploy"],
            requires_approval=work_order.requires_approval,
            dry_run_required=work_order.dry_run,
            expected_outputs=[f"Report for: {work_order.title}"],
            acceptance_criteria=[
                "All tests pass",
                "No forbidden paths touched",
                "Report generated",
            ],
            rollback_hint="git restore" if not work_order.is_high_risk
            else "Manual rollback required",
            report_path=f"docs/work_orders/{work_order.order_id}_report.md",
        )
