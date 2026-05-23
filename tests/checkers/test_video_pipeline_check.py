"""Tests for video_pipeline_check checker."""
from __future__ import annotations

from src.checkers import video_pipeline_check


def test_check_operational_when_strong_signals_are_present(monkeypatch):
    monkeypatch.setattr(video_pipeline_check, "_load_config", lambda: {})
    monkeypatch.setattr(
        video_pipeline_check,
        "_scan_local_video_files",
        lambda roots, exts, timeout_s: {
            "files": ["C:/videos/a.mp4"],
            "count": 1,
            "timed_out": False,
        },
    )
    monkeypatch.setattr(
        video_pipeline_check,
        "_check_keyword_in_path",
        lambda roots, keywords: [
            {"path": "C:/app/assets", "keyword": "asset", "type": "dir"},
            {"path": "C:/app/queue", "keyword": "queue", "type": "dir"},
            {"path": "C:/app/instagram", "keyword": "instagram", "type": "dir"},
        ],
    )
    monkeypatch.setattr(video_pipeline_check, "_check_video_to_content_skill", lambda: [])
    monkeypatch.setattr(
        video_pipeline_check,
        "_check_argos_bridge_skill",
        lambda: [{"path": "C:/skills/argos", "keyword": "argos-bridge", "type": "skill_integration"}],
    )
    monkeypatch.setattr(
        video_pipeline_check,
        "_check_publisher_video_code",
        lambda: [{"path": "C:/publisher/job.py", "keyword": "published", "type": "publisher_code"}],
    )
    monkeypatch.setattr(
        video_pipeline_check,
        "_check_video_asset_registry",
        lambda: {"exists": True, "asset_count": 2},
    )
    monkeypatch.setattr(
        video_pipeline_check,
        "_check_account_registry",
        lambda: {"exists": True, "account_count": 1},
    )
    monkeypatch.setattr(
        video_pipeline_check,
        "_check_content_queue",
        lambda: {"exists": True, "item_count": 3},
    )

    result = video_pipeline_check.check()

    assert result["classification"] == "operational"
    assert result["confidence"] == "high"
    assert result["counts"]["local_video_files"] == 1
    assert result["counts"]["registry_assets"] == 2
    assert result["signals"]["content_queue_found_explicit"] is True


def test_check_not_found_when_no_evidence(monkeypatch):
    monkeypatch.setattr(video_pipeline_check, "_load_config", lambda: {})
    monkeypatch.setattr(
        video_pipeline_check,
        "_scan_local_video_files",
        lambda roots, exts, timeout_s: {"files": [], "count": 0, "timed_out": False},
    )
    monkeypatch.setattr(video_pipeline_check, "_check_keyword_in_path", lambda roots, keywords: [])
    monkeypatch.setattr(video_pipeline_check, "_check_video_to_content_skill", lambda: [])
    monkeypatch.setattr(video_pipeline_check, "_check_argos_bridge_skill", lambda: [])
    monkeypatch.setattr(video_pipeline_check, "_check_publisher_video_code", lambda: [])
    monkeypatch.setattr(
        video_pipeline_check,
        "_check_video_asset_registry",
        lambda: {"exists": False, "asset_count": 0},
    )
    monkeypatch.setattr(
        video_pipeline_check,
        "_check_account_registry",
        lambda: {"exists": False, "account_count": 0},
    )
    monkeypatch.setattr(
        video_pipeline_check,
        "_check_content_queue",
        lambda: {"exists": False, "item_count": 0},
    )

    result = video_pipeline_check.check()

    assert result["classification"] == "not_found"
    assert result["confidence"] == "high"
    assert result["evidence"] == []
    assert "Nenhum pipeline de vídeo detectado" in result["risks"][0]
