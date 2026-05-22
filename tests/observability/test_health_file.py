"""Tests for filesystem health bridge — OMNIS ↔ KRATOS health contract."""
from __future__ import annotations

import json

from src.observability.health_file import write_health_file, read_health_file


def test_write_and_read_health_file(tmp_path):
    path = tmp_path / "omnis_health.json"
    components = {
        "redis": {"status": "healthy", "score": 0.95, "message": "connected"},
        "postgres": {"status": "healthy", "score": 0.90, "message": "connected"},
        "event_bus": {"status": "degraded", "score": 0.70, "message": "slow"},
    }
    written = write_health_file(components, path=path)
    assert written == path
    assert path.exists()

    data = read_health_file(path=path)
    assert data is not None
    assert data["overall_status"] == "degraded"
    assert data["component_count"] == 3
    assert data["healthy_count"] == 2
    assert data["degraded_count"] == 1
    assert data["unhealthy_count"] == 0
    assert "timestamp" in data
    assert len(data["components"]) == 3


def test_read_nonexistent():
    data = read_health_file(path=None)
    # Default path may or may not exist; test with temp path
    from pathlib import Path
    import tempfile
    p = Path(tempfile.gettempdir()) / "nonexistent_health.json"
    assert read_health_file(path=p) is None


def test_all_healthy():
    components = {
        "redis": {"status": "healthy", "score": 0.99},
        "postgres": {"status": "healthy", "score": 0.98},
    }
    report_path = write_health_file(components)
    data = read_health_file(path=report_path)
    assert data["overall_status"] == "healthy"
    assert data["healthy_count"] == 2


def test_all_unhealthy():
    components = {
        "redis": {"status": "unhealthy", "score": 0.0},
        "postgres": {"status": "healthy", "score": 0.95},
    }
    report_path = write_health_file(components)
    data = read_health_file(path=report_path)
    assert data["overall_status"] == "unhealthy"
    assert data["unhealthy_count"] == 1


def test_empty_components():
    components: dict = {}
    report_path = write_health_file(components)
    data = read_health_file(path=report_path)
    assert data["overall_status"] == "unknown"
    assert data["component_count"] == 0


def test_roundtrip_preserves_scores():
    components = {
        "docker": {"status": "healthy", "score": 0.88, "message": "11/17 up"},
        "ollama": {"status": "healthy", "score": 0.92, "message": "qwen2.5-coder:7b active"},
    }
    report_path = write_health_file(components)
    data = read_health_file(path=report_path)
    assert data["components"]["docker"]["score"] == 0.88
    assert data["components"]["ollama"]["message"] == "qwen2.5-coder:7b active"
