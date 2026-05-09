"""Errors for Work Order System."""


class WorkOrderError(Exception):
    """Base error for work order operations."""


class WorkOrderValidationError(WorkOrderError):
    """Validation failed for a work order."""


class WorkOrderBuildError(WorkOrderError):
    """Building a work order failed (missing inputs, invalid graph, etc.)."""


class WorkOrderContractError(WorkOrderError):
    """Output contract not satisfied or invalid."""


class WorkOrderStatusError(WorkOrderError):
    """Invalid status transition."""
