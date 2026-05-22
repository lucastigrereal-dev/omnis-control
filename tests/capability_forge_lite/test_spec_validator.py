"""Tests for Capability Spec Validator."""
import json
import pytest
from pathlib import Path
from src.capability_forge_real import store as store_mod
from src.capability_forge_real.store import ProposalStore
from src.capability_forge_real.models import CapabilityProposal
from src.capability_forge_real.spec_exporter import export_spec
from src.capability_forge_real.spec_validator import validate_spec
from src.capability_forge_real.errors import ProposalNotFoundError


def make_and_export(tmp_path, sector="apps", risk="high"):
    p = CapabilityProposal.from_gap("gap_xyz", "cap_test", sector, "plan_test", risk_level=risk)
    ProposalStore(tmp_path / "proposals.jsonl").save(p)
    spec_dir = export_spec(p.proposal_id, proposals_log=tmp_path / "proposals.jsonl", specs_root=tmp_path / "specs")
    return p, spec_dir


def test_valid_spec_returns_valid_true(tmp_path):
    p, _ = make_and_export(tmp_path)
    result = validate_spec(p.proposal_id, proposals_log=tmp_path / "proposals.jsonl", specs_root=tmp_path / "specs")
    assert result["valid"] is True
    assert result["files_missing"] == []
    assert result["manifest_errors"] == []


def test_missing_file_makes_invalid(tmp_path):
    p, spec_dir = make_and_export(tmp_path)
    (spec_dir / "risk_assessment.md").unlink()
    result = validate_spec(p.proposal_id, proposals_log=tmp_path / "proposals.jsonl", specs_root=tmp_path / "specs")
    assert result["valid"] is False
    assert "risk_assessment.md" in result["files_missing"]


def test_corrupt_manifest_makes_invalid(tmp_path):
    p, spec_dir = make_and_export(tmp_path)
    (spec_dir / "capability_manifest.json").write_text("not json", encoding="utf-8")
    result = validate_spec(p.proposal_id, proposals_log=tmp_path / "proposals.jsonl", specs_root=tmp_path / "specs")
    assert result["manifest_valid"] is False
    assert result["valid"] is False


def test_wrong_status_in_manifest_makes_invalid(tmp_path):
    p, spec_dir = make_and_export(tmp_path)
    manifest_path = spec_dir / "capability_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["status"] = "active"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    result = validate_spec(p.proposal_id, proposals_log=tmp_path / "proposals.jsonl", specs_root=tmp_path / "specs")
    assert result["manifest_valid"] is False
    assert any("status" in err for err in result["manifest_errors"])


def test_proposal_not_found_raises(tmp_path):
    with pytest.raises(ProposalNotFoundError):
        validate_spec("prop_ghost", proposals_log=tmp_path / "proposals.jsonl", specs_root=tmp_path / "specs")


def test_result_contains_spec_dir_path(tmp_path):
    p, spec_dir = make_and_export(tmp_path)
    result = validate_spec(p.proposal_id, proposals_log=tmp_path / "proposals.jsonl", specs_root=tmp_path / "specs")
    assert str(spec_dir) == result["spec_dir"]


def test_no_secrets_flag_true_for_clean_manifest(tmp_path):
    p, _ = make_and_export(tmp_path)
    result = validate_spec(p.proposal_id, proposals_log=tmp_path / "proposals.jsonl", specs_root=tmp_path / "specs")
    assert result["no_secrets"] is True
