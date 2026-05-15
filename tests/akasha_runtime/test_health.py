from src.akasha_runtime.models import AkashaConnectionConfig
from src.akasha_runtime.health import AkashaHealthChecker


class TestAkashaHealthChecker:
    def test_not_enabled_returns_disconnected(self):
        checker = AkashaHealthChecker()
        config = AkashaConnectionConfig(enabled=False)
        status = checker.check_connection(config)
        assert status.connected is False
        assert status.error_message == "akasha not enabled"

    def test_dry_run_mock_connected(self):
        checker = AkashaHealthChecker(dry_run=True)
        config = AkashaConnectionConfig(enabled=True, pool_size=5)
        status = checker.check_connection(config)
        assert status.connected is True
        assert status.latency_ms == 0.5
        assert status.pool_available == 5
        assert status.pool_total == 5

    def test_real_not_implemented(self):
        checker = AkashaHealthChecker(dry_run=False)
        config = AkashaConnectionConfig(enabled=True)
        status = checker.check_connection(config)
        assert status.connected is False
        assert "not implemented" in status.error_message

    def test_full_health_check_healthy_dry_run(self):
        checker = AkashaHealthChecker(dry_run=True)
        config = AkashaConnectionConfig(enabled=True, pool_size=10, timeout_seconds=5)
        result = checker.full_health_check(config)
        assert result.healthy is True
        assert result.checks["connectivity"] is True
        assert result.checks["pool_ok"] is True
        assert result.checks["latency_ok"] is True
        assert result.checks["dry_run_mode"] is True

    def test_full_health_check_disabled(self):
        checker = AkashaHealthChecker(dry_run=True)
        config = AkashaConnectionConfig(enabled=False)
        result = checker.full_health_check(config)
        assert result.healthy is False
        assert result.checks["connectivity"] is False
        assert result.errors == ["akasha not enabled"]

    def test_last_status_tracked(self):
        checker = AkashaHealthChecker(dry_run=True)
        config = AkashaConnectionConfig(enabled=True)
        checker.check_connection(config)
        assert checker.last_status is not None
        assert checker.last_status.connected is True

    def test_last_result_tracked(self):
        checker = AkashaHealthChecker(dry_run=True)
        config = AkashaConnectionConfig(enabled=True)
        checker.full_health_check(config)
        assert checker.last_result is not None
        assert checker.last_result.healthy is True

    def test_latency_exceeds_timeout_fails(self):
        checker = AkashaHealthChecker(dry_run=True)
        config = AkashaConnectionConfig(enabled=True, timeout_seconds=0)
        result = checker.full_health_check(config)
        assert result.checks["latency_ok"] is False
        assert result.healthy is False
