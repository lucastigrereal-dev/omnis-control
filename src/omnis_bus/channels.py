"""Channel Taxonomy — standardized Redis channel naming for OMNIS Bus.

Pattern: <domain>:<subdomain>

All publishers and subscribers MUST use these channel constants.
Legacy channels are mapped for backward compatibility.
"""

from enum import Enum


class Channel(str, Enum):
    """Standardized Redis channels for the OMNIS Bus."""

    # ── OMNIS Runtime ──────────────────────────────────────────
    OMNIS_RUNTIME = "omnis:runtime"
    """OMNIS runtime events: heartbeats, kernel bootstrap, shutdown, health."""

    # ── Akasha Memory ──────────────────────────────────────────
    AKASHA_MEMORY = "akasha:memory"
    """Akasha memory events: ingestion, query, index, embedding updates."""

    # ── KRATOS Snapshot ────────────────────────────────────────
    KRATOS_SNAPSHOT = "kratos:snapshot"
    """KRATOS cockpit snapshots: collector runs, operational truth verdicts, drift."""

    # ── Mission Events ─────────────────────────────────────────
    MISSION_EVENTS = "mission:events"
    """Mission lifecycle events: created, started, completed, failed, checkpoint."""

    # ── Finance Cost ───────────────────────────────────────────
    FINANCE_COST = "finance:cost"
    """Cost tracking events: LLM usage, provider billing, budget warnings."""

    # ── CRM Pipeline ───────────────────────────────────────────
    CRM_PIPELINE = "crm:pipeline"
    """CRM pipeline events: lead status changes, qualification, stage transitions."""


# ---------------------------------------------------------------------------
# Channel set for iteration
# ---------------------------------------------------------------------------
CHANNELS: tuple[Channel, ...] = tuple(Channel)


# ---------------------------------------------------------------------------
# Legacy channel mapping (backward compatibility)
# ---------------------------------------------------------------------------
LEGACY_MAP: dict[str, Channel] = {
    "system:heartbeat": Channel.OMNIS_RUNTIME,
    "omnis:events": Channel.OMNIS_RUNTIME,
    "akasha:events": Channel.AKASHA_MEMORY,
    "risk:events": Channel.OMNIS_RUNTIME,  # risk events route through runtime
    "runtime:heartbeat": Channel.OMNIS_RUNTIME,
    "mission:events": Channel.MISSION_EVENTS,
    "memory:events": Channel.AKASHA_MEMORY,
}


def channel_for(legacy_name: str) -> Channel:
    """Map a legacy channel name to its canonical Channel.

    Returns Channel.OMNIS_RUNTIME for unknown legacy channels
    (safe default — runtime receives all uncategorized events).
    """
    return LEGACY_MAP.get(legacy_name, Channel.OMNIS_RUNTIME)
