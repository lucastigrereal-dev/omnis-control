"""Output Generator errors."""
from __future__ import annotations


class OutputGeneratorError(Exception):
    """Base error for output generator module."""


class GeneratorNotFoundError(OutputGeneratorError):
    """Generator ID not found in registry."""


class NoGeneratorForTypeError(OutputGeneratorError):
    """No generator (active or planned) found for output type."""
