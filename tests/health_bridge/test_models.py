"""W197 — Tests for HealthStatus model."""
import json
import pytest
from src.health_bridge.models import (
    HealthCheck, HealthLevel, HealthStatus, _now_iso,
)


def test_health_check_factories():
    ok = HealthCheck.ok("test", "all good")
    assert ok.level == HealthLevel.OK
    assert ok.name == "test"
    assert ok.message == "all good"

    warn = HealthCheck.warn("disk", "80% full")
    assert warn.level == HealthLevel.WARN

    err = HealthCheck.error("db", "connection refused")
    assert err.level == HealthLevel.ERROR


def test_health_check_to_dict():
    c = HealthCheck.ok("cpu")
    d = c.to_dict()
    assert d["name"] == "cpu"
    assert d["level"] == "ok"
    assert "checked_at" in d


def test_health_status_from_checks_all_ok():
    checks = [HealthCheck.ok("a"), HealthCheck.ok("b")]
    s = HealthStatus.from_checks(checks)
    assert s.status == HealthLevel.OK


def test_health_status_from_checks_with_error():
    checks = [HealthCheck.ok("a"), HealthCheck.error("b", "fail")]
    s = HealthStatus.from_checks(checks)
    assert s.status == HealthLevel.ERROR


def test_health_status_from_checks_with_warn():
    checks = [HealthCheck.ok("a"), HealthCheck.warn("b", "warn")]
    s = HealthStatus.from_checks(checks)
    assert s.status == HealthLevel.WARN


def test_health_status_empty_checks():
    s = HealthStatus.from_checks([])
    assert s.status == HealthLevel.UNKNOWN


def test_health_status_to_dict():
    s = HealthStatus.from_checks([HealthCheck.ok("ok")])
    d = s.to_dict()
    assert d["status"] == "ok"
    assert len(d["checks"]) == 1
    assert d["source"] == "omnis-health-bridge"
