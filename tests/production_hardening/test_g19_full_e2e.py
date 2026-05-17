"""W180 — G19 Full Production Hardening E2E (all modules integrated)."""
import pytest
from src.production_hardening.circuit_breaker import CircuitBreaker, CircuitConfig
from src.production_hardening.config_validator import ConfigSchema, ConfigValidator, FieldSchema, FieldType
from src.production_hardening.dependency_checker import DependencyChecker, ModuleDescriptor
from src.production_hardening.health_registry import CheckStatus, HealthCheckRegistry
from src.production_hardening.metrics_collector import MetricsCollector, MetricType
from src.production_hardening.retry_manager import RetryConfig, RetryManager
from src.production_hardening.shutdown_manager import ShutdownManager, ShutdownModule, ShutdownPhase
from src.production_hardening.timeout_guard import TimeoutConfig, TimeoutGuard


# ---------------------------------------------------------------------------
# Full startup simulation
# ---------------------------------------------------------------------------

def test_startup_validates_deps_and_configs():
    """Simulate OMNIS startup: check deps → validate config → register health checks."""
    # 1. Dependency check
    checker = DependencyChecker()
    checker.register_many([
        ModuleDescriptor("core", version="1.0.0"),
        ModuleDescriptor("kratos_bridge", version="0.1.0", requires=["core"]),
        ModuleDescriptor("remote_control", version="0.1.0", requires=["core"]),
        ModuleDescriptor("production_hardening", version="0.1.0", requires=["core", "kratos_bridge"]),
    ])
    dep_report = checker.check()
    assert dep_report.ok
    assert "core" in dep_report.load_order

    # 2. Config validation
    schema = ConfigSchema("omnis_core")
    schema.add_field(FieldSchema("dry_run", FieldType.BOOL))
    schema.add_field(FieldSchema("max_workers", FieldType.INT, min_val=1, max_val=32))
    schema.add_field(FieldSchema("log_level", FieldType.STRING, required=False, default="INFO"))

    validator = ConfigValidator(schema)
    config = {"dry_run": True, "max_workers": 4}
    result = validator.validate(config)
    assert result.ok
    assert result.applied["log_level"] == "INFO"  # default applied

    # 3. Health checks
    registry = HealthCheckRegistry()
    registry.register_fn("deps_ok", lambda: dep_report.ok, module="startup", critical=True)
    registry.register_fn("config_valid", lambda: result.ok, module="startup", critical=True)
    health = registry.run()
    assert health.overall == CheckStatus.PASS


def test_runtime_metrics_and_circuit_breaker():
    """Simulate runtime: metrics recorded, circuit breaker protects service."""
    metrics = MetricsCollector(module="remote_control")
    cb = CircuitBreaker("webhook", CircuitConfig(failure_threshold=3))
    retry = RetryManager(RetryConfig.fast())

    # Simulate 5 successful calls
    for _ in range(5):
        result = cb.call(lambda: "ok")
        if result.ok:
            metrics.increment("webhook.success")
            metrics.time_ms("webhook.latency", 25.0)

    snap = metrics.snapshot()
    assert snap["counters"]["webhook.success"] == 5
    assert cb.is_closed()

    # One failure
    cb.call(lambda: (_ for _ in ()).throw(RuntimeError("down")))
    metrics.increment("webhook.error")

    assert metrics.counter_value("webhook.error") == 1
    assert cb.is_closed()  # threshold=3, only 1 failure


def test_timeout_and_retry_with_metrics():
    """Timeout guard + retry: track attempts in metrics."""
    metrics = MetricsCollector(module="kratos_bridge")
    guard = TimeoutGuard(TimeoutConfig(dry_run=True))
    retry = RetryManager(RetryConfig(max_attempts=3, dry_run=True, jitter=False))

    calls = [0]

    def flaky():
        calls[0] += 1
        if calls[0] < 3:
            raise RuntimeError("flaky")
        return "ok"

    result = retry.execute(flaky)
    metrics.gauge("retry.attempts", result.total_attempts)
    metrics.gauge("retry.ok", 1.0 if result.ok else 0.0)

    assert result.ok
    assert metrics.summary("retry.attempts").last_val == 3


def test_graceful_shutdown_sequence():
    """Shutdown in phase order: edge → bridge → core."""
    mgr = ShutdownManager(dry_run=True)
    order = []

    mgr.register(ShutdownModule(name="core", phase=0))
    mgr.register(ShutdownModule(name="kratos_bridge", phase=5))
    mgr.register(ShutdownModule(name="remote_control", phase=5))
    mgr.register(ShutdownModule(name="health_monitor", phase=10))

    report = mgr.shutdown()
    assert report.ok
    names = [r.name for r in report.results]
    assert names.index("health_monitor") < names.index("core")
    assert names.index("kratos_bridge") < names.index("core")
    assert mgr.phase == ShutdownPhase.STOPPED


def test_health_registry_gates_shutdown():
    """Health check must pass before shutdown proceeds."""
    registry = HealthCheckRegistry()
    mgr = ShutdownManager(dry_run=True)
    mgr.register(ShutdownModule(name="bridge", phase=5))
    mgr.register(ShutdownModule(name="core", phase=0))

    registry.register_fn("system_ok", lambda: True, critical=True)
    health = registry.run()

    if health.overall == CheckStatus.PASS:
        report = mgr.shutdown()
        assert report.ok


def test_config_invalid_blocks_startup():
    """Invalid config should prevent module startup."""
    schema = ConfigSchema("gate")
    schema.add_field(FieldSchema("timeout", FieldType.INT, min_val=1, max_val=300))
    validator = ConfigValidator(schema)

    bad = {"timeout": 999}
    result = validator.validate(bad)
    assert not result.ok
    # Module should not start
    assert len(result.errors) > 0


def test_full_resilience_snapshot():
    """Capture a snapshot of all production hardening stats."""
    cb = CircuitBreaker("main", CircuitConfig(failure_threshold=5))
    guard = TimeoutGuard(TimeoutConfig(dry_run=True))
    retry = RetryManager(RetryConfig.fast())
    metrics = MetricsCollector("prod")

    # Simulate load
    for _ in range(3):
        r = cb.call(lambda: "ok")
        if r.ok:
            metrics.increment("calls.ok")

    guard.execute(lambda: "fast")
    metrics.gauge("guard.timeouts", guard.stats()["timed_out"])

    retry.execute(lambda: "done")
    metrics.gauge("retry.total", retry.stats()["total_executions"])

    snap = metrics.snapshot()
    assert snap["counters"]["calls.ok"] == 3
    assert snap["summaries"]["guard.timeouts"]["last"] == 0
    assert snap["summaries"]["retry.total"]["last"] == 1
