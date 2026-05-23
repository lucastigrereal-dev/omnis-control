"""Single canonical risk classifier for the OMNIS ecosystem.

Maps all action patterns to ABA 4 L0-L5 risk levels.
Replaces 7+ incompatible risk taxonomies (KRATOS SAFE/DANGER/HUMAN_SLOT,
OMNIS low/medium/high/critical, Control Tower LOW/MEDIUM/HIGH/CRITICAL, etc.)
"""
import re
from typing import Optional

from ..policies.risk_taxonomy import RISK_LEVELS


# Action patterns → risk level mapping
# Ordered from most specific to least specific
_RISK_PATTERNS: list[tuple[str, int]] = [
    # L5 — DESTRUCTIVE
    ("delete.*(database|volume|container|credential|secret)", 5),
    ("rm\\s+-rf", 5),
    ("git\\s+push\\s+--force", 5),
    ("rotate.*(credential|secret|key)", 5),
    ("destroy.*(infra|service|cluster)", 5),
    ("drop\\s+table", 5),
    ("docker\\s+(rm|prune|system\\s+prune)", 5),

    # L4 — PRODUCTION
    ("(deploy|release|publish)", 4),
    ("(restart|stop|kill).*(service|container|process)", 4),
    ("docker\\s+(compose|stack)\\s+(up|down|restart)", 4),
    ("git\\s+(push|merge).*(main|master|production)", 4),
    ("modify.*(config|env|secret).*(production|prod)", 4),
    ("terraform\\s+(apply|destroy)", 4),

    # L3 — CODE
    ("(write|edit|create|modify|refactor|implement).*\\.(py|ts|js|go|rs|java)$", 3),
    ("git\\s+commit", 3),
    ("pip\\s+install", 3),
    ("npm\\s+install", 3),
    ("yarn\\s+add", 3),
    ("cargo\\s+(build|add)", 3),

    # L2 — INTERNAL
    ("(query|select|insert|update).*(database|db|sql)", 2),
    ("(call|invoke|request).*(api|service|endpoint)", 2),
    ("redis.*(get|set|publish|subscribe)", 2),
    ("curl.*(localhost|127\\.0\\.0\\.1|internal)", 2),
    ("docker\\s+(ps|logs|inspect|stats|exec)", 2),
    ("(run|execute)\\s+(test|pytest|suite)", 2),

    # L1 — LOCAL
    ("(write|create|save|touch|mkdir|cp|mv|echo).*\\.(md|txt|yaml|json|toml|log)$", 1),
    ("git\\s+(status|diff|log|branch|checkout|stash)", 1),
    ("cat|head|tail|less|more", 1),

    # L0 — READ
    ("(read|list|show|get|check|ping|status|health|verify|validate)", 0),
    ("(ls|dir|find|grep|rg|which|where)", 0),
    ("git\\s+(remote|fetch|pull\\s+--ff-only)", 0),
]

# Translation from other taxonomies to L0-L5
TAXONOMY_TRANSLATION = {
    # KRATOS → ABA 4
    "SAFE": 1,
    "DANGER": 3,
    "REQUIRES_HUMAN_SLOT": 4,

    # OMNIS Governance / Control Tower / Approval Runtime / Missions
    "low": 0,
    "medium": 2,
    "high": 3,
    "critical": 4,
    "LOW": 0,
    "MEDIUM": 2,
    "HIGH": 3,
    "CRITICAL": 4,

    # JARVIS Guardrails
    "jarvis_low": 0,
    "jarvis_medium": 2,
    "jarvis_high": 3,

    # Remote Control
    "SAFE_REMOTE": 0,
    "CAUTION": 2,
    "DANGER_REMOTE": 3,
}


def classify_action(action: str) -> dict:
    """Classify an action string into an ABA 4 L0-L5 risk level.

    Args:
        action: The action description to classify

    Returns:
        Dict with 'level', 'name', 'auto_approve', 'human_slot', 'audit', 'matched_pattern'
    """
    level = _match_patterns(action)
    info = RISK_LEVELS[level].copy()
    info["level"] = level
    info["action"] = action
    return info


def translate_from(taxonomy_name: str, value: str) -> int:
    """Translate a risk level from another taxonomy to ABA 4 L0-L5.

    Args:
        taxonomy_name: Name of the taxonomy (kratos, omnis, jarvis, remote_control)
        value: The risk value to translate

    Returns:
        ABA 4 level (0-5)
    """
    key = f"{taxonomy_name}_{value}" if taxonomy_name != "kratos" else value
    translated = TAXONOMY_TRANSLATION.get(key)
    if translated is not None:
        return translated

    # Fallback: try value alone
    return TAXONOMY_TRANSLATION.get(value, 2)  # Default to L2 (INTERNAL)


def _match_patterns(action: str) -> int:
    """Match action string against risk patterns."""
    action_lower = action.lower().strip()
    for pattern, level in _RISK_PATTERNS:
        if re.search(pattern, action_lower):
            return level
    return 2  # Default: L2 (INTERNAL) — safe default
