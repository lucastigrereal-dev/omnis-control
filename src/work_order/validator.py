"""Work Order Validator — validates fields, status transitions, contract completeness."""
from __future__ import annotations

from dataclasses import dataclass, field

from src.work_order.errors import (
    WorkOrderContractError,
    WorkOrderStatusError,
    WorkOrderValidationError,
)
from src.work_order.models import (
    VALID_STATUS_TRANSITIONS,
    OutputContract,
    OutputEntry,
    OutputType,
    WorkOrder,
    WorkOrderStatus,
)


@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_error(self, msg: str):
        self.errors.append(msg)
        self.is_valid = False

    def add_warning(self, msg: str):
        self.warnings.append(msg)


def validate_work_order(wo: WorkOrder) -> ValidationResult:
    """Validate a work order has required fields, valid status, and consistent contracts."""
    result = ValidationResult(is_valid=True)

    _validate_required_fields(wo, result)
    _validate_status(wo, result)
    _validate_contracts(wo, result)
    _validate_outputs(wo, result)

    return result


def _validate_required_fields(wo: WorkOrder, result: ValidationResult):
    if not wo.work_order_id:
        result.add_error("work_order_id is required")
    if not wo.graph_step_id:
        result.add_error("graph_step_id is required")
    if not wo.graph_run_id:
        result.add_error("graph_run_id is required")
    if not wo.role:
        result.add_error("role is required")
    if not wo.work_order_id.startswith("wo_"):
        result.add_error("work_order_id must start with 'wo_'")


def _validate_status(wo: WorkOrder, result: ValidationResult):
    try:
        status = WorkOrderStatus(wo.status.value if isinstance(wo.status, WorkOrderStatus) else wo.status)
    except ValueError:
        result.add_error(f"Invalid status: {wo.status}")
        return

    if status not in VALID_STATUS_TRANSITIONS:
        result.add_error(f"Unknown status: {status.value}")


def _validate_contracts(wo: WorkOrder, result: ValidationResult):
    if not wo.contracts:
        result.add_warning(f"Work order {wo.work_order_id} has no output contracts")

    contract_ids: set[str] = set()
    for c in wo.contracts:
        if not c.contract_id:
            result.add_error("Contract missing contract_id")
            continue
        if c.contract_id in contract_ids:
            result.add_error(f"Duplicate contract_id: {c.contract_id}")
        contract_ids.add(c.contract_id)
        if not c.description:
            result.add_warning(f"Contract {c.contract_id} has no description")
        if c.min_count < 0:
            result.add_error(f"Contract {c.contract_id}: min_count cannot be negative")
        if c.max_count < c.min_count:
            result.add_error(f"Contract {c.contract_id}: max_count ({c.max_count}) < min_count ({c.min_count})")


def _validate_outputs(wo: WorkOrder, result: ValidationResult):
    if wo.status in (WorkOrderStatus.DRAFT, WorkOrderStatus.READY, WorkOrderStatus.BLOCKED):
        if wo.outputs:
            result.add_warning(f"Work order {wo.work_order_id} has outputs but status is {wo.status.value}")

    output_ids: set[str] = set()
    for o in wo.outputs:
        if not o.output_id:
            result.add_error("Output missing output_id")
            continue
        if o.output_id in output_ids:
            result.add_error(f"Duplicate output_id: {o.output_id}")
        output_ids.add(o.output_id)

        if o.output_type not in OutputType:
            result.add_error(f"Invalid output_type for {o.output_id}: {o.output_type}")

    contract_ids = {c.contract_id for c in wo.contracts}
    for o in wo.outputs:
        if o.contract_id and o.contract_id not in contract_ids:
            result.add_error(
                f"Output {o.output_id} references unknown contract: {o.contract_id}"
            )
