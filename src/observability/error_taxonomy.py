"""Error Taxonomy — structured error classification for OMNIS observability."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ErrorCategory(str, Enum):
    VALIDATION = "validation"
    RUNTIME = "runtime"
    CONFIGURATION = "configuration"
    IO = "io"
    SECURITY = "security"
    TIMEOUT = "timeout"
    DEPENDENCY = "dependency"
    STATE_MACHINE = "state_machine"
    UNKNOWN = "unknown"


class ErrorSeverity(str, Enum):
    FATAL = "fatal"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


CATEGORY_SEVERITY_MAP: dict[ErrorCategory, ErrorSeverity] = {
    ErrorCategory.VALIDATION: ErrorSeverity.ERROR,
    ErrorCategory.RUNTIME: ErrorSeverity.ERROR,
    ErrorCategory.CONFIGURATION: ErrorSeverity.FATAL,
    ErrorCategory.IO: ErrorSeverity.ERROR,
    ErrorCategory.SECURITY: ErrorSeverity.FATAL,
    ErrorCategory.TIMEOUT: ErrorSeverity.WARNING,
    ErrorCategory.DEPENDENCY: ErrorSeverity.ERROR,
    ErrorCategory.STATE_MACHINE: ErrorSeverity.FATAL,
    ErrorCategory.UNKNOWN: ErrorSeverity.ERROR,
}


_CLASSIFICATION_RULES: list[tuple[ErrorCategory, list[str]]] = [
    (ErrorCategory.STATE_MACHINE, ["state", "transition", "invalid status", "illegal transition"]),
    (ErrorCategory.TIMEOUT, ["timeout", "timed out", "deadline exceeded", "too slow"]),
    (ErrorCategory.CONFIGURATION, ["configuration", "config", "env var", "missing key", "not configured"]),
    (ErrorCategory.SECURITY, ["unauthorized", "forbidden", "permission denied", "access denied", "token"]),
    (ErrorCategory.IO, ["file not found", "no such file", "permission error", "disk full", "read error", "write error"]),
    (ErrorCategory.DEPENDENCY, ["dependency", "import error", "module not found", "package", "version conflict"]),
    (ErrorCategory.VALIDATION, ["validation", "invalid", "bad request", "malformed", "schema", "type error"]),
    (ErrorCategory.RUNTIME, ["runtime", "exception", "crash", "unexpected", "nil pointer", "null reference"]),
]


@dataclass
class ClassifiedError:
    error_id: str = ""
    category: ErrorCategory = ErrorCategory.UNKNOWN
    severity: ErrorSeverity = ErrorSeverity.ERROR
    message: str = ""
    original_exception: str = ""
    context: dict[str, Any] = field(default_factory=dict)


class ErrorClassifier:
    """Classifies errors into categories with severity levels."""

    @staticmethod
    def classify(
        error_message: str,
        exception_type: str = "",
        context: dict[str, Any] | None = None,
    ) -> ClassifiedError:
        lower = error_message.lower()
        category = ErrorCategory.UNKNOWN

        for cat, patterns in _CLASSIFICATION_RULES:
            if any(p in lower for p in patterns):
                category = cat
                break

        # Also check exception type if message wasn't decisive
        if category == ErrorCategory.UNKNOWN and exception_type:
            type_lower = exception_type.lower()
            for cat, patterns in _CLASSIFICATION_RULES:
                if any(p in type_lower for p in patterns):
                    category = cat
                    break

        severity = CATEGORY_SEVERITY_MAP.get(category, ErrorSeverity.ERROR)

        return ClassifiedError(
            category=category,
            severity=severity,
            message=error_message,
            original_exception=exception_type,
            context=context or {},
        )

    RETRYABLE_CATEGORIES: frozenset[ErrorCategory] = frozenset({
        ErrorCategory.TIMEOUT,
        ErrorCategory.IO,
        ErrorCategory.DEPENDENCY,
    })

    FATAL_CATEGORIES: frozenset[ErrorCategory] = frozenset({
        ErrorCategory.CONFIGURATION,
        ErrorCategory.SECURITY,
        ErrorCategory.STATE_MACHINE,
    })

    @staticmethod
    def is_retryable(category: ErrorCategory) -> bool:
        return category in ErrorClassifier.RETRYABLE_CATEGORIES

    @staticmethod
    def is_fatal(category: ErrorCategory) -> bool:
        return category in ErrorClassifier.FATAL_CATEGORIES
