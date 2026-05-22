"""Unified action classifier — merges all 7+ classifiers into one.

Sources absorbed:
  - KRATOS governance_runtime.py DANGER_PATTERNS / SAFE_PATTERNS / HUMAN_SLOT_PATTERNS
  - guardrails.yaml blocked_patterns
  - OMNIS Control Tower RiskClassifier
  - OMNIS Governance RiskClassifier
"""
import re
from typing import Optional

# Human Slot patterns (L4-L5) — merged from KRATOS + guardrails + OMNIS
HUMAN_SLOT_PATTERNS: list[str] = [
    r"(?i)delete.*(database|volume|container|credential|secret|key)",
    r"(?i)rm\s+-rf",
    r"(?i)git\s+push\s+--force",
    r"(?i)rotate.*(credential|secret|key|token)",
    r"(?i)destroy.*(infra|service|cluster|volume)",
    r"(?i)drop\s+(table|database|collection)",
    r"(?i)docker\s+(rm|prune|system\s+prune)",
    r"(?i)(terraform|pulumi)\s+(destroy|apply)",
    r"(?i)force\s+push",
    r"(?i)(revoke|invalidate).*(token|key|credential)",
    r"(?i)production.*(write|delete|modify|update)",
    r"(?i)(drop|truncate|purge).*(cache|queue|database)",
]

# Danger patterns (L3) — merged from KRATOS + OMNIS
DANGER_PATTERNS: list[str] = [
    r"(?i)(write|edit|create|modify|refactor|implement).*\.(py|ts|js|go|rs|java)$",
    r"(?i)git\s+commit",
    r"(?i)pip\s+install",
    r"(?i)npm\s+install",
    r"(?i)yarn\s+add",
    r"(?i)cargo\s+(build|add)",
    r"(?i)docker\s+(build|compose)",
    r"(?i)(create|new)\s+(file|module|directory|project)",
    r"(?i)chmod\s+\+x",
    r"(?i)(add|install|setup).*(package|dependency|library|module)",
]

# Safe patterns (L0-L1) — merged from KRATOS
SAFE_PATTERNS: list[str] = [
    r"(?i)^(read|list|show|get|check|ping|status|health|verify|validate)",
    r"(?i)^(ls|dir|find|grep|rg|which|where|cat|head|tail|less|more)",
    r"(?i)git\s+(status|diff|log|branch|fetch|remote)",
    r"(?i)^(help|man|info|about|version)",
    r"(?i)^(echo|print|display|format)",
]


def classify_risk(action: str) -> str:
    """Classify an action as SAFE, DANGER, or REQUIRES_HUMAN_SLOT.

    Returns one of: 'SAFE', 'DANGER', 'REQUIRES_HUMAN_SLOT'
    """
    action_stripped = action.strip()

    for pattern in HUMAN_SLOT_PATTERNS:
        if re.search(pattern, action_stripped):
            return "REQUIRES_HUMAN_SLOT"

    for pattern in DANGER_PATTERNS:
        if re.search(pattern, action_stripped):
            return "DANGER"

    for pattern in SAFE_PATTERNS:
        if re.search(pattern, action_stripped):
            return "SAFE"

    return "DANGER"  # Unknown actions default to DANGER
