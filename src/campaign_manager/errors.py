"""P19 Campaign Manager — error hierarchy."""

from __future__ import annotations


class CampaignError(Exception):
    """Base exception for all campaign manager errors."""


class StateTransitionError(CampaignError):
    """Raised when an invalid campaign state transition is attempted."""


class BudgetError(CampaignError):
    """Raised for invalid budget operations (negative, zero, insufficient)."""


class ROIError(CampaignError):
    """Raised when ROI calculation cannot be performed (missing metrics, etc.)."""
