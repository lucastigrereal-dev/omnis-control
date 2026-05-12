"""Errors for App Factory."""
from __future__ import annotations


class AppFactoryError(Exception):
    """Base error for all App Factory operations."""
    pass


class InvalidAppIdeaError(AppFactoryError):
    """AppIdea failed validation."""
    pass


class PlannerError(AppFactoryError):
    """Planner pipeline failed."""
    pass


class PRDGenerationError(AppFactoryError):
    """PRD generation failed."""
    pass


class StructureGenerationError(AppFactoryError):
    """Project structure generation failed."""
    pass
