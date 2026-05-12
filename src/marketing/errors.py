"""Marketing module error hierarchy."""

from __future__ import annotations


class MarketingError(Exception):
    """Base error for marketing module."""
    pass


class InvalidObjectiveError(MarketingError):
    """Invalid marketing objective."""
    pass


class InvalidAudienceError(MarketingError):
    """Invalid audience profile."""
    pass


class InvalidPillarError(MarketingError):
    """Invalid content pillar."""
    pass


class InvalidCampaignError(MarketingError):
    """Invalid campaign brief."""
    pass


class ContentPlanError(MarketingError):
    """Content plan generation failure."""
    pass


class ValidationError(MarketingError):
    """Campaign validation failure."""
    pass


class ExportError(MarketingError):
    """Export generation failure."""
    pass
