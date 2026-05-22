"""Canonical ABA 4 L0-L5 Risk Taxonomy.

This is the SINGLE canonical risk taxonomy for the OMNIS ecosystem.
All other risk taxonomies must translate to this one.

Translation table: see translation_table.yaml in this directory.
"""

RISK_LEVELS = {
    0: {
        "name": "READ",
        "description": "Read-only operations, no side effects",
        "auto_approve": True,
        "dry_run_allowed": False,
        "human_slot": False,
        "audit": False,
        "examples": ["health check", "status query", "read config", "list resources"],
    },
    1: {
        "name": "LOCAL",
        "description": "Local filesystem writes, no external systems",
        "auto_approve": True,
        "dry_run_allowed": False,
        "human_slot": False,
        "audit": False,
        "examples": ["write file", "create directory", "local git commit"],
    },
    2: {
        "name": "INTERNAL",
        "description": "Internal service calls, no production data",
        "auto_approve": True,
        "dry_run_allowed": True,
        "human_slot": False,
        "audit": False,
        "examples": ["call internal API", "query database", "run test suite"],
    },
    3: {
        "name": "CODE",
        "description": "Code changes with tests, requires review",
        "auto_approve": False,
        "dry_run_allowed": True,
        "human_slot": False,
        "audit": True,
        "examples": ["edit source file", "create new module", "refactor function"],
    },
    4: {
        "name": "PRODUCTION",
        "description": "Production system changes, requires Human Slot",
        "auto_approve": False,
        "dry_run_allowed": False,
        "human_slot": True,
        "audit": True,
        "examples": ["deploy code", "restart service", "modify container", "change config in production"],
    },
    5: {
        "name": "DESTRUCTIVE",
        "description": "Data deletion, credential rotation, infrastructure destruction",
        "auto_approve": False,
        "dry_run_allowed": False,
        "human_slot": True,
        "audit": True,
        "examples": ["delete data", "rotate credentials", "destroy infrastructure", "force push"],
    },
}


def get_level(level: int) -> dict:
    """Get risk level definition by number."""
    if level not in RISK_LEVELS:
        raise ValueError(f"Invalid risk level: {level}. Must be 0-5.")
    return RISK_LEVELS[level]


def requires_human_slot(level: int) -> bool:
    """Check if a risk level requires human approval."""
    return get_level(level)["human_slot"]


def is_auto_approved(level: int) -> bool:
    """Check if a risk level is auto-approved."""
    return get_level(level)["auto_approve"]
