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
]
