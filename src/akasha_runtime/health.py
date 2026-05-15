from src.akasha_runtime.models import (
    AkashaConnectionConfig,
    AkashaConnectionStatus,
    AkashaHealthResult,
)


class AkashaHealthChecker:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self._last_status: AkashaConnectionStatus | None = None
        self._last_result: AkashaHealthResult | None = None

    def check_connection(self, config: AkashaConnectionConfig) -> AkashaConnectionStatus:
        if not config.enabled:
            status = AkashaConnectionStatus(
                config_id=config.config_id,
                connected=False,
                error_message="akasha not enabled",
            )
            self._last_status = status
            return status

        if self.dry_run:
            status = AkashaConnectionStatus(
                config_id=config.config_id,
                connected=True,
                latency_ms=0.5,
                pool_available=config.pool_size,
                pool_total=config.pool_size,
            )
            self._last_status = status
            return status

        status = AkashaConnectionStatus(
            config_id=config.config_id,
            connected=False,
            error_message="real connection not implemented",
        )
        self._last_status = status
        return status

    def full_health_check(self, config: AkashaConnectionConfig) -> AkashaHealthResult:
        conn_status = self.check_connection(config)
        checks = {
            "connectivity": conn_status.connected,
            "pool_ok": conn_status.pool_available > 0,
            "latency_ok": conn_status.latency_ms < config.timeout_seconds * 1000,
        }
        errors = []
        if not conn_status.connected:
            errors.append(conn_status.error_message)
        if config.dry_run:
            checks["dry_run_mode"] = True
        healthy = all(checks.values())

        result = AkashaHealthResult(
            config_id=config.config_id,
            healthy=healthy,
            connection_status=conn_status,
            checks=checks,
            errors=errors,
        )
        self._last_result = result
        return result

    @property
    def last_status(self) -> AkashaConnectionStatus | None:
        return self._last_status

    @property
    def last_result(self) -> AkashaHealthResult | None:
        return self._last_result
