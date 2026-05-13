"""P19 Campaign Manager — campaign orchestration engine.

Coordinates marketing briefs (P5), publishing (P8), and analytics (P13)
into structured, trackable campaigns with budget and ROI tracking.
"""

from src.campaign_manager.errors import BudgetError, CampaignError, ROIError, StateTransitionError
from src.campaign_manager.models import (
    ROICalculation,
    BudgetTracker,
    Campaign,
    CampaignStatus,
    _new_id,
    _now_iso,
)
from src.campaign_manager.service import CampaignOrchestrator

__all__ = [
    # Models
    "Campaign",
    "BudgetTracker",
    "ROICalculation",
    "CampaignStatus",
    # Service
    "CampaignOrchestrator",
    # Errors
    "CampaignError",
    "StateTransitionError",
    "BudgetError",
    "ROIError",
    # Helpers
    "_now_iso",
    "_new_id",
]
