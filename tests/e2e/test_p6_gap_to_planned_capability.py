"""E2E: Gap → Proposal → Spec → Approval → Planned Capability (P6 full flow)."""
import json
import yaml
import pytest
from pathlib import Path

from src.capability_gap.models import CapabilityGap
from src.capability_gap.store import GapStore
from src.capability_forge_real import store as store_mod
from src.capability_forge_real.store import ProposalStore
from src.capability_forge_real.proposal import propose_from_gap
from src.capability_forge_real.spec_exporter import export_spec
from src.capability_forge_real.spec_validator import validate_spec
from src.capability_forge_real.approval_bridge import (
    request_proposal_approval,
    mark_proposal_approved,
    mark_proposal_rejected,
    get_approval_status,
)
from src.capability_forge_real.registrar import register_capability
from src.capability_forge_real.models import (
    PROPOSAL_STATUS_APPROVED,
    PROPOSAL_STATUS_REJECTED,
    PROPOSAL_STATUS_REGISTERED,
    PROPOSAL_STATUS_NEEDS_APPROVAL,
)
from src.capability_forge_real.errors import (
    ProposalNotApprovedError,
    DuplicateCapabilityError,
)
from src.skill_matcher.matcher import match_capabilities, list_capabilities


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def store_paths(tmp_path):
    return {
        "gaps": tmp_path / "gaps.jsonl",
        "proposals": tmp_path / "proposals.jsonl",
        "approvals": tmp_path / "approvals.jsonl",
        "caps": tmp_path / "capabilities.yaml",
        "specs": tmp_path / "specs",
    }


@pytest.fixture()
def blank_caps(store_paths):
    store_paths["caps"].write_text("capabilities: {}\n", encoding="utf-8")
    return store_paths["caps"]


def save_gap(paths, request="cria sistema crm enterprise", sector="apps", risk="high") -> CapabilityGap:
    gap = CapabilityGap.new(
        request=request,
        sector=sector,
        missing_capability=f"{sector}_crm_capability",
        desired_output="crm_system",
        risk_level=risk,
    )
    GapStore(paths["gaps"]).save(gap)
    return gap


# ---------------------------------------------------------------------------
# Phase 1: Gap → Proposal
# ---------------------------------------------------------------------------

def test_e2e_gap_generates_proposal(store_paths):
    gap = save_gap(store_paths)
    proposal = propose_from_gap(gap.gap_id, gaps_log=store_paths["gaps"], proposals_log=store_paths["proposals"])
    assert proposal.proposal_id.startswith("prop_")
    assert proposal.gap_id == gap.gap_id
    assert proposal.sector == "apps"


def test_e2e_high_risk_proposal_needs_approval(store_paths):
    gap = save_gap(store_paths, risk="high")
    proposal = propose_from_gap(gap.gap_id, gaps_log=store_paths["gaps"], proposals_log=store_paths["proposals"])
    assert proposal.approval_required is True
    assert proposal.status == PROPOSAL_STATUS_NEEDS_APPROVAL


# ---------------------------------------------------------------------------
# Phase 2: Proposal → Spec Export + Validation
# ---------------------------------------------------------------------------

def test_e2e_spec_export_and_valid(store_paths):
    gap = save_gap(store_paths)
    proposal = propose_from_gap(gap.gap_id, gaps_log=store_paths["gaps"], proposals_log=store_paths["proposals"])
    spec_dir = export_spec(proposal.proposal_id, proposals_log=store_paths["proposals"], specs_root=store_paths["specs"])
    result = validate_spec(proposal.proposal_id, proposals_log=store_paths["proposals"], specs_root=store_paths["specs"])
    assert result["valid"] is True
    assert result["files_missing"] == []


