"""Registrar — persists approved capability proposals into capabilities.yaml."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import yaml

from src.capability_forge_real.errors import (
    ProposalNotFoundError,
    ProposalNotApprovedError,
    DuplicateCapabilityError,
)
from src.capability_forge_real.models import (
    PROPOSAL_STATUS_APPROVED,
    PROPOSAL_STATUS_REGISTERED,
)
from src.capability_forge_lite import store as store_mod
from src.capability_forge_real.store import ProposalStore
from src.skill_matcher.loader import DEFAULT_CONFIG_PATH

BASE = Path(__file__).resolve().parent.parent.parent
_DEFAULT_CAPS_PATH = DEFAULT_CONFIG_PATH


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9_]", "_", name.lower()).strip("_")


def register_capability(
    proposal_id: str,
    proposals_log=None,
    caps_path: Optional[Path] = None,
) -> str:
    """Register an approved proposal as a planned capability in capabilities.yaml.

    Returns the capability_id that was written.
    Raises ProposalNotFoundError, ProposalNotApprovedError, DuplicateCapabilityError.
    """
    p_log = proposals_log if proposals_log is not None else store_mod.DEFAULT_PROPOSALS_LOG
    c_path = Path(caps_path) if caps_path is not None else _DEFAULT_CAPS_PATH

    store = ProposalStore(p_log)
    proposal = store.get(proposal_id)
    if proposal is None:
        raise ProposalNotFoundError(f"Proposal {proposal_id} not found")
    if proposal.status != PROPOSAL_STATUS_APPROVED:
        raise ProposalNotApprovedError(
            f"Proposal {proposal_id} is '{proposal.status}', must be 'approved'"
        )

    raw = yaml.safe_load(c_path.read_text(encoding="utf-8")) or {}
    caps_data: dict = raw.get("capabilities", {})

    cap_id = _slug(proposal.capability_name)
    if cap_id in caps_data:
        raise DuplicateCapabilityError(f"Capability '{cap_id}' already exists in capabilities.yaml")

    caps_data[cap_id] = {
        "sector": proposal.sector,
        "command": f"jarvis forge-lite register {proposal.proposal_id}",
        "output": proposal.desired_output,
        "risk_level": proposal.risk_level,
        "status": "planned",
        "implementation_type": proposal.implementation_type,
        "proposal_id": proposal.proposal_id,
        "keywords": [proposal.capability_name.replace("_", " ")],
    }
    raw["capabilities"] = caps_data
    c_path.write_text(yaml.dump(raw, allow_unicode=True, sort_keys=False), encoding="utf-8")

    proposal.status = PROPOSAL_STATUS_REGISTERED
    store.update(proposal)
    return cap_id
