"""Centralized dry_run resolution for OMNIS.

All entry points should use resolve_dry_run() instead of hardcoding
dry_run=True. Controlled via OMNIS_DRY_RUN environment variable:

    OMNIS_DRY_RUN=false  → real execution (L0-L2 safe modules)
    OMNIS_DRY_RUN=true   → simulation (default, safe)
    (unset)              → simulation (default, safe)

Individual modules can still override explicitly via constructor kwarg.
"""

import os


def resolve_dry_run(explicit: bool | None = None) -> bool:
    """Resolve dry_run with env var override.

    Priority:
    1. Explicit kwarg (if not None)
    2. OMNIS_DRY_RUN env var
    3. Default True (safe)
    """
    if explicit is not None:
        return explicit
    val = os.environ.get("OMNIS_DRY_RUN", "true").lower()
    return val not in ("false", "0", "no", "off")


def is_real_mode() -> bool:
    """True when OMNIS_DRY_RUN is explicitly set to false."""
    return not resolve_dry_run()
