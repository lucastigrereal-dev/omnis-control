"""B8D — E2E Smoke Mission: full offline pipeline.

Flow:
  1. mission-builder run  → creates mission package
  2. import fake asset     → stored copy + inbox registry
  3. assign to mission     → asset_reference.json + manifest updated
  4. validate package      → all required files present + quality checks
  5. mission-report close  → outcome recorded + report file written

NUNCA chama rede. NUNCA publica. NUNCA toca original.
"""
import json
import zipfile
import pytest
from pathlib import Path

from src.asset_inbox import importer as imp_mod
from src.asset_inbox import registry as reg_mod
from src.asset_inbox import assignment as asgn_mod
from src.asset_inbox.assignment import assign_to_mission, ASSIGN_STATUS_OK
from src.asset_inbox.importer import import_asset
from src.mission_builder.executor import run as mb_run
from src.mission_report import service as rpt_svc


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def workspace(tmp_path):
    """Isolated workspace for the full E2E test."""
    return {
        "packages_root": tmp_path / "mission_packages",
        "storage_root": tmp_path / "asset_storage",
        "inbox_reg": tmp_path / "inbox_registry.jsonl",
        "reports_log": tmp_path / "mission_reports.jsonl",
        "asset_file": tmp_path / "test_asset.jpg",
    }


def _make_asset_file(path: Path, content: bytes = b"fake jpg content for e2e") -> Path:
    path.write_bytes(content)
    return path


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_e2e_mission_builder_creates_package(workspace):
    """Step 1: mission-builder run creates expected package structure."""
    plan, manifest = mb_run(
        request_text="quero postar um reel do hotel em Natal",
        account_handle="oinatalrn",
        dry_run=True,
        packages_root=workspace["packages_root"],
    )

    assert manifest is not None
    assert manifest.mission_id
    pkg_dir = Path(manifest.package_dir)
    assert pkg_dir.exists()
    assert (pkg_dir / "mission_manifest.json").exists()
    assert (pkg_dir / "01_mission_brief.md").exists()
    assert (pkg_dir / "03_execution_plan.md").exists()
    assert (pkg_dir / "04_outputs").is_dir()


def test_e2e_import_asset(workspace):
    """Step 2: import_asset copies file and records in registry."""
    _make_asset_file(workspace["asset_file"])

    result = import_asset(
        source_path=str(workspace["asset_file"]),
        storage_root=workspace["storage_root"],
        registry_path=workspace["inbox_reg"],
    )

    assert result.status == "imported"
    assert result.asset is not None
    assert Path(result.asset.stored_path).exists()
    assert result.asset.fingerprint_match is True
    assert workspace["asset_file"].exists()  # original untouched


def test_e2e_assign_to_mission(workspace):
    """Step 3: assign imported asset to mission package."""
    # Build package
    plan, manifest = mb_run(
        request_text="reel gastronomia Natal",
        account_handle="oquecomernatalrn",
        dry_run=True,
        packages_root=workspace["packages_root"],
    )
    pkg_dir = Path(manifest.package_dir)

    # Import asset
    _make_asset_file(workspace["asset_file"])
    imp_result = import_asset(
        source_path=str(workspace["asset_file"]),
        storage_root=workspace["storage_root"],
        registry_path=workspace["inbox_reg"],
    )

    # Assign
    asgn_result = assign_to_mission(
        asset_id=imp_result.asset.asset_id,
        mission_id=manifest.mission_id,
        inbox_registry_path=workspace["inbox_reg"],
        packages_root=workspace["packages_root"],
    )

    assert asgn_result.status == ASSIGN_STATUS_OK
    assert not asgn_result.blockers

    # asset_reference.json must exist
    ref_path = pkg_dir / "04_outputs" / "asset_reference.json"
    assert ref_path.exists()
    ref_data = json.loads(ref_path.read_text(encoding="utf-8"))
    assert ref_data["asset_id"] == imp_result.asset.asset_id
    assert ref_data["fingerprint_match"] is True

    # mission_manifest.json updated
    manifest_data = json.loads((pkg_dir / "mission_manifest.json").read_text(encoding="utf-8"))
    assert manifest_data.get("assigned_asset_id") == imp_result.asset.asset_id


