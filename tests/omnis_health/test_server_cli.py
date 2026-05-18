"""Tests for health-server CLI commands."""
from __future__ import annotations

import json
import pytest
from typer.testing import CliRunner

from src.omnis_health.models import HealthStatus, CheckResult, HealthReport
from src.omnis_health.server import (
    ServerState,
    save_server_state,
    load_server_state,
    clear_server_state,
    is_server_alive,
    STATE_FILE,
)


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def _clean_state():
    clear_server_state()
    yield
    clear_server_state()


def _ok_report() -> HealthReport:
    return HealthReport(
        session_id="test",
        timestamp="2026-05-17T10:00:00Z",
        overall_status=HealthStatus.OK,
        checks=[CheckResult(name="disk", status=HealthStatus.OK, data={"free_gb": 100})],
    )


class TestHealthServerCLIStatus:
    def test_status_when_server_stopped(self, runner):
        from src.cli import app

        result = runner.invoke(app, ["health-server", "status"])
        assert result.exit_code == 0
        assert "parado" in result.stdout.lower() or "stopped" in result.stdout.lower()

    def test_status_handles_missing_state_file_gracefully(self, runner):
        clear_server_state()
        from src.cli import app

        result = runner.invoke(app, ["health-server", "status"])
        assert result.exit_code == 0


class TestHealthServerCLIStart:
    def test_start_creates_state_file(self, runner, monkeypatch, tmp_path):
        from src.omnis_health.server import HealthServer

        # Track which port was used
        started_ports = []

        class _FakeServer:
            def __init__(self, port=0, report_builder=None):
                self._port = port or 9876

            @property
            def port(self):
                return self._port

            def start(self):
                started_ports.append(self._port)
                return self._port

            def stop(self):
                pass

            def is_running(self):
                return True

        monkeypatch.setattr("src.omnis_health.server.HealthServer", _FakeServer)
        monkeypatch.setattr("src.omnis_health.server.is_server_alive", lambda: False)

        # Use a tmp_path for state
        state_path = str(tmp_path / "state.json")
        monkeypatch.setattr("src.omnis_health.server.STATE_FILE", state_path)

        from src.cli import app

        result = runner.invoke(app, ["health-server", "start"])
        assert result.exit_code == 0
        assert "9876" in result.stdout


class TestHealthServerCLIStop:
    def test_stop_when_already_stopped(self, runner, monkeypatch):
        monkeypatch.setattr("src.omnis_health.server.is_server_alive", lambda: False)

        from src.cli import app

        result = runner.invoke(app, ["health-server", "stop"])
        assert result.exit_code == 0


class TestServerStatePersistence:
    def test_save_and_load_round_trip(self, tmp_path, monkeypatch):
        state_path = str(tmp_path / "state.json")
        monkeypatch.setattr("src.omnis_health.server.STATE_FILE", state_path)

        state = ServerState(pid=12345, port=9876, started_at="2026-05-17T10:00:00Z")
        save_server_state(state)

        loaded = load_server_state()
        assert loaded is not None
        assert loaded.pid == 12345
        assert loaded.port == 9876

    def test_load_returns_none_when_no_file(self, tmp_path, monkeypatch):
        state_path = str(tmp_path / "nonexistent.json")
        monkeypatch.setattr("src.omnis_health.server.STATE_FILE", state_path)
        assert load_server_state() is None

    def test_clear_removes_file(self, tmp_path, monkeypatch):
        state_path = str(tmp_path / "state.json")
        monkeypatch.setattr("src.omnis_health.server.STATE_FILE", state_path)

        save_server_state(ServerState(pid=1, port=2))
        assert load_server_state() is not None
        clear_server_state()
        assert load_server_state() is None

    def test_is_server_alive_false_when_no_state(self, monkeypatch):
        monkeypatch.setattr("src.omnis_health.server.load_server_state", lambda: None)
        assert is_server_alive() is False
