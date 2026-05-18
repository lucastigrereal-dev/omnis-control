"""W198-200 — Tests for health HTTP server."""
import json
import pytest
from src.health_bridge.server import build_basic_checks, HealthCheck, HealthLevel


def test_build_basic_checks_returns_list():
    checks = build_basic_checks()
    assert isinstance(checks, list)
    assert len(checks) >= 1  # at least process check
    assert all(isinstance(c, HealthCheck) for c in checks)


def test_process_check_is_ok():
    checks = build_basic_checks()
    process = [c for c in checks if c.name == "process"]
    assert len(process) == 1
    assert process[0].level == HealthLevel.OK
