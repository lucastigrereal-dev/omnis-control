"""Tests for B8C — Asset Inbox Assignment (17 tests)."""
import json
import pytest
from pathlib import Path
from typer.testing import CliRunner
from src.cli import app

from src.asset_inbox import importer as imp_mod
from src.asset_inbox import registry as reg_mod
from src.asset_inbox import assignment as asgn_mod
from src.asset_inbox.assignment import (
    assign_to_queue,
    assign_to_mission,
    ASSIGN_STATUS_OK,
    ASSIGN_STATUS_NOT_FOUND,
    ASSIGN_STATUS_QUEUE_NOT_FOUND,
    ASSIGN_STATUS_MISSION_NOT_FOUND,
    ASSIGN_STATUS_ALREADY_ASSIGNED,
)

runner = CliRunner()


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_file(parent: Path, name: str, content: bytes = b"fake asset") -> Path:
    p = parent / name
    p.write_bytes(content)
    return p


def make_imported_asset(tmp_path: Path) -> tuple[str, Path, Path]:
    """Import a file and return (asset_id, storage, reg_path)."""
    storage = tmp_path / "storage"
    reg = tmp_path / "reg.jsonl"
    f = make_file(tmp_path, "photo.jpg")
    result = imp_mod.import_asset(
        str(f),
        storage_root=storage,
        registry_path=reg,
    )
    assert result.status == "imported"
    return result.asset.asset_id, storage, reg


def make_queue_item(queue_path: Path, queue_id: str = "q_test001") -> None:
    """Write a minimal QueueItem directly to the JSONL file."""
    from src.content_queue.models import QueueItem
    item = QueueItem(
        queue_id=queue_id,
        account_handle="lucastigrereal",
        date="2026-06-01",
        time="09:00",
    )
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    with queue_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(item.to_dict(), ensure_ascii=False) + "\n")


