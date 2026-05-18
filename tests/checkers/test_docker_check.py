"""Tests for docker_check checker."""
from __future__ import annotations

import subprocess
import pytest


class TestDockerCheck:
    def test_check_returns_dict_with_expected_keys(self, monkeypatch):
        """Docker check returns dict with expected structure."""
        mock_output = type("_", (), {
            "returncode": 0,
            "stdout": "",
            "stderr": "",
        })()

        def _mock_run(*args, **kwargs):
            return mock_output

        monkeypatch.setattr("subprocess.run", _mock_run)

        from src.checkers.docker_check import check

        result = check()
        assert "containers_running" in result
        assert "containers_unhealthy" in result
        assert "containers" in result
        assert "error" in result

    def test_check_parses_healthy_container(self, monkeypatch):
        import json

        container = {
            "Names": "healthy-app",
            "Status": "Up 2 hours (healthy)",
            "Image": "nginx:latest",
            "Ports": "8080:80",
        }
        mock_output = type("_", (), {
            "returncode": 0,
            "stdout": json.dumps(container),
            "stderr": "",
        })()

        monkeypatch.setattr("subprocess.run", lambda *a, **kw: mock_output)

        from src.checkers.docker_check import check

        result = check()
        assert result["containers_running"] == 1
        assert result["containers_unhealthy"] == 0
        c = result["containers"][0]
        assert c["name"] == "healthy-app"
        assert c["unhealthy"] is False

    def test_check_detects_unhealthy_container(self, monkeypatch):
        import json

        container = {
            "Names": "sick-app",
            "Status": "Up 10 minutes (unhealthy)",
            "Image": "myapp:latest",
            "Ports": "",
        }
        mock_output = type("_", (), {
            "returncode": 0,
            "stdout": json.dumps(container),
            "stderr": "",
        })()

        monkeypatch.setattr("subprocess.run", lambda *a, **kw: mock_output)

        from src.checkers.docker_check import check

        result = check()
        assert result["containers_unhealthy"] == 1
        c = result["containers"][0]
        assert c["unhealthy"] is True

    def test_check_handles_docker_cli_not_found(self, monkeypatch):
        def _mock_run(*args, **kwargs):
            raise FileNotFoundError("docker")

        monkeypatch.setattr("subprocess.run", _mock_run)

        from src.checkers.docker_check import check

        result = check()
        assert "Docker" in result.get("error", "")

    def test_check_handles_timeout(self, monkeypatch):
        def _mock_run(*args, **kwargs):
            raise subprocess.TimeoutExpired(cmd="docker ps", timeout=10)

        monkeypatch.setattr("subprocess.run", _mock_run)

        from src.checkers.docker_check import check

        result = check()
        assert "timed out" in result.get("error", "").lower()

    def test_check_handles_docker_ps_failure(self, monkeypatch):
        mock_output = type("_", (), {
            "returncode": 1,
            "stdout": "",
            "stderr": "permission denied",
        })()

        monkeypatch.setattr("subprocess.run", lambda *a, **kw: mock_output)

        from src.checkers.docker_check import check

        result = check()
        assert result["error"] is not None
