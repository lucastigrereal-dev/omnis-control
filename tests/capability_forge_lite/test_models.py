"""Tests for Capability Forge Lite models."""
from src.capability_forge_lite.models import (
    CapabilityProposal,
    PROPOSAL_STATUS_DRAFT,
    PROPOSAL_STATUS_NEEDS_APPROVAL,
    IMPL_TYPE_MANUAL_PROCESS,
    IMPL_TYPE_APP_FACTORY_FUTURE,
)


def test_proposal_from_gap_generates_id():
    p = CapabilityProposal.from_gap(
        gap_id="gap_abc123",
        capability_name="crm_capability",
        sector="sales",
        desired_output="crm_plan",
        risk_level="low",
    )
    assert p.proposal_id.startswith("prop_")
    assert p.gap_id == "gap_abc123"
    assert p.status == PROPOSAL_STATUS_DRAFT


def test_proposal_medium_risk_needs_approval():
    p = CapabilityProposal.from_gap(
        "gap_x", "cap_x", "apps", "output_x", risk_level="medium"
    )
    assert p.approval_required is True
    assert p.status == PROPOSAL_STATUS_NEEDS_APPROVAL


def test_proposal_high_risk_needs_approval():
    p = CapabilityProposal.from_gap(
        "gap_x", "cap_x", "apps", "output_x", risk_level="high"
    )
    assert p.approval_required is True


def test_proposal_low_risk_no_approval():
    p = CapabilityProposal.from_gap(
        "gap_x", "cap_low", "marketing", "output_x", risk_level="low"
    )
    assert p.approval_required is False
    assert p.status == PROPOSAL_STATUS_DRAFT


def test_proposal_to_dict_round_trip():
    p = CapabilityProposal.from_gap(
        "gap_abc", "my_cap", "apps", "tech_spec", risk_level="high",
        implementation_type=IMPL_TYPE_APP_FACTORY_FUTURE,
    )
    d = p.to_dict()
    p2 = CapabilityProposal.from_dict(d)
    assert p2.proposal_id == p.proposal_id
    assert p2.implementation_type == IMPL_TYPE_APP_FACTORY_FUTURE
    assert p2.approval_required is True
