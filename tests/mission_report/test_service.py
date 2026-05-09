"""Tests for mission_report service — close, get, list."""
import json
import pytest
from pathlib import Path
from src.mission_report import service as svc_mod
from src.mission_report.service import close_mission, get_report, list_reports
from src.mission_report.models import MissionReport
from src.mission_report.errors import (
    MissionNotFoundError,
    InvalidOutcomeError,
)


def _make_package(tmp_path: Path, mission_id: str, intent: str = "carousel") -> Path:
    pkg = tmp_path / "mission_packages" / mission_id
    pkg.mkdir(parents=True)
    manifest = {
        "mission_id": mission_id,
        "request_text": "cria um carrossel sobre Natal",
        "intent": intent,
        "deliverable": f"{intent}_package",
        "account_handle": "oinatalrn",
        "package_dir": str(pkg),
        "files": [],
        "dry_run": True,
        "created_at": "2026-05-09T00:00:00Z",
    }
    (pkg / "mission_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False), encoding="utf-8"
    )
    return pkg


@pytest.fixture
def pkgs_root(tmp_path):
    return tmp_path / "mission_packages"


@pytest.fixture
def reports_log(tmp_path):
    return tmp_path / "data" / "mission_reports.jsonl"


def test_close_creates_report_file(tmp_path, pkgs_root, reports_log):
    _make_package(tmp_path, "mb_test001")
    report = close_mission(
        "mb_test001",
        outcome="completed",
        packages_root=pkgs_root,
        reports_log=reports_log,
    )
    assert isinstance(report, MissionReport)
    report_file = pkgs_root / "mb_test001" / "07_mission_report.md"
    assert report_file.exists()
    content = report_file.read_text(encoding="utf-8")
    assert "COMPLETED" in content
    assert "mb_test001" in content


def test_close_appends_to_log(tmp_path, pkgs_root, reports_log):
    _make_package(tmp_path, "mb_test002")
    close_mission("mb_test002", outcome="completed", packages_root=pkgs_root, reports_log=reports_log)
    assert reports_log.exists()
    lines = [l for l in reports_log.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["mission_id"] == "mb_test002"
    assert data["outcome"] == "completed"


def test_close_cancelled_outcome(tmp_path, pkgs_root, reports_log):
    _make_package(tmp_path, "mb_test003")
    report = close_mission(
        "mb_test003",
        outcome="cancelled",
        notes="sem tempo esta semana",
        packages_root=pkgs_root,
        reports_log=reports_log,
    )
    assert report.outcome == "cancelled"
    assert report.notes == "sem tempo esta semana"


def test_close_deferred_outcome(tmp_path, pkgs_root, reports_log):
    _make_package(tmp_path, "mb_test004")
    report = close_mission(
        "mb_test004",
        outcome="deferred",
        packages_root=pkgs_root,
        reports_log=reports_log,
    )
    assert report.outcome == "deferred"


def test_close_invalid_outcome_raises(tmp_path, pkgs_root, reports_log):
    _make_package(tmp_path, "mb_test005")
    with pytest.raises(InvalidOutcomeError):
        close_mission("mb_test005", outcome="published", packages_root=pkgs_root, reports_log=reports_log)


def test_close_missing_package_raises(pkgs_root, reports_log):
    with pytest.raises(MissionNotFoundError):
        close_mission("mb_nonexistent", outcome="completed", packages_root=pkgs_root, reports_log=reports_log)


def test_close_with_url(tmp_path, pkgs_root, reports_log):
    _make_package(tmp_path, "mb_test006")
    report = close_mission(
        "mb_test006",
        outcome="completed",
        published_url="https://instagram.com/p/abc123",
        packages_root=pkgs_root,
        reports_log=reports_log,
    )
    assert report.published_url == "https://instagram.com/p/abc123"
    content = (pkgs_root / "mb_test006" / "07_mission_report.md").read_text(encoding="utf-8")
    assert "instagram.com" in content


def test_get_report_returns_most_recent(tmp_path, pkgs_root, reports_log):
    _make_package(tmp_path, "mb_get001")
    close_mission("mb_get001", outcome="completed", packages_root=pkgs_root, reports_log=reports_log)
    found = get_report("mb_get001", reports_log=reports_log)
    assert found is not None
    assert found.mission_id == "mb_get001"


def test_get_report_returns_none_when_missing(reports_log):
    result = get_report("mb_nonexistent", reports_log=reports_log)
    assert result is None


def test_list_reports_empty(reports_log):
    assert list_reports(reports_log=reports_log) == []


def test_list_reports_newest_first(tmp_path, pkgs_root, reports_log):
    _make_package(tmp_path, "mb_list001")
    _make_package(tmp_path, "mb_list002")
    close_mission("mb_list001", outcome="completed", packages_root=pkgs_root, reports_log=reports_log)
    close_mission("mb_list002", outcome="deferred", packages_root=pkgs_root, reports_log=reports_log)
    reports = list_reports(reports_log=reports_log)
    assert len(reports) == 2
    assert reports[0].mission_id == "mb_list002"  # newest first
    assert reports[1].mission_id == "mb_list001"
