"""P10 Sales/CRM — error hierarchy."""


class SalesCRMError(Exception):
    """Base error for the sales_crm package."""
    pass


class InvalidLeadError(SalesCRMError):
    """Lead data fails validation."""
    pass


class InvalidDealError(SalesCRMError):
    """Deal data fails validation."""
    pass


class InvalidPipelineError(SalesCRMError):
    """Pipeline structure or integrity issue."""
    pass


class PipelineStageError(SalesCRMError):
    """Invalid stage transition."""
    pass


class InvalidActivityError(SalesCRMError):
    """Sales activity fails validation."""
    pass


class InvalidObjectionError(SalesCRMError):
    """Objection record fails validation."""
    pass


class InvalidProposalError(SalesCRMError):
    """Proposal record fails validation."""
    pass


class InvalidFollowUpError(SalesCRMError):
    """Follow-up task fails validation."""
    pass


class ExternalContactBlockedError(SalesCRMError):
    """Attempted external contact without approval."""
    pass


class RiskFlagError(SalesCRMError):
    """Risk flag raised — manual review required."""
    pass
