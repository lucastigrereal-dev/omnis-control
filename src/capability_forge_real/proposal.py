"""Proposal generator — creates CapabilityProposal from a detected gap."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from src.capability_forge_real.errors import GapNotFoundError
from src.capability_forge_real.models import (
    CapabilityProposal,
    IMPL_TYPE_MANUAL_PROCESS,
    IMPL_TYPE_APP_FACTORY_FUTURE,
    IMPL_TYPE_OFFLINE_PACKAGE,
    IMPL_TYPE_EXTERNAL_FUTURE,
    IMPL_TYPE_CLI_WRAPPER,
)
from src.capability_forge_real import store as store_mod
from src.capability_forge_real.store import ProposalStore
from src.capability_gap import store as gap_store_mod
from src.capability_gap.store import GapStore

_SECTOR_IMPL_MAP = {
    "apps": IMPL_TYPE_APP_FACTORY_FUTURE,
    "automation": IMPL_TYPE_CLI_WRAPPER,
    "marketing": IMPL_TYPE_OFFLINE_PACKAGE,
    "operations": IMPL_TYPE_CLI_WRAPPER,
    "sales": IMPL_TYPE_MANUAL_PROCESS,
    "finance": IMPL_TYPE_MANUAL_PROCESS,
    "knowledge": IMPL_TYPE_CLI_WRAPPER,
}


def propose_from_gap(
    gap_id: str,
    gaps_log=None,
    proposals_log=None,
) -> CapabilityProposal:
    """Create and persist a CapabilityProposal from a detected gap.

    Raises GapNotFoundError if gap does not exist.
    """
    gap_path = gaps_log if gaps_log is not None else gap_store_mod.DEFAULT_GAPS_LOG
    gap = GapStore(gap_path).get(gap_id)
    if gap is None:
        raise GapNotFoundError(f"Gap {gap_id} not found")

    impl_type = _SECTOR_IMPL_MAP.get(gap.sector, IMPL_TYPE_MANUAL_PROCESS)
    capability_name = gap.missing_capability

    proposal = CapabilityProposal.from_gap(
        gap_id=gap_id,
        capability_name=capability_name,
        sector=gap.sector,
        desired_output=gap.desired_output,
        risk_level=gap.risk_level,
        implementation_type=impl_type,
    )

    log_path = proposals_log if proposals_log is not None else store_mod.DEFAULT_PROPOSALS_LOG
    ProposalStore(log_path).save(proposal)
    return proposal
