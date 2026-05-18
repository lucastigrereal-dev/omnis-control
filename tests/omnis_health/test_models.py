"""Tests for unified health models."""
from __future__ import annotations

import json
import pytest

from src.omnis_health.models import HealthStatus, CheckResult, HealthReport


class TestHealthStatus:
    def test_enum_values(self):
        assert HealthStatus.OK == "ok"
        assert HealthStatus.WARNING == "warning"
        assert HealthStatus.CRITICAL == "critical"
        assert HealthStatus.UNKNOWN == "unknown"
        assert HealthStatus.ERROR == "error"

    def test_from_string(self):
        assert HealthStatus("ok") == HealthStatus.OK
        assert HealthStatus("warning") == HealthStatus.WARNING
        assert HealthStatus("critical") == HealthStatus.CRITICAL


class TestCheckResult:
    def test_create_with_minimal_fields(self):
        r = CheckResult(name="disk", status=HealthStatus.OK)
        assert r.name == "disk"
        assert r.status == HealthStatus.OK
        assert r.data == {}
        assert r.error is None
        assert r.duration_ms == 0

    def test_create_with_all_fields(self):
        r = CheckResult(
            name="docker",
            status=HealthStatus.WARNING,
            data={"containers_running": 3, "containers_unhealthy": 1},
            error=None,
            duration_ms=150,
            timestamp="2026-05-17T10:00:00Z",
        )
        assert r.name == "docker"
        assert r.status == HealthStatus.WARNING
        assert r.data["containers_running"] == 3

    def test_to_dict(self):
        r = CheckResult(name="disk", status=HealthStatus.OK, data={"free_gb": 100})
        d = r.to_dict()
        assert d["name"] == "disk"
        assert d["status"] == "ok"
        assert d["data"]["free_gb"] == 100
        assert d["error"] is None
        assert "duration_ms" in d

    def test_from_dict_minimal(self):
        d = {"name": "memory", "status": "ok"}
        r = CheckResult.from_dict(d)
        assert r.name == "memory"
        assert r.status == HealthStatus.OK
        assert r.data == {}

    def test_from_dict_full(self):
        d = {
            "name": "publisher",
            "status": "warning",
            "data": {"port_open": False},
            "error": "port closed",
            "duration_ms": 500,
            "timestamp": "2026-05-17T10:00:00Z",
        }
        r = CheckResult.from_dict(d)
        assert r.name == "publisher"
        assert r.status == HealthStatus.WARNING
        assert r.error == "port closed"
        assert r.duration_ms == 500

    def test_round_trip(self):
        r1 = CheckResult(
            name="obsidian",
            status=HealthStatus.WARNING,
            data={"md_file_count": 0},
            error="vault empty",
            duration_ms=42,
            timestamp="2026-05-17T10:00:00Z",
        )
        r2 = CheckResult.from_dict(r1.to_dict())
        assert r2.name == r1.name
        assert r2.status == r1.status
        assert r2.data == r1.data
        assert r2.error == r1.error
        assert r2.duration_ms == r1.duration_ms

    def test_json_serializable(self):
        r = CheckResult(name="test", status=HealthStatus.OK)
        json.dumps(r.to_dict())


