"""Automation module errors."""


class AutomationError(Exception):
    pass


class WorkflowValidationError(AutomationError):
    pass


class CycleDetectedError(WorkflowValidationError):
    pass


class UnresolvedDependencyError(WorkflowValidationError):
    pass


class EmptyWorkflowError(WorkflowValidationError):
    pass


class PlanError(AutomationError):
    pass
