"""Tests for minimal HTTP health server."""
from __future__ import annotations

import json
import pytest
import urllib.request
import urllib.error

from src.omnis_health.models import HealthStatus, CheckResult, HealthReport
from src.omnis_health.server import HealthServer, _pick_free_port


def _ok_report() -> HealthReport:
    return HealthReport(
        session_id="test",
        timestamp="2026-05-17T10:00:00Z",
        overall_status=HealthStatus.OK,
        checks=[CheckResult(name="disk", status=HealthStatus.OK, data={"free_gb": 100})],
    )


def _critical_report() -> HealthReport:
    return HealthReport(
        session_id="test",
        timestamp="2026-05-17T10:00:00Z",
        overall_status=HealthStatus.CRITICAL,
        checks=[CheckResult(name="disk", status=HealthStatus.ERROR, error="disk full", data={})],
    )


def _warning_report() -> HealthReport:
    return HealthReport(
        session_id="test",
        timestamp="2026-05-17T10:00:00Z",
        overall_status=HealthStatus.WARNING,
        checks=[CheckResult(name="disk", status=HealthStatus.WARNING, data={"free_gb": 15})],
    )


class TestPickFreePort:
    def test_returns_valid_port(self):
        port = _pick_free_port()
        assert 1024 <= port <= 65535

    def test_returns_different_ports(self):
        p1 = _pick_free_port()
        p2 = _pick_free_port()
        assert p1 != p2


class TestHealthServer:
    def test_start_stop(self):
        server = HealthServer(port=0, report_builder=_ok_report)
        port = server.start()
        assert port > 0
        assert server.is_running()
        server.stop()
        assert not server.is_running()

    def test_url(self):
        server = HealthServer(port=9876, report_builder=_ok_report)
        assert "9876" in server.url

    def test_get_health_returns_200_and_json(self):
        server = HealthServer(port=0, report_builder=_ok_report)
        port = server.start()
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{port}/health")
            resp = urllib.request.urlopen(req, timeout=5)
            assert resp.status == 200
            assert resp.headers.get("Content-Type") == "application/json"
            data = json.loads(resp.read())
            assert data["overall_status"] == "ok"
            assert len(data["checks"]) == 1
            assert "disk" in data["checks"]
        finally:
            server.stop()

    def test_get_health_returns_503_on_critical(self):
        server = HealthServer(port=0, report_builder=_critical_report)
        port = server.start()
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{port}/health")
            try:
                urllib.request.urlopen(req, timeout=5)
                assert False, "Expected HTTPError"
            except urllib.error.HTTPError as e:
                assert e.code == 503
                data = json.loads(e.read())
                assert data["overall_status"] == "critical"
        finally:
            server.stop()

    def test_get_health_warning_returns_200(self):
        server = HealthServer(port=0, report_builder=_warning_report)
        port = server.start()
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{port}/health")
            resp = urllib.request.urlopen(req, timeout=5)
            assert resp.status == 200
            data = json.loads(resp.read())
            assert data["overall_status"] == "warning"
        finally:
            server.stop()

    def test_non_health_path_returns_404(self):
        server = HealthServer(port=0, report_builder=_ok_report)
        port = server.start()
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{port}/other")
            try:
                urllib.request.urlopen(req, timeout=5)
                assert False, "Expected HTTPError"
            except urllib.error.HTTPError as e:
                assert e.code == 404
        finally:
            server.stop()

    def test_port_auto_assign_when_zero(self):
        server = HealthServer(port=0, report_builder=_ok_report)
        port = server.start()
        try:
            assert port != 0
            assert server.port == port
        finally:
            server.stop()

    def test_explicit_port(self):
        free_port = _pick_free_port()
        server = HealthServer(port=free_port, report_builder=_ok_report)
        port = server.start()
        try:
            assert port == free_port
        finally:
            server.stop()

    def test_stop_idempotent(self):
        server = HealthServer(port=0, report_builder=_ok_report)
        server.start()
        server.stop()
        server.stop()  # Should not raise

    def test_is_running_false_before_start(self):
        server = HealthServer(port=0, report_builder=_ok_report)
        assert not server.is_running()

    def test_multiple_servers_different_ports(self):
        s1 = HealthServer(port=0, report_builder=_ok_report)
        s2 = HealthServer(port=0, report_builder=_ok_report)
        p1 = s1.start()
        p2 = s2.start()
        try:
            assert p1 != p2
        finally:
            s1.stop()
            s2.stop()
