"""P9 Work Order System — local, deterministic, no-LLM, no-network."""

from src.work_order.models import (
    OutputContract,
    OutputEntry,
    OutputType,
    WorkOrder,
    WorkOrderStatus,
    VALID_STATUS_TRANSITIONS,
    make_output_id,
    make_work_order_id,
)
from src.work_order.builder import (
    build_work_orders_from_graph,
    build_work_orders_from_step_run,
)
from src.work_order.validator import ValidationResult, validate_work_order
from src.work_order.output_contract import (
    ContentRule,
    OutputContractSpec,
)
from src.work_order.contract_validator import (
    ContractValidationResult,
    all_contracts_satisfied,
    get_contract_specs_for_role,
    get_missing_contracts,
    validate_contracts_for_work_order,
)
from src.work_order.output_registry import OutputRegistry, OutputRegistryEntry
from src.work_order.output_collector import (
    DEFAULT_EXPORTS_ROOT,
    collect_output,
    collect_outputs_batch,
    list_collected_outputs,
    reject_output,
    validate_output,
)
from src.work_order.approval_bridge import (
    GATE_APPROVED,
    GATE_BLOCKED,
    GATE_NOT_REQUIRED,
    GATE_REJECTED,
    approve_work_order,
    check_work_order_approval_gate,
    reject_work_order,
    request_work_order_approval,
)

__all__ = [
    "WorkOrderStatus",
    "OutputType",
    "OutputContract",
    "OutputEntry",
    "WorkOrder",
    "VALID_STATUS_TRANSITIONS",
    "make_work_order_id",
    "make_output_id",
    "build_work_orders_from_graph",
    "build_work_orders_from_step_run",
    "validate_work_order",
    "ValidationResult",
    "ContentRule",
    "OutputContractSpec",
    "ContractValidationResult",
    "validate_contracts_for_work_order",
    "all_contracts_satisfied",
    "get_missing_contracts",
    "get_contract_specs_for_role",
    "OutputRegistry",
    "OutputRegistryEntry",
    "collect_output",
    "collect_outputs_batch",
    "validate_output",
    "reject_output",
    "list_collected_outputs",
    "DEFAULT_EXPORTS_ROOT",
    "check_work_order_approval_gate",
    "request_work_order_approval",
    "approve_work_order",
    "reject_work_order",
    "GATE_APPROVED",
    "GATE_BLOCKED",
    "GATE_NOT_REQUIRED",
    "GATE_REJECTED",
]