class TestHealthReport:
    def test_create_empty(self):
        r = HealthReport(session_id="s1", timestamp="2026-05-17T10:00:00Z", overall_status=HealthStatus.OK)
        assert r.session_id == "s1"
        assert r.overall_status == HealthStatus.OK
        assert r.checks == []
        assert r.risks == []
        assert r.next_steps == []

    def test_create_with_checks(self):
        checks = [
            CheckResult(name="disk", status=HealthStatus.OK),
            CheckResult(name="docker", status=HealthStatus.WARNING, error="unhealthy container"),
        ]
        r = HealthReport(
            session_id="s1",
            timestamp="2026-05-17T10:00:00Z",
            overall_status=HealthStatus.WARNING,
            checks=checks,
            risks=["disk almost full"],
            next_steps=["clean temp files"],
        )
        assert len(r.checks) == 2
        assert r.risks == ["disk almost full"]
        assert r.healthy_count() == 1
        assert r.warning_count() == 1
        assert r.critical_count() == 0

    def test_to_dict(self):
        checks = [CheckResult(name="disk", status=HealthStatus.OK)]
        r = HealthReport(
            session_id="s1",
            timestamp="2026-05-17T10:00:00Z",
            overall_status=HealthStatus.OK,
            checks=checks,
            risks=[],
            next_steps=["step 1"],
        )
        d = r.to_dict()
        assert d["session_id"] == "s1"
        assert d["overall_status"] == "ok"
        assert len(d["checks"]) == 1
        assert d["checks"][0]["name"] == "disk"

    def test_from_dict_normalized(self):
        d = {
            "session_id": "s1",
            "timestamp": "2026-05-17T10:00:00Z",
            "overall_status": "warning",
            "checks": [
                {"name": "disk", "status": "ok", "data": {}},
                {"name": "docker", "status": "warning", "data": {}, "error": "unhealthy"},
            ],
            "risks": ["risk1"],
            "next_steps": ["step1"],
        }
        r = HealthReport.from_dict(d)
        assert r.session_id == "s1"
        assert r.overall_status == HealthStatus.WARNING
        assert len(r.checks) == 2
        assert r.checks[0].name == "disk"
        assert r.checks[1].name == "docker"

    def test_from_dict_legacy_dict_of_dicts(self):
        """Legacy doctor output format: checks is a dict of dicts."""
        d = {
            "session_id": "legacy-session",
            "timestamp": "2026-05-17T10:00:00Z",
            "overall_status": "ok",
            "checks": {
                "disk": {"severity": "ok", "disks": []},
                "docker": {"containers_running": 0},
                "publisher": {"error": "port closed"},
            },
            "risks": [],
            "next_steps": [],
        }
        r = HealthReport.from_dict(d)
        assert len(r.checks) == 3
        assert r.checks[0].name == "disk"
        assert r.checks[0].status == HealthStatus.OK
        assert r.checks[2].name == "publisher"
        assert r.checks[2].status == HealthStatus.ERROR

    def test_round_trip(self):
        checks = [
            CheckResult(name="disk", status=HealthStatus.OK, data={"free_gb": 100}),
            CheckResult(name="docker", status=HealthStatus.ERROR, error="docker not found"),
        ]
        r1 = HealthReport(
            session_id="s1",
            timestamp="2026-05-17T10:00:00Z",
            overall_status=HealthStatus.WARNING,
            checks=checks,
            risks=["risk1"],
            next_steps=["step1"],
        )
        r2 = HealthReport.from_dict(r1.to_dict())
        assert r2.session_id == r1.session_id
        assert r2.overall_status == r1.overall_status
        assert len(r2.checks) == 2
        assert r2.checks[0].name == "disk"
        assert r2.risks == r1.risks
        assert r2.next_steps == r1.next_steps

    def test_healthy_count(self):
        checks = [
            CheckResult(name="a", status=HealthStatus.OK),
            CheckResult(name="b", status=HealthStatus.OK),
            CheckResult(name="c", status=HealthStatus.WARNING),
            CheckResult(name="d", status=HealthStatus.CRITICAL),
            CheckResult(name="e", status=HealthStatus.ERROR),
        ]
        r = HealthReport(
            session_id="s1",
            timestamp="",
            overall_status=HealthStatus.CRITICAL,
            checks=checks,
        )
        assert r.healthy_count() == 2
        assert r.warning_count() == 1
        assert r.critical_count() == 2

    def test_json_serializable(self):
        checks = [CheckResult(name="disk", status=HealthStatus.OK)]
        r = HealthReport(
            session_id="s1",
            timestamp="2026-05-17T10:00:00Z",
            overall_status=HealthStatus.OK,
            checks=checks,
        )
        json.dumps(r.to_dict())

    def test_from_dict_legacy_with_no_checks(self):
        d = {
            "session_id": "s1",
            "timestamp": "",
            "overall_status": "unknown",
            "checks": {},
        }
        r = HealthReport.from_dict(d)
        assert r.checks == []
        assert r.overall_status == HealthStatus.UNKNOWN
