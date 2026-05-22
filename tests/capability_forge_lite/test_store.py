"""Tests for ProposalStore."""
from src.capability_forge_real.models import CapabilityProposal
from src.capability_forge_real.store import ProposalStore


def make_proposal(gap_id="gap_001", risk="high") -> CapabilityProposal:
    return CapabilityProposal.from_gap(gap_id, "test_cap", "apps", "tech_spec", risk_level=risk)


def test_store_save_and_list(tmp_path):
    store = ProposalStore(tmp_path / "proposals.jsonl")
    p = make_proposal()
    store.save(p)
    proposals = store.list_all()
    assert len(proposals) == 1
    assert proposals[0].proposal_id == p.proposal_id


def test_store_list_empty(tmp_path):
    assert ProposalStore(tmp_path / "empty.jsonl").list_all() == []


def test_store_get_found(tmp_path):
    store = ProposalStore(tmp_path / "proposals.jsonl")
    p = make_proposal()
    store.save(p)
    found = store.get(p.proposal_id)
    assert found is not None
    assert found.proposal_id == p.proposal_id


def test_store_get_not_found(tmp_path):
    store = ProposalStore(tmp_path / "proposals.jsonl")
    assert store.get("prop_ghost") is None


def test_store_newest_first(tmp_path):
    store = ProposalStore(tmp_path / "proposals.jsonl")
    p1 = make_proposal("gap_001")
    p2 = make_proposal("gap_002")
    store.save(p1)
    store.save(p2)
    proposals = store.list_all()
    assert proposals[0].proposal_id == p2.proposal_id


def test_store_update_returns_latest(tmp_path):
    store = ProposalStore(tmp_path / "proposals.jsonl")
    p = make_proposal()
    store.save(p)
    p.status = "approved"
    store.update(p)
    found = store.get(p.proposal_id)
    assert found.status == "approved"
