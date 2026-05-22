"""Approval Bridge — connects capability proposals to the approval center."""
from __future__ import annotations

from typing import Optional

from src.capability_forge_real.errors import (
    ProposalNotFoundError,
    ProposalNotApprovedError,
)
from src.capability_forge_real.models import (
    PROPOSAL_STATUS_APPROVED,
    PROPOSAL_STATUS_REJECTED,
    PROPOSAL_STATUS_NEEDS_APPROVAL,
)
from src.capability_forge_real import store as store_mod
from src.capability_forge_real.store import ProposalStore
from src.approval_center import store as approval_store_mod
from src.approval_center.service import request_approval, approve, reject
from src.approval_center.errors import ApprovalNotFoundError, ApprovalAlreadyResolvedError
from src.approval_center.models import APPROVAL_STATUS_APPROVED, APPROVAL_STATUS_REJECTED


def request_proposal_approval(
    proposal_id: str,
    proposals_log=None,
    approvals_log=None,
) -> str:
    """Create an approval request for a proposal. Returns request_id."""
    p_log = proposals_log if proposals_log is not None else store_mod.DEFAULT_PROPOSALS_LOG
    a_log = approvals_log if approvals_log is not None else approval_store_mod.DEFAULT_APPROVALS_LOG

    store = ProposalStore(p_log)
    proposal = store.get(proposal_id)
    if proposal is None:
        raise ProposalNotFoundError(f"Proposal {proposal_id} not found")

    req = request_approval(
        subject=f"Capability proposal: {proposal.capability_name}",
        description=f"Sector: {proposal.sector} | Type: {proposal.implementation_type} | Output: {proposal.desired_output}",
        capability_id=proposal.proposal_id,
        risk_level=proposal.risk_level,
        approvals_log=a_log,
    )
    proposal.approval_id = req.request_id
    store.update(proposal)
    return req.request_id


def mark_proposal_approved(
    proposal_id: str,
    note: str = "",
    proposals_log=None,
    approvals_log=None,
) -> None:
    """Approve the approval request linked to a proposal and update proposal status."""
    p_log = proposals_log if proposals_log is not None else store_mod.DEFAULT_PROPOSALS_LOG
    a_log = approvals_log if approvals_log is not None else approval_store_mod.DEFAULT_APPROVALS_LOG

    store = ProposalStore(p_log)
    proposal = store.get(proposal_id)
    if proposal is None:
        raise ProposalNotFoundError(f"Proposal {proposal_id} not found")
    if not proposal.approval_id:
        raise ProposalNotApprovedError(f"Proposal {proposal_id} has no linked approval request")

    approve(proposal.approval_id, note=note, approvals_log=a_log)
    proposal.status = PROPOSAL_STATUS_APPROVED
    store.update(proposal)


def mark_proposal_rejected(
    proposal_id: str,
    note: str = "",
    proposals_log=None,
    approvals_log=None,
) -> None:
    """Reject the approval request linked to a proposal and update proposal status."""
    p_log = proposals_log if proposals_log is not None else store_mod.DEFAULT_PROPOSALS_LOG
    a_log = approvals_log if approvals_log is not None else approval_store_mod.DEFAULT_APPROVALS_LOG

    store = ProposalStore(p_log)
    proposal = store.get(proposal_id)
    if proposal is None:
        raise ProposalNotFoundError(f"Proposal {proposal_id} not found")
    if not proposal.approval_id:
        raise ProposalNotApprovedError(f"Proposal {proposal_id} has no linked approval request")

    reject(proposal.approval_id, note=note, approvals_log=a_log)
    proposal.status = PROPOSAL_STATUS_REJECTED
    store.update(proposal)


def get_approval_status(
    proposal_id: str,
    proposals_log=None,
    approvals_log=None,
) -> Optional[str]:
    """Return the current approval status for a proposal's linked request, or None."""
    from src.approval_center.store import ApprovalStore

    p_log = proposals_log if proposals_log is not None else store_mod.DEFAULT_PROPOSALS_LOG
    a_log = approvals_log if approvals_log is not None else approval_store_mod.DEFAULT_APPROVALS_LOG

    proposal = ProposalStore(p_log).get(proposal_id)
    if proposal is None:
        raise ProposalNotFoundError(f"Proposal {proposal_id} not found")
    if not proposal.approval_id:
        return None

    req = ApprovalStore(a_log).get(proposal.approval_id)
    return req.status if req is not None else None