def make_mission_package(packages_root: Path, mission_id: str, with_manifest: bool = True) -> Path:
    """Create a minimal mission package directory."""
    pkg_dir = packages_root / mission_id
    pkg_dir.mkdir(parents=True, exist_ok=True)
    if with_manifest:
        manifest = {
            "mission_id": mission_id,
            "intent": "viagem_hotel",
            "account_handle": "oinatalrn",
            "status": "ready",
        }
        (pkg_dir / "mission_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return pkg_dir


# ── assign_to_queue tests ─────────────────────────────────────────────────────

def test_assign_to_queue_success(tmp_path):
    asset_id, storage, reg = make_imported_asset(tmp_path)
    queue_path = tmp_path / "queue.jsonl"
    va_path = str(tmp_path / "va.jsonl")
    make_queue_item(queue_path)

    result = assign_to_queue(
        asset_id=asset_id,
        queue_id="q_test001",
        inbox_registry_path=reg,
        video_assets_path=va_path,
        queue_path=str(queue_path),
    )
    assert result.status == ASSIGN_STATUS_OK
    assert result.target_type == "queue"
    assert result.target_id == "q_test001"
    assert not result.blockers


def test_assign_to_queue_asset_not_found(tmp_path):
    queue_path = tmp_path / "queue.jsonl"
    make_queue_item(queue_path)
    reg = tmp_path / "empty_reg.jsonl"

    result = assign_to_queue(
        asset_id="ai_nonexistent",
        queue_id="q_test001",
        inbox_registry_path=reg,
        video_assets_path=str(tmp_path / "va.jsonl"),
        queue_path=str(queue_path),
    )
    assert result.status == ASSIGN_STATUS_NOT_FOUND
    assert result.blockers


def test_assign_to_queue_item_not_found(tmp_path):
    asset_id, storage, reg = make_imported_asset(tmp_path)
    queue_path = tmp_path / "queue.jsonl"  # empty — no items

    result = assign_to_queue(
        asset_id=asset_id,
        queue_id="q_ghost",
        inbox_registry_path=reg,
        video_assets_path=str(tmp_path / "va.jsonl"),
        queue_path=str(queue_path),
    )
    assert result.status == ASSIGN_STATUS_QUEUE_NOT_FOUND
    assert result.blockers


def test_assign_to_queue_already_assigned_no_force(tmp_path):
    asset_id, storage, reg = make_imported_asset(tmp_path)
    queue_path = tmp_path / "queue.jsonl"
    va_path = str(tmp_path / "va.jsonl")
    make_queue_item(queue_path)

    # First assign
    assign_to_queue(
        asset_id=asset_id,
        queue_id="q_test001",
        inbox_registry_path=reg,
        video_assets_path=va_path,
        queue_path=str(queue_path),
    )

    # Import a second different asset
    f2 = make_file(tmp_path, "clip.mp4", b"different content")
    r2 = imp_mod.import_asset(str(f2), storage_root=storage, registry_path=reg)
    assert r2.status == "imported"

    # Try to assign second asset without force
    result = assign_to_queue(
        asset_id=r2.asset.asset_id,
        queue_id="q_test001",
        inbox_registry_path=reg,
        video_assets_path=va_path,
        queue_path=str(queue_path),
    )
    assert result.status == ASSIGN_STATUS_ALREADY_ASSIGNED
    assert result.blockers


def test_assign_to_queue_force_override(tmp_path):
    asset_id, storage, reg = make_imported_asset(tmp_path)
    queue_path = tmp_path / "queue.jsonl"
    va_path = str(tmp_path / "va.jsonl")
    make_queue_item(queue_path)

    assign_to_queue(
        asset_id=asset_id,
        queue_id="q_test001",
        inbox_registry_path=reg,
        video_assets_path=va_path,
        queue_path=str(queue_path),
    )

    f2 = make_file(tmp_path, "clip.mp4", b"other content")
    r2 = imp_mod.import_asset(str(f2), storage_root=storage, registry_path=reg)

    result = assign_to_queue(
        asset_id=r2.asset.asset_id,
        queue_id="q_test001",
        force=True,
        inbox_registry_path=reg,
        video_assets_path=va_path,
        queue_path=str(queue_path),
    )
    assert result.status == ASSIGN_STATUS_OK
    assert any("Overriding" in w for w in result.warnings)


def test_assign_to_queue_creates_video_asset_entry(tmp_path):
    asset_id, storage, reg = make_imported_asset(tmp_path)
    queue_path = tmp_path / "queue.jsonl"
    va_path = tmp_path / "va.jsonl"
    make_queue_item(queue_path)

    assign_to_queue(
        asset_id=asset_id,
        queue_id="q_test001",
        inbox_registry_path=reg,
        video_assets_path=str(va_path),
        queue_path=str(queue_path),
    )

    from src.video_assets.registry import Registry as VARegistry
    va_reg = VARegistry(path=str(va_path))
    va = va_reg.get(asset_id)
    assert va is not None
    assert va.asset_id == asset_id
    assert va.source_type == "local"


def test_assign_to_queue_no_duplicate_video_asset(tmp_path):
    asset_id, storage, reg = make_imported_asset(tmp_path)
    queue_path = tmp_path / "queue.jsonl"
    va_path = tmp_path / "va.jsonl"
    make_queue_item(queue_path, queue_id="q_slot1")
    make_queue_item(queue_path, queue_id="q_slot2")

    assign_to_queue(
        asset_id=asset_id, queue_id="q_slot1",
        inbox_registry_path=reg, video_assets_path=str(va_path), queue_path=str(queue_path),
    )
    assign_to_queue(
        asset_id=asset_id, queue_id="q_slot2",
        force=True,
        inbox_registry_path=reg, video_assets_path=str(va_path), queue_path=str(queue_path),
    )

    from src.video_assets.registry import Registry as VARegistry
    va_reg = VARegistry(path=str(va_path))
    entries = [a for a in va_reg.list_all() if a.asset_id == asset_id]
    assert len(entries) == 1  # not duplicated


# ── assign_to_mission tests ───────────────────────────────────────────────────

def test_assign_to_mission_success(tmp_path):
    asset_id, storage, reg = make_imported_asset(tmp_path)
    packages_root = tmp_path / "packages"
    make_mission_package(packages_root, "mb_mission001")

    result = assign_to_mission(
        asset_id=asset_id,
        mission_id="mb_mission001",
        inbox_registry_path=reg,
        packages_root=packages_root,
    )
    assert result.status == ASSIGN_STATUS_OK
    assert result.target_type == "mission"
    assert not result.blockers


def test_assign_to_mission_asset_not_found(tmp_path):
    packages_root = tmp_path / "packages"
    make_mission_package(packages_root, "mb_mission001")

    result = assign_to_mission(
        asset_id="ai_ghost",
        mission_id="mb_mission001",
        inbox_registry_path=tmp_path / "empty.jsonl",
        packages_root=packages_root,
    )
    assert result.status == ASSIGN_STATUS_NOT_FOUND
    assert result.blockers


def test_assign_to_mission_package_not_found(tmp_path):
    asset_id, storage, reg = make_imported_asset(tmp_path)
    packages_root = tmp_path / "packages"  # empty — no package dir

    result = assign_to_mission(
        asset_id=asset_id,
        mission_id="mb_nonexistent",
        inbox_registry_path=reg,
        packages_root=packages_root,
    )
    assert result.status == ASSIGN_STATUS_MISSION_NOT_FOUND
    assert result.blockers


def test_assign_to_mission_creates_asset_reference(tmp_path):
    asset_id, storage, reg = make_imported_asset(tmp_path)
    packages_root = tmp_path / "packages"
    make_mission_package(packages_root, "mb_mission001")

    assign_to_mission(
        asset_id=asset_id,
        mission_id="mb_mission001",
        inbox_registry_path=reg,
        packages_root=packages_root,
    )

    ref_path = packages_root / "mb_mission001" / "04_outputs" / "asset_reference.json"
    assert ref_path.exists()
    data = json.loads(ref_path.read_text(encoding="utf-8"))
    assert data["asset_id"] == asset_id
    assert data["mission_id"] == "mb_mission001"
    assert data["fingerprint_match"] is True


def test_assign_to_mission_updates_manifest(tmp_path):
    asset_id, storage, reg = make_imported_asset(tmp_path)
    packages_root = tmp_path / "packages"
    make_mission_package(packages_root, "mb_mission001", with_manifest=True)

    assign_to_mission(
        asset_id=asset_id,
        mission_id="mb_mission001",
        inbox_registry_path=reg,
        packages_root=packages_root,
    )

    manifest = json.loads(
        (packages_root / "mb_mission001" / "mission_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["assigned_asset_id"] == asset_id
    assert "assigned_at" in manifest


def test_assign_to_mission_no_manifest_ok(tmp_path):
    asset_id, storage, reg = make_imported_asset(tmp_path)
    packages_root = tmp_path / "packages"
    make_mission_package(packages_root, "mb_mission001", with_manifest=False)

    result = assign_to_mission(
        asset_id=asset_id,
        mission_id="mb_mission001",
        inbox_registry_path=reg,
        packages_root=packages_root,
    )
    assert result.status == ASSIGN_STATUS_OK
    assert any("not found" in w for w in result.warnings)
    ref_path = packages_root / "mb_mission001" / "04_outputs" / "asset_reference.json"
    assert ref_path.exists()


# ── CLI assign tests ──────────────────────────────────────────────────────────

def test_cli_assign_no_target(tmp_path, monkeypatch):
    monkeypatch.setattr(imp_mod, "DEFAULT_STORAGE_ROOT", tmp_path / "storage")
    monkeypatch.setattr(imp_mod, "DEFAULT_REGISTRY_PATH", tmp_path / "reg.jsonl")
    monkeypatch.setattr(reg_mod, "DEFAULT_REGISTRY_PATH", tmp_path / "reg.jsonl")
    result = runner.invoke(app, ["asset-inbox", "assign", "ai_fake"])
    assert result.exit_code != 0


def test_cli_assign_queue_success(tmp_path, monkeypatch):
    storage = tmp_path / "storage"
    reg = tmp_path / "reg.jsonl"
    va_path = str(tmp_path / "va.jsonl")
    queue_path = str(tmp_path / "queue.jsonl")

    monkeypatch.setattr(imp_mod, "DEFAULT_STORAGE_ROOT", storage)
    monkeypatch.setattr(imp_mod, "DEFAULT_REGISTRY_PATH", reg)
    monkeypatch.setattr(reg_mod, "DEFAULT_REGISTRY_PATH", reg)
    monkeypatch.setattr(asgn_mod, "DEFAULT_INBOX_REGISTRY_PATH", reg)
    monkeypatch.setattr(asgn_mod, "DEFAULT_VIDEO_ASSETS_PATH", va_path)
    monkeypatch.setattr(asgn_mod, "DEFAULT_QUEUE_PATH", queue_path)

    f = make_file(tmp_path, "photo.jpg")
    import_result = runner.invoke(app, ["asset-inbox", "import", str(f), "--json"])
    asset_id = json.loads(import_result.output)["asset"]["asset_id"]

    make_queue_item(Path(queue_path))
    result = runner.invoke(app, ["asset-inbox", "assign", asset_id, "--queue", "q_test001"])
    assert result.exit_code == 0, result.output
    assert "assigned" in result.output.lower() or "q_test001" in result.output


def test_cli_assign_queue_json(tmp_path, monkeypatch):
    storage = tmp_path / "storage"
    reg = tmp_path / "reg.jsonl"
    va_path = str(tmp_path / "va.jsonl")
    queue_path = str(tmp_path / "queue.jsonl")

    monkeypatch.setattr(imp_mod, "DEFAULT_STORAGE_ROOT", storage)
    monkeypatch.setattr(imp_mod, "DEFAULT_REGISTRY_PATH", reg)
    monkeypatch.setattr(reg_mod, "DEFAULT_REGISTRY_PATH", reg)
    monkeypatch.setattr(asgn_mod, "DEFAULT_INBOX_REGISTRY_PATH", reg)
    monkeypatch.setattr(asgn_mod, "DEFAULT_VIDEO_ASSETS_PATH", va_path)
    monkeypatch.setattr(asgn_mod, "DEFAULT_QUEUE_PATH", queue_path)

    f = make_file(tmp_path, "clip.mp4", b"video content")
    import_result = runner.invoke(app, ["asset-inbox", "import", str(f), "--json"])
    asset_id = json.loads(import_result.output)["asset"]["asset_id"]

    make_queue_item(Path(queue_path))
    result = runner.invoke(app, ["asset-inbox", "assign", asset_id, "--queue", "q_test001", "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["status"] == "assigned"
    assert data["target_type"] == "queue"
    assert "B8D" in str(data["next_actions"])


def test_cli_assign_mission_success(tmp_path, monkeypatch):
    storage = tmp_path / "storage"
    reg = tmp_path / "reg.jsonl"
    packages_root = tmp_path / "packages"

    monkeypatch.setattr(imp_mod, "DEFAULT_STORAGE_ROOT", storage)
    monkeypatch.setattr(imp_mod, "DEFAULT_REGISTRY_PATH", reg)
    monkeypatch.setattr(reg_mod, "DEFAULT_REGISTRY_PATH", reg)
    monkeypatch.setattr(asgn_mod, "DEFAULT_INBOX_REGISTRY_PATH", reg)
    monkeypatch.setattr(asgn_mod, "DEFAULT_PACKAGES_ROOT", packages_root)

    f = make_file(tmp_path, "photo.jpg")
    import_result = runner.invoke(app, ["asset-inbox", "import", str(f), "--json"])
    asset_id = json.loads(import_result.output)["asset"]["asset_id"]

    make_mission_package(packages_root, "mb_mission001")
    result = runner.invoke(
        app, ["asset-inbox", "assign", asset_id, "--mission", "mb_mission001", "--json"]
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["status"] == "assigned"
    assert data["target_type"] == "mission"
