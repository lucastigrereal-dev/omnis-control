"""Tests for package_exporter — file creation, structure, no network."""
import json
import pytest
from pathlib import Path
from src.mission_builder.planner import build_plan
from src.mission_builder import package_exporter as exp_mod
from src.mission_builder.package_exporter import export_package
from src.mission_builder.models import MissionPackageManifest

CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "intents.yaml"

REQUIRED_FILES = {
    "01_mission_brief.md",
    "02_context_used.md",
    "03_execution_plan.md",
    "06_next_action.md",
    "mission_manifest.json",
}
REQUIRED_DIRS = {"04_outputs", "05_exports"}


@pytest.fixture
def plan(tmp_path):
    return build_plan("cria um carrossel sobre turismo em Natal", config_path=CONFIG_PATH)


def test_export_creates_required_files(plan, tmp_path, monkeypatch):
    monkeypatch.setattr(exp_mod, "PACKAGES_ROOT", tmp_path)
    manifest = export_package(plan, packages_root=tmp_path)
    pkg = Path(manifest.package_dir)
    for fname in REQUIRED_FILES:
        assert (pkg / fname).exists(), f"Missing: {fname}"


def test_export_creates_required_dirs(plan, tmp_path, monkeypatch):
    monkeypatch.setattr(exp_mod, "PACKAGES_ROOT", tmp_path)
    manifest = export_package(plan, packages_root=tmp_path)
    pkg = Path(manifest.package_dir)
    for dname in REQUIRED_DIRS:
        assert (pkg / dname).is_dir(), f"Missing dir: {dname}"


def test_export_manifest_json_valid(plan, tmp_path):
    manifest = export_package(plan, packages_root=tmp_path)
    manifest_path = Path(manifest.package_dir) / "mission_manifest.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert data["intent"] == "carousel"
    assert data["dry_run"] is True
    assert data["mission_id"] == plan.mission_id


def test_export_returns_manifest_instance(plan, tmp_path):
    manifest = export_package(plan, packages_root=tmp_path)
    assert isinstance(manifest, MissionPackageManifest)
    assert len(manifest.files) >= len(REQUIRED_FILES)


def test_export_brief_contains_mission_id(plan, tmp_path):
    manifest = export_package(plan, packages_root=tmp_path)
    brief = (Path(manifest.package_dir) / "01_mission_brief.md").read_text(encoding="utf-8")
    assert plan.mission_id in brief


def test_export_no_network_calls(plan, tmp_path, monkeypatch):
    import socket
    def _blocked(*args, **kwargs):
        raise AssertionError("Network call — not allowed in export_package")
    monkeypatch.setattr(socket.socket, "connect", _blocked)
    manifest = export_package(plan, packages_root=tmp_path)
    assert manifest is not None


def test_src_missions_not_imported():
    """mission_builder source must not directly import from src.missions."""
    import inspect
    import src.mission_builder.package_exporter as mod
    import src.mission_builder.planner as planner_mod
    import src.mission_builder.intent as intent_mod
    for m in (mod, planner_mod, intent_mod):
        src_code = inspect.getsource(m)
        assert "from src.missions" not in src_code, f"Found src.missions import in {m.__name__}"
        assert "import src.missions" not in src_code, f"Found src.missions import in {m.__name__}"
