"""Design Art module error hierarchy."""

from __future__ import annotations


class DesignArtError(Exception):
    """Base error for design_art module."""
    pass


class InvalidProfileError(DesignArtError):
    """Invalid brand visual profile."""
    pass


class InvalidDirectionError(DesignArtError):
    """Invalid visual direction."""
    pass


class InvalidBriefError(DesignArtError):
    """Invalid design brief."""
    pass


class InvalidAssetSpecError(DesignArtError):
    """Invalid asset specification."""
    pass


class InvalidCarouselLayoutError(DesignArtError):
    """Invalid carousel layout specification."""
    pass


class InvalidReviewError(DesignArtError):
    """Invalid creative review."""
    pass


class ValidationError(DesignArtError):
    """Visual direction / design brief validation failure."""
    pass


class ExportError(DesignArtError):
    """Export generation failure."""
    pass
