"""P20 OMNIS Supreme Activation — Error hierarchy."""


class SupremeError(Exception):
    """Base error for all P20 Supreme operations."""


class PlanError(SupremeError):
    """Planning phase failed — unable to decompose request into steps."""


class ExecutionError(SupremeError):
    """Execution phase failed — step(s) could not complete."""


class ApprovalDeniedError(SupremeError):
    """Approval gate denied the plan or delivery."""


class UnknownIntentError(SupremeError):
    """Request intent could not be classified."""


class StepAdapterError(SupremeError):
    """No adapter found for (module_ref, operation) pair."""


class DryRunBlockedError(SupremeError):
    """Dry-run detected a blocker that prevents real execution."""
