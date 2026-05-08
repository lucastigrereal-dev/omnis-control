"""OAuth Meta Readiness Gate — P1.2a.

Validates 12 preconditions for Meta OAuth WITHOUT reading .env,
calling Meta APIs, or executing real OAuth.

Public API:
    OAuthReadinessChecker  — run all 12 checks
    OAuthReadinessReport    — structured output
    get_checker()           — convenience accessor
"""

from src.oauth_readiness.checker import OAuthReadinessChecker
from src.oauth_readiness.models import (
    OAuthReadinessStatus,
    OAuthReadinessCheck,
    OAuthReadinessReport,
)

_checker: OAuthReadinessChecker | None = None


def get_checker() -> OAuthReadinessChecker:
    global _checker
    if _checker is None:
        _checker = OAuthReadinessChecker()
    return _checker
