"""Tests for disk_check checker."""
from __future__ import annotations

import pytest


class TestDiskCheck:
    def test_check_returns_dict_with_expected_keys(self, monkeypatch):
        """Disk check returns dict with severity, disks, critical, warning, summary."""
        mock_partitions = [
            type("_", (), {"mountpoint": "C:\\", "device": "C:"})(),
        ]

        def _mock_disk_partitions():
            return mock_partitions

        mock_usage = type("_", (), {
            "total": 500 * 1024**3,
            "used": 200 * 1024**3,
            "free": 300 * 1024**3,
            "percent": 40.0,
        })()

        def _mock_disk_usage(path):
            return mock_usage

        monkeypatch.setattr("psutil.disk_partitions", _mock_disk_partitions)
        monkeypatch.setattr("psutil.disk_usage", _mock_disk_usage)

        from src.checkers.disk_check import check

        result = check()
        assert "severity" in result
        assert "disks" in result
        assert "critical" in result
        assert "warning" in result
        assert "summary" in result

    def test_check_ok_when_free_above_warning(self, monkeypatch):
        mock_partitions = [
            type("_", (), {"mountpoint": "C:\\", "device": "C:"})(),
        ]
        mock_usage = type("_", (), {
            "total": 500 * 1024**3,
            "used": 200 * 1024**3,
            "free": 300 * 1024**3,
            "percent": 40.0,
        })()

        monkeypatch.setattr("psutil.disk_partitions", lambda: mock_partitions)
        monkeypatch.setattr("psutil.disk_usage", lambda p: mock_usage)

        from src.checkers.disk_check import check

        result = check()
        assert result["severity"] == "ok"
        assert result["critical"] == []
        assert result["warning"] == []

    def test_check_critical_when_free_below_10(self, monkeypatch):
        mock_partitions = [
            type("_", (), {"mountpoint": "C:\\", "device": "C:"})(),
        ]
        mock_usage = type("_", (), {
            "total": 500 * 1024**3,
            "used": 475 * 1024**3,
            "free": 25 * 1024**3,
            "percent": 95.0,
        })()

        monkeypatch.setattr("psutil.disk_partitions", lambda: mock_partitions)
        monkeypatch.setattr("psutil.disk_usage", lambda p: mock_usage)

        from src.checkers.disk_check import check

        result = check()
        assert result["severity"] == "critical"
        assert len(result["critical"]) == 1

    def test_check_warning_when_free_between_10_and_20(self, monkeypatch):
        mock_partitions = [
            type("_", (), {"mountpoint": "C:\\", "device": "C:"})(),
        ]
        mock_usage = type("_", (), {
            "total": 500 * 1024**3,
            "used": 425 * 1024**3,
            "free": 75 * 1024**3,
            "percent": 85.0,
        })()

        monkeypatch.setattr("psutil.disk_partitions", lambda: mock_partitions)
        monkeypatch.setattr("psutil.disk_usage", lambda p: mock_usage)

        from src.checkers.disk_check import check

        result = check()
        assert result["severity"] == "warning"
        assert len(result["warning"]) == 1

    def test_check_skips_permission_errors(self, monkeypatch):
        mock_partitions = [
            type("_", (), {"mountpoint": "C:\\", "device": "C:"})(),
        ]

        def _fail_usage(path):
            raise PermissionError("acesso negado")

        monkeypatch.setattr("psutil.disk_partitions", lambda: mock_partitions)
        monkeypatch.setattr("psutil.disk_usage", _fail_usage)

        from src.checkers.disk_check import check

        result = check()
        assert result["severity"] == "ok"
        assert result["disks"] == []

    def test_disks_have_expected_fields(self, monkeypatch):
        mock_partitions = [
            type("_", (), {"mountpoint": "C:\\", "device": "C:"})(),
        ]
        mock_usage = type("_", (), {
            "total": 500 * 1024**3,
            "used": 200 * 1024**3,
            "free": 300 * 1024**3,
            "percent": 40.0,
        })()

        monkeypatch.setattr("psutil.disk_partitions", lambda: mock_partitions)
        monkeypatch.setattr("psutil.disk_usage", lambda p: mock_usage)

        from src.checkers.disk_check import check

        result = check()
        disk = result["disks"][0]
        assert "mount" in disk
        assert "total_gb" in disk
        assert "used_gb" in disk
        assert "free_gb" in disk
        assert "percent_free" in disk
        assert "percent_used" in disk
