"""Tests for offline_dashboard service."""
import json
import pytest
from pathlib import Path

import src.offline_dashboard.service as dash_svc


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def _make_package(root: Path, pkg_id: str, status: str) -> None:
    d = root / pkg_id
    d.mkdir(parents=True, exist_ok=True)
    (d / "manifest.json").write_text(
        json.dumps({"status": status}), encoding="utf-8"
    )


@pytest.fixture
def patched_paths(tmp_path, monkeypatch):
    export_root = tmp_path / "exports" / "offline_factory"
    render_root = tmp_path / "exports" / "rendered"
    campaigns_root = tmp_path / "exports" / "campaigns"
    delivery_root = tmp_path / "exports" / "client_delivery"
    manual_log = tmp_path / "data" / "manual_publishing_log.jsonl"
    scores_log = tmp_path / "data" / "quality_scores.jsonl"

    monkeypatch.setattr(dash_svc, "EXPORT_ROOT", export_root)
    monkeypatch.setattr(dash_svc, "RENDER_ROOT", render_root)
    monkeypatch.setattr(dash_svc, "CAMPAIGNS_ROOT", campaigns_root)
    monkeypatch.setattr(dash_svc, "DELIVERY_ROOT", delivery_root)
    monkeypatch.setattr(dash_svc, "MANUAL_LOG", manual_log)
    monkeypatch.setattr(dash_svc, "SCORES_LOG", scores_log)

    return tmp_path


class TestGetDashboardData:
    def test_returns_dict_with_required_keys(self, patched_paths):
        data = dash_svc.get_dashboard_data()
        assert "packages" in data
        assert "renders" in data
        assert "quality" in data
        assert "campaigns" in data
        assert "deliveries" in data
        assert "manual_published" in data
        assert "oauth_gate" in data

    def test_empty_dirs_return_zero_counts(self, patched_paths):
        data = dash_svc.get_dashboard_data()
        assert data["packages"]["total"] == 0
        assert data["renders"] == 0
        assert data["campaigns"]["total"] == 0
        assert data["deliveries"] == 0
        assert data["manual_published"] == 0

    def test_package_status_counts(self, patched_paths, monkeypatch):
        export_root = patched_paths / "exports" / "offline_factory"
        monkeypatch.setattr(dash_svc, "EXPORT_ROOT", export_root)
        _make_package(export_root, "pkg_ready_001", "ready")
        _make_package(export_root, "pkg_blocked_001", "blocked")
        _make_package(export_root, "pkg_blocked_002", "blocked")

        data = dash_svc.get_dashboard_data()
        assert data["packages"]["total"] == 3
        assert data["packages"]["by_status"]["ready"] == 1
        assert data["packages"]["by_status"]["blocked"] == 2

    def test_render_count(self, patched_paths, monkeypatch):
        render_root = patched_paths / "exports" / "rendered"
        render_root.mkdir(parents=True, exist_ok=True)
        (render_root / "render_001").mkdir()
        (render_root / "render_002").mkdir()
        monkeypatch.setattr(dash_svc, "RENDER_ROOT", render_root)

        data = dash_svc.get_dashboard_data()
        assert data["renders"] == 2

    def test_quality_avg_score(self, patched_paths, monkeypatch):
        scores_log = patched_paths / "data" / "quality_scores.jsonl"
        monkeypatch.setattr(dash_svc, "SCORES_LOG", scores_log)
        _write_jsonl(scores_log, [
            {"score": 90, "package_id": "p1"},
            {"score": 70, "package_id": "p2"},
        ])

        data = dash_svc.get_dashboard_data()
        assert data["quality"]["scored_count"] == 2
        assert data["quality"]["avg_score"] == 80.0

    def test_quality_empty_scores(self, patched_paths):
        data = dash_svc.get_dashboard_data()
        assert data["quality"]["scored_count"] == 0
        assert data["quality"]["avg_score"] is None

    def test_manual_published_count(self, patched_paths, monkeypatch):
        manual_log = patched_paths / "data" / "manual_publishing_log.jsonl"
        monkeypatch.setattr(dash_svc, "MANUAL_LOG", manual_log)
        _write_jsonl(manual_log, [
            {"package_id": "pkg1", "platform": "instagram"},
            {"package_id": "pkg2", "platform": "instagram"},
        ])

        data = dash_svc.get_dashboard_data()
        assert data["manual_published"] == 2

    def test_oauth_gate_structure(self, patched_paths):
        data = dash_svc.get_dashboard_data()
        assert "ready" in data["oauth_gate"]
        assert "target" in data["oauth_gate"]
        assert "go" in data["oauth_gate"]
        assert data["oauth_gate"]["target"] == 5
        assert isinstance(data["oauth_gate"]["go"], bool)

    def test_no_network_calls(self, patched_paths):
        from unittest.mock import patch
        with patch("requests.post") as mock_post, \
             patch("requests.get") as mock_get:
            dash_svc.get_dashboard_data()
            mock_post.assert_not_called()
            mock_get.assert_not_called()

    def test_nonexistent_dirs_safe(self, patched_paths):
        """Dashboard must not raise when export dirs don't exist yet."""
        data = dash_svc.get_dashboard_data()
        assert data["packages"]["total"] == 0
