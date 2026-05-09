"""Tests for capability proposal generator."""
import socket
import os
import pytest
from src.capability_forge_lite.proposal import propose_from_gap
from src.capability_forge_lite.errors import GapNotFoundError
from src.capability_forge_lite.models import PROPOSAL_STATUS_NEEDS_APPROVAL, PROPOSAL_STATUS_DRAFT
from src.capability_gap.models import CapabilityGap
from src.capability_gap.store import GapStore


def save_gap(tmp_path, sector="apps", risk_level="high") -> CapabilityGap:
    gap = CapabilityGap.new(
        request="cria crm sistema",
        sector=sector,
        missing_capability=f"{sector}_capability",
        desired_output="crm_app",
        risk_level=risk_level,
    )
    GapStore(tmp_path / "gaps.jsonl").save(gap)
    return gap


def test_existing_gap_generates_proposal(tmp_path):
    gap = save_gap(tmp_path)
    proposal = propose_from_gap(
        gap.gap_id,
        gaps_log=tmp_path / "gaps.jsonl",
        proposals_log=tmp_path / "proposals.jsonl",
    )
    assert proposal.proposal_id.startswith("prop_")
    assert proposal.gap_id == gap.gap_id
    assert proposal.sector == "apps"


def test_high_risk_proposal_needs_approval(tmp_path):
    gap = save_gap(tmp_path, risk_level="high")
    proposal = propose_from_gap(
        gap.gap_id,
        gaps_log=tmp_path / "gaps.jsonl",
        proposals_log=tmp_path / "proposals.jsonl",
    )
    assert proposal.approval_required is True
    assert proposal.status == PROPOSAL_STATUS_NEEDS_APPROVAL


def test_low_risk_proposal_no_approval(tmp_path):
    gap = save_gap(tmp_path, sector="marketing", risk_level="low")
    proposal = propose_from_gap(
        gap.gap_id,
        gaps_log=tmp_path / "gaps.jsonl",
        proposals_log=tmp_path / "proposals.jsonl",
    )
    assert proposal.approval_required is False
    assert proposal.status == PROPOSAL_STATUS_DRAFT


def test_gap_not_found_raises(tmp_path):
    with pytest.raises(GapNotFoundError):
        propose_from_gap(
            "gap_ghost",
            gaps_log=tmp_path / "gaps.jsonl",
            proposals_log=tmp_path / "proposals.jsonl",
        )


def test_proposal_persisted_in_store(tmp_path):
    from src.capability_forge_lite.store import ProposalStore
    gap = save_gap(tmp_path)
    proposal = propose_from_gap(
        gap.gap_id,
        gaps_log=tmp_path / "gaps.jsonl",
        proposals_log=tmp_path / "proposals.jsonl",
    )
    found = ProposalStore(tmp_path / "proposals.jsonl").get(proposal.proposal_id)
    assert found is not None
    assert found.proposal_id == proposal.proposal_id


def test_apps_sector_maps_to_app_factory_type(tmp_path):
    gap = save_gap(tmp_path, sector="apps", risk_level="high")
    proposal = propose_from_gap(
        gap.gap_id,
        gaps_log=tmp_path / "gaps.jsonl",
        proposals_log=tmp_path / "proposals.jsonl",
    )
    assert proposal.implementation_type == "app_factory_future"


def test_no_network_calls(monkeypatch, tmp_path):
    def _block(*args, **kwargs):
        raise AssertionError("Network blocked")
    monkeypatch.setattr(socket.socket, "connect", _block)
    gap = save_gap(tmp_path)
    propose_from_gap(gap.gap_id, gaps_log=tmp_path / "gaps.jsonl", proposals_log=tmp_path / "props.jsonl")


def test_no_env_reads(monkeypatch, tmp_path):
    original = os.getenv
    def _guard(key, *args, **kwargs):
        assert not key.startswith("META_") and not key.startswith("INSTAGRAM_")
        return original(key, *args, **kwargs)
    monkeypatch.setattr(os, "getenv", _guard)
    gap = save_gap(tmp_path)
    propose_from_gap(gap.gap_id, gaps_log=tmp_path / "gaps.jsonl", proposals_log=tmp_path / "props.jsonl")
