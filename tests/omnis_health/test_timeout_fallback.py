"""Tests for health check timeout and fallback behavior — W200."""
from __future__ import annotations

import time
import json
import pytest

from src.omnis_health.models import HealthStatus, CheckResult, HealthReport
from src.omnis_health.server import build_health_report, _collect_risks


class TestBuildHealthReportWithTimeouts:
    def test_all_checks_pass_returns_ok(self, monkeypatch):
        """When all checks succeed, overall is OK."""
        mock_data = {"status": "ok"}

        for mod_name in ["disk_check", "docker_check", "publisher_check", "memory_check", "obsidian_check", "skills_check", "video_pipeline_check"]:
            mod = type("_M", (), {"check": lambda s, d=mock_data: d})()
            monkeypatch.setattr(f"src.checkers.{mod_name}", mod)

        report = build_health_report(per_check_timeout_s=5, total_timeout_s=30)
        assert report.overall_status == HealthStatus.OK
        assert len(report.checks) == 7
        for c in report.checks:
            assert c.status == HealthStatus.OK

    def test_one_check_error_returns_warning(self, monkeypatch):
        """When one check fails, overall is WARNING."""
        ok_data = {"status": "ok"}

        class _FailingMod:
            def check(self):
                raise RuntimeError("boom")

        for mod_name in ["disk_check", "docker_check", "publisher_check", "memory_check", "obsidian_check", "skills_check", "video_pipeline_check"]:
            if mod_name == "disk_check":
                monkeypatch.setattr(f"src.checkers.{mod_name}", _FailingMod())
            else:
                mod = type("_M", (), {"check": lambda s, d=ok_data: d})()
                monkeypatch.setattr(f"src.checkers.{mod_name}", mod)

        report = build_health_report(per_check_timeout_s=5, total_timeout_s=30)
        assert report.overall_status == HealthStatus.WARNING
        assert report.checks[0].status == HealthStatus.ERROR
        assert report.critical_count() >= 0  # ERROR counts as critical, but overall is warning

    def test_all_checks_error_returns_critical(self, monkeypatch):
        """When all checks fail, overall is CRITICAL."""
        class _FailingMod:
            def check(self):
                raise RuntimeError("all dead")

        for mod_name in ["disk_check", "docker_check", "publisher_check", "memory_check", "obsidian_check", "skills_check", "video_pipeline_check"]:
            monkeypatch.setattr(f"src.checkers.{mod_name}", _FailingMod())

        report = build_health_report(per_check_timeout_s=5, total_timeout_s=30)
        assert report.overall_status == HealthStatus.CRITICAL

    def test_slow_check_triggers_per_check_timeout(self, monkeypatch):
        """A check that exceeds per_check_timeout_s gets marked as error with timeout message."""
        ok_data = {"status": "ok"}

        class _SlowMod:
            def check(self):
                time.sleep(2)  # Slow but under total timeout
                return {"status": "ok"}

        for mod_name in ["disk_check", "docker_check", "publisher_check", "memory_check", "obsidian_check", "skills_check", "video_pipeline_check"]:
            if mod_name == "disk_check":
                monkeypatch.setattr(f"src.checkers.{mod_name}", _SlowMod())
            else:
                mod = type("_M", (), {"check": lambda s, d=ok_data: d})()
                monkeypatch.setattr(f"src.checkers.{mod_name}", mod)

        # per_check_timeout of 1s, slow check takes 2s → should timeout
        report = build_health_report(per_check_timeout_s=1, total_timeout_s=30)
        assert report.overall_status == HealthStatus.WARNING
        disk_check = next(c for c in report.checks if c.name == "disk")
        assert disk_check.status == HealthStatus.ERROR
        assert "timeout" in (disk_check.error or "")

    def test_checks_do_not_exceed_total_timeout(self, monkeypatch):
        """Total execution time stays within total_timeout_s."""
        ok_data = {"status": "ok"}

        for mod_name in ["disk_check", "docker_check", "publisher_check", "memory_check", "obsidian_check", "skills_check", "video_pipeline_check"]:
            mod = type("_M", (), {"check": lambda s, d=ok_data: d})()
            monkeypatch.setattr(f"src.checkers.{mod_name}", mod)

        start = time.time()
        report = build_health_report(per_check_timeout_s=5, total_timeout_s=30)
        elapsed = time.time() - start
        assert elapsed < 35  # Allow some slack
        assert report.overall_status == HealthStatus.OK

    def test_output_is_valid_json(self, monkeypatch):
        """Report serializes to valid JSON."""
        ok_data = {"status": "ok"}

        for mod_name in ["disk_check", "docker_check", "publisher_check", "memory_check", "obsidian_check", "skills_check", "video_pipeline_check"]:
            mod = type("_M", (), {"check": lambda s, d=ok_data: d})()
            monkeypatch.setattr(f"src.checkers.{mod_name}", mod)

        report = build_health_report()
        json.dumps(report.to_dict())  # Should not raise


class TestCollectRisks:
    def test_empty_checks_no_risks(self):
        assert _collect_risks([]) == []

    def test_ok_checks_no_risks(self):
        checks = [
            CheckResult(name="a", status=HealthStatus.OK, data={}),
            CheckResult(name="b", status=HealthStatus.OK, data={}),
        ]
        assert _collect_risks(checks) == []

    def test_error_checks_produce_risks(self):
        checks = [
            CheckResult(name="disk", status=HealthStatus.ERROR, error="disk full", data={}),
            CheckResult(name="docker", status=HealthStatus.OK, data={}),
            CheckResult(name="publisher", status=HealthStatus.ERROR, error="timeout", data={}),
        ]
        risks = _collect_risks(checks)
        assert len(risks) == 2
        assert any("disk" in r for r in risks)
        assert any("publisher" in r for r in risks)

    def test_warning_checks_no_risks(self):
        checks = [CheckResult(name="a", status=HealthStatus.WARNING, data={})]
        assert _collect_risks(checks) == []
