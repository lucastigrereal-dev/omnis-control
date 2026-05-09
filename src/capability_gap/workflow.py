"""Gap-to-Approval Workflow — bridge between detected gaps and approval queue."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from src.capability_gap.models import (
    CapabilityGap,
    GAP_STATUS_OPEN,
)
from src.capability_gap import store as gap_store_mod
from src.capability_gap.store import GapStore
from src.capability_gap.errors import CapabilityGapError
from src.approval_center import store as approval_store_mod
from src.approval_center.models import APPROVAL_STATUS_APPROVED, APPROVAL_STATUS_REJECTED

GAP_STATUS_PLANNED = "planned"
GAP_STATUS_DISMISSED = "dismissed"


def request_approval_for_gap(
    gap_id: str,
    gaps_log=None,
    approvals_log=None,
) -> str:
    """Create an approval request for a detected gap.

    Returns the approval request_id.
    Raises CapabilityGapError if gap not found.
    """
    from src.approval_center.service import request_approval

    gap_path = gaps_log if gaps_log is not None else gap_store_mod.DEFAULT_GAPS_LOG
    gap = GapStore(gap_path).get(gap_id)
    if gap is None:
        raise CapabilityGapError(f"Gap {gap_id} not found")

    approval_path = approvals_log if approvals_log is not None else approval_store_mod.DEFAULT_APPROVALS_LOG
    req = request_approval(
        subject=f"New capability for gap: {gap.missing_capability}",
        description=f"gap_id={gap.gap_id} | sector={gap.sector} | request={gap.request[:80]}",
        capability_id=gap.missing_capability,
        risk_level=gap.risk_level,
        approvals_log=approval_path,
    )
    return req.request_id


def mark_gap_planned(
    gap_id: str,
    approval_id: str,
    gaps_log=None,
    approvals_log=None,
) -> CapabilityGap:
    """Mark a gap as planned after its approval is approved.

    Raises CapabilityGapError if gap not found or approval not approved.
    """
    gap_path = gaps_log if gaps_log is not None else gap_store_mod.DEFAULT_GAPS_LOG
    approval_path = approvals_log if approvals_log is not None else approval_store_mod.DEFAULT_APPROVALS_LOG

    gap_store = GapStore(gap_path)
    gap = gap_store.get(gap_id)
    if gap is None:
        raise CapabilityGapError(f"Gap {gap_id} not found")

    from src.approval_center.store import ApprovalStore
    req = ApprovalStore(approval_path).get(approval_id)
    if req is None:
        raise CapabilityGapError(f"Approval {approval_id} not found")
    if req.status != APPROVAL_STATUS_APPROVED:
        raise CapabilityGapError(
            f"Cannot mark gap as planned: approval {approval_id} is '{req.status}', not 'approved'"
        )

    gap.status = GAP_STATUS_PLANNED
    gap_store.save(gap)
    return gap


def mark_gap_dismissed(
    gap_id: str,
    approval_id: str,
    gaps_log=None,
    approvals_log=None,
) -> CapabilityGap:
    """Mark a gap as dismissed after its approval is rejected.

    Raises CapabilityGapError if gap not found or approval not rejected.
    """
    gap_path = gaps_log if gaps_log is not None else gap_store_mod.DEFAULT_GAPS_LOG
    approval_path = approvals_log if approvals_log is not None else approval_store_mod.DEFAULT_APPROVALS_LOG

    gap_store = GapStore(gap_path)
    gap = gap_store.get(gap_id)
    if gap is None:
        raise CapabilityGapError(f"Gap {gap_id} not found")

    from src.approval_center.store import ApprovalStore
    req = ApprovalStore(approval_path).get(approval_id)
    if req is None:
        raise CapabilityGapError(f"Approval {approval_id} not found")
    if req.status != APPROVAL_STATUS_REJECTED:
        raise CapabilityGapError(
            f"Cannot mark gap as dismissed: approval {approval_id} is '{req.status}', not 'rejected'"
        )

    gap.status = GAP_STATUS_DISMISSED
    gap_store.save(gap)
    return gap