def test_e2e_spec_manifest_contains_proposal_data(store_paths):
    gap = save_gap(store_paths)
    proposal = propose_from_gap(gap.gap_id, gaps_log=store_paths["gaps"], proposals_log=store_paths["proposals"])
    spec_dir = export_spec(proposal.proposal_id, proposals_log=store_paths["proposals"], specs_root=store_paths["specs"])
    manifest = json.loads((spec_dir / "capability_manifest.json").read_text(encoding="utf-8"))
    assert manifest["proposal_id"] == proposal.proposal_id
    assert manifest["sector"] == "apps"
    assert manifest["status"] == "spec_draft"


# ---------------------------------------------------------------------------
# Phase 3: Approval flow
# ---------------------------------------------------------------------------

def test_e2e_request_approval_links_to_proposal(store_paths):
    gap = save_gap(store_paths)
    proposal = propose_from_gap(gap.gap_id, gaps_log=store_paths["gaps"], proposals_log=store_paths["proposals"])
    request_id = request_proposal_approval(
        proposal.proposal_id,
        proposals_log=store_paths["proposals"],
        approvals_log=store_paths["approvals"],
    )
    updated = ProposalStore(store_paths["proposals"]).get(proposal.proposal_id)
    assert updated.approval_id == request_id
    assert get_approval_status(proposal.proposal_id, proposals_log=store_paths["proposals"], approvals_log=store_paths["approvals"]) == "pending"


def test_e2e_approve_updates_proposal_status(store_paths):
    gap = save_gap(store_paths)
    proposal = propose_from_gap(gap.gap_id, gaps_log=store_paths["gaps"], proposals_log=store_paths["proposals"])
    request_proposal_approval(proposal.proposal_id, proposals_log=store_paths["proposals"], approvals_log=store_paths["approvals"])
    mark_proposal_approved(proposal.proposal_id, proposals_log=store_paths["proposals"], approvals_log=store_paths["approvals"])
    updated = ProposalStore(store_paths["proposals"]).get(proposal.proposal_id)
    assert updated.status == PROPOSAL_STATUS_APPROVED


def test_e2e_reject_blocks_registration(store_paths, blank_caps):
    gap = save_gap(store_paths)
    proposal = propose_from_gap(gap.gap_id, gaps_log=store_paths["gaps"], proposals_log=store_paths["proposals"])
    request_proposal_approval(proposal.proposal_id, proposals_log=store_paths["proposals"], approvals_log=store_paths["approvals"])
    mark_proposal_rejected(proposal.proposal_id, proposals_log=store_paths["proposals"], approvals_log=store_paths["approvals"])
    updated = ProposalStore(store_paths["proposals"]).get(proposal.proposal_id)
    assert updated.status == PROPOSAL_STATUS_REJECTED
    with pytest.raises(ProposalNotApprovedError):
        register_capability(proposal.proposal_id, proposals_log=store_paths["proposals"], caps_path=blank_caps)


# ---------------------------------------------------------------------------
# Phase 4: Registration → Planned
# ---------------------------------------------------------------------------

def test_e2e_full_flow_gap_to_registered(store_paths, blank_caps):
    gap = save_gap(store_paths)
    proposal = propose_from_gap(gap.gap_id, gaps_log=store_paths["gaps"], proposals_log=store_paths["proposals"])
    request_proposal_approval(proposal.proposal_id, proposals_log=store_paths["proposals"], approvals_log=store_paths["approvals"])
    mark_proposal_approved(proposal.proposal_id, proposals_log=store_paths["proposals"], approvals_log=store_paths["approvals"])
    cap_id = register_capability(proposal.proposal_id, proposals_log=store_paths["proposals"], caps_path=blank_caps)
    raw = yaml.safe_load(blank_caps.read_text(encoding="utf-8"))
    assert cap_id in raw["capabilities"]
    assert raw["capabilities"][cap_id]["status"] == "planned"
    final = ProposalStore(store_paths["proposals"]).get(proposal.proposal_id)
    assert final.status == PROPOSAL_STATUS_REGISTERED


