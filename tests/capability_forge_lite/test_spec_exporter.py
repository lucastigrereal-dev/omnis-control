"""Tests for Capability Spec Exporter."""
import json
import pytest
from pathlib import Path
from src.capability_forge_lite import store as store_mod
from src.capability_forge_lite.store import ProposalStore
from src.capability_forge_lite.models import CapabilityProposal
from src.capability_forge_lite.spec_exporter import export_spec, DEFAULT_SPECS_ROOT
from src.capability_forge_lite.errors import ProposalNotFoundError


def make_proposal(tmp_path, sector="apps", risk="high") -> CapabilityProposal:
    p = CapabilityProposal.from_gap("gap_abc", "crm_capability", sector, "crm_plan", risk_level=risk)
    ProposalStore(tmp_path / "proposals.jsonl").save(p)
    return p


def test_export_creates_spec_dir(tmp_path):
    p = make_proposal(tmp_path)
    spec_dir = export_spec(p.proposal_id, proposals_log=tmp_path / "proposals.jsonl", specs_root=tmp_path / "specs")
    assert spec_dir.is_dir()
    assert spec_dir.name == p.proposal_id


def test_export_creates_all_five_files(tmp_path):
    p = make_proposal(tmp_path)
    spec_dir = export_spec(p.proposal_id, proposals_log=tmp_path / "proposals.jsonl", specs_root=tmp_path / "specs")
    expected = [
        "capability_manifest.json",
        "CAPABILITY_SPEC.md",
        "implementation_plan.md",
        "risk_assessment.md",
        "next_actions.md",
    ]
    for fname in expected:
        assert (spec_dir / fname).exists(), f"Missing: {fname}"


def test_manifest_has_required_keys(tmp_path):
    p = make_proposal(tmp_path)
    spec_dir = export_spec(p.proposal_id, proposals_log=tmp_path / "proposals.jsonl", specs_root=tmp_path / "specs")
    manifest = json.loads((spec_dir / "capability_manifest.json").read_text(encoding="utf-8"))
    for key in ["proposal_id", "capability_name", "sector", "status", "spec_generated_at"]:
        assert key in manifest


def test_manifest_status_is_spec_draft(tmp_path):
    p = make_proposal(tmp_path)
    spec_dir = export_spec(p.proposal_id, proposals_log=tmp_path / "proposals.jsonl", specs_root=tmp_path / "specs")
    manifest = json.loads((spec_dir / "capability_manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "spec_draft"


def test_manifest_no_secrets(tmp_path):
    p = make_proposal(tmp_path)
    spec_dir = export_spec(p.proposal_id, proposals_log=tmp_path / "proposals.jsonl", specs_root=tmp_path / "specs")
    manifest = json.loads((spec_dir / "capability_manifest.json").read_text(encoding="utf-8"))
    forbidden = ("meta_", "instagram_", "secret", "token", "password", "api_key")
    for key in manifest:
        assert not any(key.lower().startswith(f) for f in forbidden), f"Forbidden key: {key}"


def test_export_proposal_not_found_raises(tmp_path):
    with pytest.raises(ProposalNotFoundError):
        export_spec("prop_ghost", proposals_log=tmp_path / "proposals.jsonl", specs_root=tmp_path / "specs")


def test_spec_md_contains_capability_name(tmp_path):
    p = make_proposal(tmp_path)
    spec_dir = export_spec(p.proposal_id, proposals_log=tmp_path / "proposals.jsonl", specs_root=tmp_path / "specs")
    content = (spec_dir / "CAPABILITY_SPEC.md").read_text(encoding="utf-8")
    assert p.capability_name in content


def test_impl_plan_varies_by_type(tmp_path):
    from src.capability_forge_lite.models import IMPL_TYPE_APP_FACTORY_FUTURE
    p_apps = CapabilityProposal.from_gap(
        "gap_abc", "crm_capability", "apps", "crm_plan",
        risk_level="high", implementation_type=IMPL_TYPE_APP_FACTORY_FUTURE,
    )
    ProposalStore(tmp_path / "proposals.jsonl").save(p_apps)
    spec_dir = export_spec(p_apps.proposal_id, proposals_log=tmp_path / "proposals.jsonl", specs_root=tmp_path / "specs")
    plan = (spec_dir / "implementation_plan.md").read_text(encoding="utf-8")
    assert "app_factory_future" in plan or "PRD" in plan


def test_next_actions_contains_register_step(tmp_path):
    p = make_proposal(tmp_path)
    spec_dir = export_spec(p.proposal_id, proposals_log=tmp_path / "proposals.jsonl", specs_root=tmp_path / "specs")
    actions = (spec_dir / "next_actions.md").read_text(encoding="utf-8")
    assert "register" in actions