def test_e2e_package_quality_validation(workspace):
    """Step 4: full package has all required files and quality >= 90%."""
    # Build + import + assign
    plan, manifest = mb_run(
        request_text="carrossel viagem familia RN",
        account_handle="afamiliatigrereal",
        dry_run=True,
        packages_root=workspace["packages_root"],
    )
    _make_asset_file(workspace["asset_file"])
    imp_result = import_asset(
        source_path=str(workspace["asset_file"]),
        storage_root=workspace["storage_root"],
        registry_path=workspace["inbox_reg"],
    )
    assign_to_mission(
        asset_id=imp_result.asset.asset_id,
        mission_id=manifest.mission_id,
        inbox_registry_path=workspace["inbox_reg"],
        packages_root=workspace["packages_root"],
    )

    pkg_dir = Path(manifest.package_dir)
    required_files = [
        "mission_manifest.json",
        "01_mission_brief.md",
        "02_context_used.md",
        "03_execution_plan.md",
        "04_outputs",
        "06_next_action.md",
    ]
    for fname in required_files:
        assert (pkg_dir / fname).exists(), f"Missing: {fname}"

    # asset_reference.json present (quality requirement)
    assert (pkg_dir / "04_outputs" / "asset_reference.json").exists()

    # Quality score: count present required files
    present = sum(1 for f in required_files if (pkg_dir / f).exists())
    plus_asset_ref = 1 if (pkg_dir / "04_outputs" / "asset_reference.json").exists() else 0
    total_checks = len(required_files) + 1  # +1 for asset_reference
    score = (present + plus_asset_ref) / total_checks * 100
    assert score >= 90, f"Package quality {score:.0f}% < 90%"


def test_e2e_mission_report_close(workspace):
    """Step 5: close mission records outcome in report + log."""
    plan, manifest = mb_run(
        request_text="reels autoridade hotel boutique",
        account_handle="lucastigrereal",
        dry_run=True,
        packages_root=workspace["packages_root"],
    )
    _make_asset_file(workspace["asset_file"])
    imp_result = import_asset(
        source_path=str(workspace["asset_file"]),
        storage_root=workspace["storage_root"],
        registry_path=workspace["inbox_reg"],
    )
    assign_to_mission(
        asset_id=imp_result.asset.asset_id,
        mission_id=manifest.mission_id,
        inbox_registry_path=workspace["inbox_reg"],
        packages_root=workspace["packages_root"],
    )

    report = rpt_svc.close_mission(
        mission_id=manifest.mission_id,
        outcome="completed",
        notes="E2E smoke test — pipeline validated",
        packages_root=workspace["packages_root"],
        reports_log=workspace["reports_log"],
    )

    assert report.mission_id == manifest.mission_id
    assert report.outcome == "completed"
    assert workspace["reports_log"].exists()

    # Report file written inside package
    pkg_dir = Path(manifest.package_dir)
    report_file = pkg_dir / "07_mission_report.md"
    assert report_file.exists()
    content = report_file.read_text(encoding="utf-8")
    assert "COMPLETED" in content or "completed" in content.lower()


def test_e2e_original_file_never_touched(workspace):
    """Original file must be untouched throughout the entire pipeline."""
    original_content = b"immutable original asset content"
    _make_asset_file(workspace["asset_file"], original_content)

    plan, manifest = mb_run(
        request_text="reel para hotel Natal",
        account_handle="oinatalrn",
        dry_run=True,
        packages_root=workspace["packages_root"],
    )
    imp_result = import_asset(
        source_path=str(workspace["asset_file"]),
        storage_root=workspace["storage_root"],
        registry_path=workspace["inbox_reg"],
    )
    assign_to_mission(
        asset_id=imp_result.asset.asset_id,
        mission_id=manifest.mission_id,
        inbox_registry_path=workspace["inbox_reg"],
        packages_root=workspace["packages_root"],
    )

    assert workspace["asset_file"].exists()
    assert workspace["asset_file"].read_bytes() == original_content


def test_e2e_no_network_calls(workspace, monkeypatch):
    """Full pipeline must not make any network calls."""
    import socket

    def _block_network(*args, **kwargs):
        raise AssertionError("Network call blocked in E2E test")

    monkeypatch.setattr(socket.socket, "connect", _block_network)

    plan, manifest = mb_run(
        request_text="stories praia Natal",
        account_handle="natalaivoueu",
        dry_run=True,
        packages_root=workspace["packages_root"],
    )
    _make_asset_file(workspace["asset_file"])
    imp_result = import_asset(
        source_path=str(workspace["asset_file"]),
        storage_root=workspace["storage_root"],
        registry_path=workspace["inbox_reg"],
    )
    assign_to_mission(
        asset_id=imp_result.asset.asset_id,
        mission_id=manifest.mission_id,
        inbox_registry_path=workspace["inbox_reg"],
        packages_root=workspace["packages_root"],
    )
    # If no AssertionError was raised, no network calls were made
