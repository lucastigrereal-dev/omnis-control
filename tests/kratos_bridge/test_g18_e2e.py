"""W170 — G18 KRATOS Bridge E2E: full pipeline integration test."""
import pytest
from src.kratos_bridge.bridge import KratosBridge, BridgeConfig
from src.kratos_bridge.event_stream import KratosEventStream, OmnisEvent, EventType
from src.kratos_bridge.health_monitor import KratosHealthMonitor, HealthStatus
from src.kratos_bridge.models import KratosPayload, PayloadPriority, PayloadType
from src.kratos_bridge.permission_gate import KratosPermissionGate, Permission, PermissionRule
from src.kratos_bridge.queue_manager import PayloadQueueManager
from src.kratos_bridge.serializer import KratosSerializer
from src.kratos_bridge.snapshot import SnapshotBuilder
from src.kratos_bridge.view_router import KratosViewRouter


# ---------------------------------------------------------------------------
# Full pipeline: permission → bridge → event → snapshot
# ---------------------------------------------------------------------------

def test_full_pipeline_happy_path():
    gate = KratosPermissionGate()
    bridge = KratosBridge(BridgeConfig(dry_run=True))
    stream = KratosEventStream(dry_run=True)
    builder = SnapshotBuilder()

    # 1. Create payload
    payload = KratosPayload.wave_progress("W170", 170, 210)

    # 2. Permission check
    gr = gate.check(payload)
    assert gr.allowed

    # 3. Bridge send
    br = bridge.send(payload)
    assert br.ok
    assert br.routing.primary_path == "/progress"

    # 4. Emit event
    event = OmnisEvent.wave_completed("W170", 25)
    stream.emit(event)

    # 5. Build snapshot
    snap = builder.build(wave="W170", completed=170, tests_passed=500, tests_total=500)
    assert snap.wave_progress.pct == pytest.approx(80.95, abs=0.1)

    # All components wired correctly
    assert gate.stats()["allowed"] == 1
    assert bridge.stats()["ok"] == 1
    assert stream.stats()["total_events"] == 1
    assert len(builder.history()) == 1


def test_denied_payload_not_sent():
    gate = KratosPermissionGate(rules=[PermissionRule.deny("external")])
    bridge = KratosBridge(BridgeConfig(dry_run=True))
    payload = KratosPayload(source_module="external", payload_type=PayloadType.ALERT,
                             body={"message": "x"})

    gr = gate.check(payload)
    assert not gr.allowed
    # If denied, we should NOT call bridge.send
    assert bridge.stats()["total"] == 0


def test_queue_then_bridge_integration():
    queue = PayloadQueueManager()
    bridge = KratosBridge(BridgeConfig(dry_run=True))

    payloads = [
        KratosPayload.metric("wave_count", 170.0),
        KratosPayload.status_update("All good", {"status": "ok"}),
        KratosPayload.alert("Low disk", "check storage"),
    ]
    entries = queue.enqueue_many(payloads)
    assert queue.size() == 3

    # Pop and send
    results = []
    while queue.size() > 0:
        entry = queue.pop()
        br = bridge.send(entry.payload)
        if br.ok:
            queue.mark_delivered(entry.entry_id)
            results.append(br)
        else:
            queue.mark_failed(entry.entry_id, "bridge_error")

    assert len(results) == 3
    assert queue.stats()["delivered"] == 3
    assert queue.stats()["pending"] == 0


def test_health_monitor_integration():
    monitor = KratosHealthMonitor()
    bridge = KratosBridge(BridgeConfig(dry_run=True))

    monitor.check_component("bridge", latency_ms=50.0)
    monitor.check_component("router", latency_ms=20.0)
    hb = monitor.send_heartbeat()
    monitor.acknowledge_heartbeat(hb.beat_id)

    report = monitor.report()
    assert report.overall == HealthStatus.HEALTHY

    br = bridge.send_status("Health OK", {"status": report.overall.value})
    assert br.ok


def test_event_stream_subscription_integration():
    stream = KratosEventStream(dry_run=False)
    received = []
    stream.subscribe(lambda e: received.append(e.event_type), event_types=[EventType.WAVE_COMPLETED])

    stream.emit(OmnisEvent.wave_completed("W170", 25))
    stream.emit(OmnisEvent.metric_updated("tests", 250.0))

    assert EventType.WAVE_COMPLETED in received
    assert len(received) == 1  # only wave_completed subscribed


def test_serializer_strict_guards_bridge():
    serializer = KratosSerializer(strict=True)
    bridge = KratosBridge(BridgeConfig(dry_run=True, strict_validation=True))

    bad = KratosPayload(payload_type=PayloadType.METRIC, body={})
    env = serializer.serialize(bad)
    assert env is None

    result = bridge.send(bad)
    assert not result.ok
    assert result.rejection_reason == "validation_failed"


def test_view_router_routes_all_default_types():
    router = KratosViewRouter()
    expected = {
        PayloadType.STATUS_UPDATE: "/dashboard",
        PayloadType.ALERT: "/alerts",
        PayloadType.METRIC: "/metrics",
        PayloadType.WAVE_PROGRESS: "/progress",
        PayloadType.COMMAND_ECHO: "/commands",
        PayloadType.ERROR: "/errors",
        PayloadType.MISSION_RESULT: "/missions",
    }
    for ptype, path in expected.items():
        p = KratosPayload(payload_type=ptype)
        result = router.route(p)
        assert result.primary_path == path, f"{ptype} should route to {path}"


# ---------------------------------------------------------------------------
# Multi-module concurrent simulation
# ---------------------------------------------------------------------------

def test_multi_module_payload_storm():
    gate = KratosPermissionGate()
    bridge = KratosBridge(BridgeConfig(dry_run=True))

    modules = ["omnis", "aurora", "argos", "remote_control"]
    payloads = []
    for module in modules:
        payloads.append(KratosPayload(source_module=module, payload_type=PayloadType.STATUS_UPDATE, title=f"{module} OK"))
        payloads.append(KratosPayload.metric(f"{module}_latency", 50.0))

    for p in payloads:
        gr = gate.check(p)
        if gr.allowed:
            bridge.send(p)

    stats = bridge.stats()
    assert stats["total"] == len(payloads)
    assert stats["ok"] == len(payloads)


def test_snapshot_captures_bridge_state():
    bridge = KratosBridge(BridgeConfig(dry_run=True))
    builder = SnapshotBuilder()

    for i in range(5):
        bridge.send(KratosPayload.metric(f"metric_{i}", float(i)))

    snap = builder.build(
        wave="W170",
        completed=170,
        tests_passed=250,
        tests_total=250,
        active_modules=["kratos_bridge", "remote_control"],
        healthy=True,
    )
    assert snap.wave_progress.completed_waves == 170
    assert snap.test_suite.pass_rate == 100.0
    assert "kratos_bridge" in snap.system.active_modules
