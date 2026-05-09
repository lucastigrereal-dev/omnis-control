"""Tests for Capability Registrar."""
import pytest
import yaml
from pathlib import Path
from src.capability_forge_lite import store as store_mod
from src.capability_forge_lite.store import ProposalStore
from src.capability_forge_lite.models import (
    CapabilityProposal,
    PROPOSAL_STATUS_APPROVED,
    PROPOSAL_STATUS_REGISTERED,
    IMPL_TYPE_APP_FACTORY_FUTURE,
)
from src.capability_forge_lite.registrar import register_capability
from src.capability_forge_lite.errors import (
    ProposalNotFoundError,
    ProposalNotApprovedError,
    DuplicateCapabilityError,
)


def make_approved_proposal(tmp_path) -> tuple[CapabilityProposal, Path]:
    p = CapabilityProposal.from_gap(
        "gap_reg", "hotel_booking_cap", "apps", "booking_plan",
        risk_level="high", implementation_type=IMPL_TYPE_APP_FACTORY_FUTURE,
    )
    p.status = PROPOSAL_STATUS_APPROVED
    ProposalStore(tmp_path / "proposals.jsonl").save(p)
    caps_path = tmp_path / "capabilities.yaml"
    caps_path.write_text("capabilities: {}\n", encoding="utf-8")
    return p, caps_path


def test_register_adds_entry_to_yaml(tmp_path):
    p, caps_path = make_approved_proposal(tmp_path)
    cap_id = register_capability(p.proposal_id, proposals_log=tmp_path / "proposals.jsonl", caps_path=caps_path)
    raw = yaml.safe_load(caps_path.read_text(encoding="utf-8"))
    assert cap_id in raw["capabilities"]


def test_register_status_is_planned(tmp_path):
    p, caps_path = make_approved_proposal(tmp_path)
    cap_id = register_capability(p.proposal_id, proposals_log=tmp_path / "proposals.jsonl", caps_path=caps_path)
    raw = yaml.safe_load(caps_path.read_text(encoding="utf-8"))
    assert raw["capabilities"][cap_id]["status"] == "planned"


def test_register_marks_proposal_as_registered(tmp_path):
    p, caps_path = make_approved_proposal(tmp_path)
    register_capability(p.proposal_id, proposals_log=tmp_path / "proposals.jsonl", caps_path=caps_path)
    updated = ProposalStore(tmp_path / "proposals.jsonl").get(p.proposal_id)
    assert updated.status == PROPOSAL_STATUS_REGISTERED


def test_register_proposal_not_found_raises(tmp_path):
    caps_path = tmp_path / "capabilities.yaml"
    caps_path.write_text("capabilities: {}\n", encoding="utf-8")
    with pytest.raises(ProposalNotFoundError):
        register_capability("prop_ghost", proposals_log=tmp_path / "proposals.jsonl", caps_path=caps_path)


def test_register_not_approved_raises(tmp_path):
    p = CapabilityProposal.from_gap("gap_na", "cap_na", "apps", "out_na", risk_level="high")
    ProposalStore(tmp_path / "proposals.jsonl").save(p)
    caps_path = tmp_path / "capabilities.yaml"
    caps_path.write_text("capabilities: {}\n", encoding="utf-8")
    with pytest.raises(ProposalNotApprovedError):
        register_capability(p.proposal_id, proposals_log=tmp_path / "proposals.jsonl", caps_path=caps_path)


def test_register_duplicate_raises(tmp_path):
    p, caps_path = make_approved_proposal(tmp_path)
    register_capability(p.proposal_id, proposals_log=tmp_path / "proposals.jsonl", caps_path=caps_path)
    p2 = CapabilityProposal.from_gap(
        "gap_reg2", "hotel_booking_cap", "apps", "booking_plan2",
        risk_level="high",
    )
    p2.status = PROPOSAL_STATUS_APPROVED
    ProposalStore(tmp_path / "proposals.jsonl").save(p2)
    with pytest.raises(DuplicateCapabilityError):
        register_capability(p2.proposal_id, proposals_log=tmp_path / "proposals.jsonl", caps_path=caps_path)


def test_matcher_sees_planned_with_flag(tmp_path):
    from src.skill_matcher.matcher import match_capabilities
    p, caps_path = make_approved_proposal(tmp_path)
    register_capability(p.proposal_id, proposals_log=tmp_path / "proposals.jsonl", caps_path=caps_path)
    results_no_flag = match_capabilities("hotel booking cap", config_path=caps_path, include_planned=False)
    results_with_flag = match_capabilities("hotel booking cap", config_path=caps_path, include_planned=True)
    assert len(results_no_flag) == 0
    assert len(results_with_flag) == 1


def test_register_preserves_existing_capabilities(tmp_path):
    caps_path = tmp_path / "capabilities.yaml"
    caps_path.write_text("capabilities:\n  existing_cap:\n    sector: marketing\n    status: active\n    command: test\n    output: out\n    risk_level: low\n    keywords: [test]\n", encoding="utf-8")
    p = CapabilityProposal.from_gap("gap_pres", "new_cap_test", "sales", "out_new", risk_level="high")
    p.status = PROPOSAL_STATUS_APPROVED
    ProposalStore(tmp_path / "proposals.jsonl").save(p)
    register_capability(p.proposal_id, proposals_log=tmp_path / "proposals.jsonl", caps_path=caps_path)
    raw = yaml.safe_load(caps_path.read_text(encoding="utf-8"))
    assert "existing_cap" in raw["capabilities"]
    assert "new_cap_test" in raw["capabilities"]
