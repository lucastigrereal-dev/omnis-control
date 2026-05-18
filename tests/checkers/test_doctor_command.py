"""Tests for jarvis doctor command."""
from __future__ import annotations

import json
import pytest
from typer.testing import CliRunner


@pytest.fixture
def runner():
    return CliRunner()


class TestDoctorCommand:
    def test_doctor_returns_json(self, runner, monkeypatch):
        """doctor command outputs valid JSON with expected top-level keys."""
        # Mock all checkers to return safe stubs
        mock_disk = {"severity": "ok", "disks": [], "critical": [], "warning": [], "summary": "Ok"}
        mock_docker = {"containers_running": 0, "containers_unhealthy": 0, "containers": [], "error": None}
        mock_publisher = {"status": "port_closed", "port_open": False}
        mock_memory = {"overall": "ok", "qdrant": {"accessible": False}, "akasha": {"container_found": False}}
        mock_obsidian = {"vault_found": False, "vault_path": "/nonexistent"}
        mock_skills = {"total": 0, "executable": 0, "doc_folder": 0, "doc_file": 0, "orphan_skills": [], "registry_missing_from_disk": [], "registry_available": False}
        mock_video = {"classification": "not_found", "confidence": "high", "signals": {}, "counts": {}, "evidence": [], "risks": []}

        monkeypatch.setattr("src.checkers.disk_check.check", lambda: mock_disk)
        monkeypatch.setattr("src.checkers.docker_check.check", lambda: mock_docker)
        monkeypatch.setattr("src.checkers.publisher_check.check", lambda: mock_publisher)
        monkeypatch.setattr("src.checkers.memory_check.check", lambda: mock_memory)
        monkeypatch.setattr("src.checkers.obsidian_check.check", lambda: mock_obsidian)
        monkeypatch.setattr("src.checkers.skills_check.check", lambda: mock_skills)
        monkeypatch.setattr("src.checkers.video_pipeline_check.check", lambda: mock_video)

        from src.cli import app

        result = runner.invoke(app, ["doctor"])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert "session_id" in data
        assert "timestamp" in data
        assert "overall_status" in data
        assert "checks" in data
        assert "risks" in data
        assert "next_steps" in data

    def test_doctor_overall_ok_when_all_healthy(self, runner, monkeypatch):
        """overall_status is 'ok' when all checks pass."""
        mock_disk = {"severity": "ok", "disks": [], "critical": [], "warning": [], "summary": "Ok"}
        mock_docker = {"containers_running": 1, "containers_unhealthy": 0, "containers": [], "error": None}
        mock_publisher = {"status": "ok", "port_open": True}
        mock_memory = {"overall": "ok", "qdrant": {"accessible": True}, "akasha": {"container_found": True}}
        mock_obsidian = {"vault_found": True, "vault_path": "/tmp", "md_file_count": 10}
        mock_skills = {"total": 5, "executable": 3, "doc_folder": 2, "doc_file": 0, "orphan_skills": [], "registry_missing_from_disk": [], "registry_available": True}
        mock_video = {"classification": "operational", "confidence": "high", "signals": {}, "counts": {}, "evidence": [], "risks": []}

        monkeypatch.setattr("src.checkers.disk_check.check", lambda: mock_disk)
        monkeypatch.setattr("src.checkers.docker_check.check", lambda: mock_docker)
        monkeypatch.setattr("src.checkers.publisher_check.check", lambda: mock_publisher)
        monkeypatch.setattr("src.checkers.memory_check.check", lambda: mock_memory)
        monkeypatch.setattr("src.checkers.obsidian_check.check", lambda: mock_obsidian)
        monkeypatch.setattr("src.checkers.skills_check.check", lambda: mock_skills)
        monkeypatch.setattr("src.checkers.video_pipeline_check.check", lambda: mock_video)

        from src.cli import app

        result = runner.invoke(app, ["doctor"])
        data = json.loads(result.stdout)
        assert data["overall_status"] == "ok"

    def test_doctor_overall_warning_when_disk_warning(self, runner, monkeypatch):
        """overall_status is 'warning' when disk has warnings."""
        mock_disk = {"severity": "warning", "disks": [], "critical": [], "warning": ["D:\\"], "summary": ""}
        mock_docker = {"containers_running": 0, "containers_unhealthy": 0, "containers": [], "error": None}
        mock_publisher = {"status": "port_closed", "port_open": False}
        mock_memory = {"overall": "ok", "qdrant": {"accessible": False}, "akasha": {"container_found": False}}
        mock_obsidian = {"vault_found": False, "vault_path": "/nonexistent"}
        mock_skills = {"total": 0, "executable": 0, "doc_folder": 0, "doc_file": 0, "orphan_skills": [], "registry_missing_from_disk": [], "registry_available": False}
        mock_video = {"classification": "not_found", "confidence": "high", "signals": {}, "counts": {}, "evidence": [], "risks": []}

        monkeypatch.setattr("src.checkers.disk_check.check", lambda: mock_disk)
        monkeypatch.setattr("src.checkers.docker_check.check", lambda: mock_docker)
        monkeypatch.setattr("src.checkers.publisher_check.check", lambda: mock_publisher)
        monkeypatch.setattr("src.checkers.memory_check.check", lambda: mock_memory)
        monkeypatch.setattr("src.checkers.obsidian_check.check", lambda: mock_obsidian)
        monkeypatch.setattr("src.checkers.skills_check.check", lambda: mock_skills)
        monkeypatch.setattr("src.checkers.video_pipeline_check.check", lambda: mock_video)

        from src.cli import app

        result = runner.invoke(app, ["doctor"])
        data = json.loads(result.stdout)
        assert data["overall_status"] == "warning"

    def test_doctor_overall_critical_when_check_fails(self, runner, monkeypatch):
        """overall_status is 'critical' when a checker raises exception."""
        def _failing_check():
            raise RuntimeError("checker exploded")

        mock_docker = {"containers_running": 0, "containers_unhealthy": 0, "containers": [], "error": None}
        mock_publisher = {"status": "port_closed", "port_open": False}
        mock_memory = {"overall": "ok", "qdrant": {"accessible": False}, "akasha": {"container_found": False}}
        mock_obsidian = {"vault_found": False, "vault_path": "/nonexistent"}
        mock_skills = {"total": 0, "executable": 0, "doc_folder": 0, "doc_file": 0, "orphan_skills": [], "registry_missing_from_disk": [], "registry_available": False}
        mock_video = {"classification": "not_found", "confidence": "high", "signals": {}, "counts": {}, "evidence": [], "risks": []}

        monkeypatch.setattr("src.checkers.disk_check.check", _failing_check)
        monkeypatch.setattr("src.checkers.docker_check.check", lambda: mock_docker)
        monkeypatch.setattr("src.checkers.publisher_check.check", lambda: mock_publisher)
        monkeypatch.setattr("src.checkers.memory_check.check", lambda: mock_memory)
        monkeypatch.setattr("src.checkers.obsidian_check.check", lambda: mock_obsidian)
        monkeypatch.setattr("src.checkers.skills_check.check", lambda: mock_skills)
        monkeypatch.setattr("src.checkers.video_pipeline_check.check", lambda: mock_video)

        from src.cli import app

        result = runner.invoke(app, ["doctor"])
        data = json.loads(result.stdout)
        assert data["overall_status"] == "critical"
        # The failing check should have an error entry
        disk_check = next(c for c in data["checks"] if c["name"] == "disk")
        assert "error" in disk_check

    def test_doctor_includes_all_check_names(self, runner, monkeypatch):
        """doctor output includes all expected check names."""
        mock_disk = {"severity": "ok", "disks": [], "critical": [], "warning": [], "summary": "Ok"}
        mock_docker = {"containers_running": 0, "containers_unhealthy": 0, "containers": [], "error": None}
        mock_publisher = {"status": "port_closed", "port_open": False}
        mock_memory = {"overall": "ok", "qdrant": {"accessible": False}, "akasha": {"container_found": False}}
        mock_obsidian = {"vault_found": False, "vault_path": "/nonexistent"}
        mock_skills = {"total": 0, "executable": 0, "doc_folder": 0, "doc_file": 0, "orphan_skills": [], "registry_missing_from_disk": [], "registry_available": False}
        mock_video = {"classification": "not_found", "confidence": "high", "signals": {}, "counts": {}, "evidence": [], "risks": []}

        monkeypatch.setattr("src.checkers.disk_check.check", lambda: mock_disk)
        monkeypatch.setattr("src.checkers.docker_check.check", lambda: mock_docker)
        monkeypatch.setattr("src.checkers.publisher_check.check", lambda: mock_publisher)
        monkeypatch.setattr("src.checkers.memory_check.check", lambda: mock_memory)
        monkeypatch.setattr("src.checkers.obsidian_check.check", lambda: mock_obsidian)
        monkeypatch.setattr("src.checkers.skills_check.check", lambda: mock_skills)
        monkeypatch.setattr("src.checkers.video_pipeline_check.check", lambda: mock_video)

        from src.cli import app

        result = runner.invoke(app, ["doctor"])
        data = json.loads(result.stdout)
        expected_checks = [
            "disk", "docker", "publisher", "memory", "obsidian",
            "skills", "video_pipeline",
        ]
        check_names = {c["name"] for c in data["checks"]}
        for check_name in expected_checks:
            assert check_name in check_names, f"Missing check: {check_name}"

    def test_doctor_safe_stderr_not_in_stdout(self, runner, monkeypatch):
        """Doctor only outputs JSON to stdout — stderr content doesn't leak to stdout."""
        mock_disk = {"severity": "ok", "disks": [], "critical": [], "warning": [], "summary": "Ok"}
        mock_docker = {"containers_running": 0, "containers_unhealthy": 0, "containers": [], "error": None}
        mock_publisher = {"status": "port_closed", "port_open": False}
        mock_memory = {"overall": "ok", "qdrant": {"accessible": False}, "akasha": {"container_found": False}}
        mock_obsidian = {"vault_found": False, "vault_path": "/nonexistent"}
        mock_skills = {"total": 0, "executable": 0, "doc_folder": 0, "doc_file": 0, "orphan_skills": [], "registry_missing_from_disk": [], "registry_available": False}
        mock_video = {"classification": "not_found", "confidence": "high", "signals": {}, "counts": {}, "evidence": [], "risks": []}

        monkeypatch.setattr("src.checkers.disk_check.check", lambda: mock_disk)
        monkeypatch.setattr("src.checkers.docker_check.check", lambda: mock_docker)
        monkeypatch.setattr("src.checkers.publisher_check.check", lambda: mock_publisher)
        monkeypatch.setattr("src.checkers.memory_check.check", lambda: mock_memory)
        monkeypatch.setattr("src.checkers.obsidian_check.check", lambda: mock_obsidian)
        monkeypatch.setattr("src.checkers.skills_check.check", lambda: mock_skills)
        monkeypatch.setattr("src.checkers.video_pipeline_check.check", lambda: mock_video)

        from src.cli import app

        result = runner.invoke(app, ["doctor"])
        # stdout should be valid JSON
        data = json.loads(result.stdout)
        assert isinstance(data, dict)