def test_e2e_planned_cap_visible_with_include_planned(store_paths, blank_caps):
    gap = save_gap(store_paths, request="apps crm sistema enterprise crm_crm")
    proposal = propose_from_gap(gap.gap_id, gaps_log=store_paths["gaps"], proposals_log=store_paths["proposals"])
    request_proposal_approval(proposal.proposal_id, proposals_log=store_paths["proposals"], approvals_log=store_paths["approvals"])
    mark_proposal_approved(proposal.proposal_id, proposals_log=store_paths["proposals"], approvals_log=store_paths["approvals"])
    register_capability(proposal.proposal_id, proposals_log=store_paths["proposals"], caps_path=blank_caps)
    cap_name = proposal.capability_name
    results_active = match_capabilities(cap_name.replace("_", " "), config_path=blank_caps, include_planned=False)
    results_planned = match_capabilities(cap_name.replace("_", " "), config_path=blank_caps, include_planned=True)
    assert len(results_active) == 0
    assert len(results_planned) == 1
    assert results_planned[0].capability_id == cap_name.replace(" ", "_").lower()


def test_e2e_duplicate_registration_raises(store_paths, blank_caps):
    gap = save_gap(store_paths)
    proposal = propose_from_gap(gap.gap_id, gaps_log=store_paths["gaps"], proposals_log=store_paths["proposals"])
    request_proposal_approval(proposal.proposal_id, proposals_log=store_paths["proposals"], approvals_log=store_paths["approvals"])
    mark_proposal_approved(proposal.proposal_id, proposals_log=store_paths["proposals"], approvals_log=store_paths["approvals"])
    register_capability(proposal.proposal_id, proposals_log=store_paths["proposals"], caps_path=blank_caps)
    proposal2 = propose_from_gap(gap.gap_id, gaps_log=store_paths["gaps"], proposals_log=store_paths["proposals"])
    request_proposal_approval(proposal2.proposal_id, proposals_log=store_paths["proposals"], approvals_log=store_paths["approvals"])
    mark_proposal_approved(proposal2.proposal_id, proposals_log=store_paths["proposals"], approvals_log=store_paths["approvals"])
    with pytest.raises(DuplicateCapabilityError):
        register_capability(proposal2.proposal_id, proposals_log=store_paths["proposals"], caps_path=blank_caps)


def test_e2e_low_risk_gap_to_draft_and_register(store_paths, blank_caps):
    """Low-risk gap → draft proposal (no approval gate) → register directly."""
    gap = save_gap(store_paths, request="exportar relatorio pdf", sector="marketing", risk="low")
    proposal = propose_from_gap(gap.gap_id, gaps_log=store_paths["gaps"], proposals_log=store_paths["proposals"])
    assert proposal.approval_required is False
    proposal.status = PROPOSAL_STATUS_APPROVED
    ProposalStore(store_paths["proposals"]).update(proposal)
    cap_id = register_capability(proposal.proposal_id, proposals_log=store_paths["proposals"], caps_path=blank_caps)
    raw = yaml.safe_load(blank_caps.read_text(encoding="utf-8"))
    assert cap_id in raw["capabilities"]


def test_e2e_no_network_calls(monkeypatch, store_paths, blank_caps):
    import socket
    def _block(*args, **kwargs):
        raise AssertionError("Network blocked in P6 E2E")
    monkeypatch.setattr(socket.socket, "connect", _block)
    gap = save_gap(store_paths)
    proposal = propose_from_gap(gap.gap_id, gaps_log=store_paths["gaps"], proposals_log=store_paths["proposals"])
    request_proposal_approval(proposal.proposal_id, proposals_log=store_paths["proposals"], approvals_log=store_paths["approvals"])
    mark_proposal_approved(proposal.proposal_id, proposals_log=store_paths["proposals"], approvals_log=store_paths["approvals"])
    register_capability(proposal.proposal_id, proposals_log=store_paths["proposals"], caps_path=blank_caps)
