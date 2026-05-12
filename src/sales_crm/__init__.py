"""P10 Sales/CRM Skeleton — deterministic sales & CRM package.

Scope:
- Lead and Deal modeling (dataclasses + enums)
- Pipeline stage tracking
- Sales activity logging (dry-run only)
- Objection recording and resolution
- Proposal management
- Follow-up task planning
- Pipeline summary and validation

Constraints:
- Zero LLM, zero network, zero Docker, zero database
- No real WhatsApp, email, or external contact
- No real CRM integration
- All operations are dry-run/modeling
- approval_required gate for future external contact
"""

from src.sales_crm.errors import (
    ExternalContactBlockedError,
    InvalidActivityError,
    InvalidDealError,
    InvalidFollowUpError,
    InvalidLeadError,
    InvalidObjectionError,
    InvalidPipelineError,
    InvalidProposalError,
    PipelineStageError,
    RiskFlagError,
    SalesCRMError,
)
from src.sales_crm.models import (
    VALID_PACKAGES,
    ActivityType,
    Deal,
    DealPriority,
    FollowUpStatus,
    FollowUpTask,
    Lead,
    LeadSource,
    LeadStatus,
    ObjectionCategory,
    ObjectionRecord,
    PipelineStage,
    ProposalRecord,
    ProposalStatus,
    SalesActivity,
    SalesPipeline,
)
from src.sales_crm.service import (
    PipelineSummary,
    SalesCRMPlanner,
    ScoreResult,
    ValidationResult,
)

__all__ = [
    # Models
    "Lead",
    "Deal",
    "SalesActivity",
    "ObjectionRecord",
    "ProposalRecord",
    "FollowUpTask",
    "SalesPipeline",
    # Enums
    "PipelineStage",
    "LeadSource",
    "LeadStatus",
    "ActivityType",
    "ObjectionCategory",
    "DealPriority",
    "FollowUpStatus",
    "ProposalStatus",
    # Constants
    "VALID_PACKAGES",
    # Service
    "SalesCRMPlanner",
    "PipelineSummary",
    "ScoreResult",
    "ValidationResult",
    # Errors
    "SalesCRMError",
    "InvalidLeadError",
    "InvalidDealError",
    "InvalidPipelineError",
    "PipelineStageError",
    "InvalidActivityError",
    "InvalidObjectionError",
    "InvalidProposalError",
    "InvalidFollowUpError",
    "ExternalContactBlockedError",
    "RiskFlagError",
]
