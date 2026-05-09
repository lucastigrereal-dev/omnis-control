"""Tests for mission executor — run(), dry_run flag, manifest."""
import pytest
from pathlib import Path
from src.mission_builder.executor import run
from src.mission_builder.models import MissionPlan, MissionPackageManifest
from src.mission_builder.errors import IntentUnknownError
from src.mission_builder import package_exporter as exp_mod

CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "intents.yaml"


def test_run_dry_run_returns_plan_and_manifest(tmp_path, monkeypatch):
    monkeypatch.setattr(exp_mod, "PACKAGES_ROOT", tmp_path)
    plan, manifest = run(
        "cria um carrossel sobre praias",
        account_handle="oinatalrn",
        dry_run=True,
        config_path=CONFIG_PATH,
        packages_root=tmp_path,
    )
    assert isinstance(plan, MissionPlan)
    assert isinstance(manifest, MissionPackageManifest)


def test_run_dry_run_creates_package_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(exp_mod, "PACKAGES_ROOT", tmp_path)
    plan, manifest = run(
        "cria uma campanha de 10 posts",
        dry_run=True,
        config_path=CONFIG_PATH,
        packages_root=tmp_path,
    )
    assert Path(manifest.package_dir).is_dir()


def test_run_no_dry_run_returns_none_manifest(tmp_path):
    plan, manifest = run(
        "cria um reel curto",
        dry_run=False,
        config_path=CONFIG_PATH,
        packages_root=tmp_path,
    )
    assert isinstance(plan, MissionPlan)
    assert manifest is None


def test_run_raises_on_unknown_intent():
    with pytest.raises(IntentUnknownError):
        run("algo completamente genérico aqui", config_path=CONFIG_PATH)


def test_run_allow_unknown(tmp_path, monkeypatch):
    monkeypatch.setattr(exp_mod, "PACKAGES_ROOT", tmp_path)
    plan, manifest = run(
        "algo completamente genérico aqui",
        allow_unknown=True,
        dry_run=True,
        config_path=CONFIG_PATH,
        packages_root=tmp_path,
    )
    assert plan.intent == "unknown"
    assert manifest is not None


def test_run_sets_dry_run_flag_on_plan(tmp_path, monkeypatch):
    monkeypatch.setattr(exp_mod, "PACKAGES_ROOT", tmp_path)
    plan, _ = run(
        "cria um carrossel",
        dry_run=True,
        config_path=CONFIG_PATH,
        packages_root=tmp_path,
    )
    assert plan.dry_run is True
