"""Tests for Capability Approval Bridge."""
import pytest
from src.capability_forge_lite import store as store_mod
from src.capability_forge_lite.store import ProposalStore
from src.capability_forge_lite.models import (
    CapabilityProposal,
    PROPOSAL_STATUS_APPROVED,
    PROPOSAL_STATUS_REJECTED,
    PROPOSAL_STATUS_NEEDS_APPROVAL,
)
from src.capability_forge_lite.approval_bridge import (
    request_proposal_approval,
    mark_proposal_approved,
    mark_proposal_rejected,
    get_approval_status,
)
from src.capability_forge_lite.errors import ProposalNotFoundError, ProposalNotApprovedError
from src.approval_center import store as approval_store_mod
from src.approval_center.store import ApprovalStore
from src.approval_center.errors import ApprovalAlreadyResolvedError


def make_proposal(tmp_path, risk="high") -> CapabilityProposal:
    p = CapabilityProposal.from_gap("gap_t1", "cap_test", "apps", "plan_test", risk_level=risk)
    ProposalStore(tmp_path / "proposals.jsonl").save(p)
    return p


def test_request_approval_returns_request_id(tmp_path):
    p = make_proposal(tmp_path)
    request_id = request_proposal_approval(
        p.proposal_id,
        proposals_log=tmp_path / "proposals.jsonl",
        approvals_log=tmp_path / "approvals.jsonl",
    )
    assert request_id.startswith("req_")


def test_request_approval_links_to_proposal(tmp_path):
    p = make_proposal(tmp_path)
    request_id = request_proposal_approval(
        p.proposal_id,
        proposals_log=tmp_path / "proposals.jsonl",
        approvals_log=tmp_path / "approvals.jsonl",
    )
    updated = ProposalStore(tmp_path / "proposals.jsonl").get(p.proposal_id)
    assert updated.approval_id == request_id


def test_request_approval_proposal_not_found(tmp_path):
    with pytest.raises(ProposalNotFoundError):
        request_proposal_approval(
            "prop_ghost",
            proposals_log=tmp_path / "proposals.jsonl",
            approvals_log=tmp_path / "approvals.jsonl",
        )


def test_mark_approved_updates_proposal_status(tmp_path):
    p = make_proposal(tmp_path)
    request_proposal_approval(
        p.proposal_id,
        proposals_log=tmp_path / "proposals.jsonl",
        approvals_log=tmp_path / "approvals.jsonl",
    )
    mark_proposal_approved(
        p.proposal_id,
        proposals_log=tmp_path / "proposals.jsonl",
        approvals_log=tmp_path / "approvals.jsonl",
    )
    updated = ProposalStore(tmp_path / "proposals.jsonl").get(p.proposal_id)
    assert updated.status == PROPOSAL_STATUS_APPROVED


def test_mark_rejected_updates_proposal_status(tmp_path):
    p = make_proposal(tmp_path)
    request_proposal_approval(
        p.proposal_id,
        proposals_log=tmp_path / "proposals.jsonl",
        approvals_log=tmp_path / "approvals.jsonl",
    )
    mark_proposal_rejected(
        p.proposal_id,
        proposals_log=tmp_path / "proposals.jsonl",
        approvals_log=tmp_path / "approvals.jsonl",
    )
    updated = ProposalStore(tmp_path / "proposals.jsonl").get(p.proposal_id)
    assert updated.status == PROPOSAL_STATUS_REJECTED


def test_mark_approved_no_approval_id_raises(tmp_path):
    p = make_proposal(tmp_path)
    with pytest.raises(ProposalNotApprovedError):
        mark_proposal_approved(
            p.proposal_id,
            proposals_log=tmp_path / "proposals.jsonl",
            approvals_log=tmp_path / "approvals.jsonl",
        )


def test_get_approval_status_returns_pending(tmp_path):
    p = make_proposal(tmp_path)
    request_proposal_approval(
        p.proposal_id,
        proposals_log=tmp_path / "proposals.jsonl",
        approvals_log=tmp_path / "approvals.jsonl",
    )
    status = get_approval_status(
        p.proposal_id,
        proposals_log=tmp_path / "proposals.jsonl",
        approvals_log=tmp_path / "approvals.jsonl",
    )
    assert status == "pending"


def test_get_approval_status_none_when_no_request(tmp_path):
    p = make_proposal(tmp_path)
    status = get_approval_status(
        p.proposal_id,
        proposals_log=tmp_path / "proposals.jsonl",
        approvals_log=tmp_path / "approvals.jsonl",
    )
    assert status is None
