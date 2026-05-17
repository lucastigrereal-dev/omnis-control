"""W164 — Tests for KratosBridge E2E pipeline."""
import pytest
from src.kratos_bridge.bridge import KratosBridge, BridgeConfig, BridgeResult
from src.kratos_bridge.models import KratosPayload, PayloadPriority, PayloadType


def _bridge(**kwargs) -> KratosBridge:
    return KratosBridge(BridgeConfig(dry_run=True, **kwargs))


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_send_status_update_ok():
    b = _bridge()
    result = b.send(KratosPayload.status_update("Wave done", {"wave": "W164"}))
    assert result.ok
    assert result.stage == "complete"


def test_send_alert_ok():
    b = _bridge()
    result = b.send_alert("Fire!", "Something broke")
    assert result.ok


def test_send_metric_ok():
    b = _bridge()
    result = b.send_metric("tests", 185.0, "count")
    assert result.ok


def test_send_wave_progress_ok():
    b = _bridge()
    result = b.send_wave_progress("W164", 9, 10)
    assert result.ok


def test_send_status_shortcut_ok():
    b = _bridge()
    result = b.send_status("All systems go", {"uptime": "99.9%"})
    assert result.ok


# ---------------------------------------------------------------------------
# Validation integration
# ---------------------------------------------------------------------------

def test_invalid_metric_non_strict_still_ok():
    b = _bridge(strict_validation=False)
    p = KratosPayload(payload_type=PayloadType.METRIC, body={})  # missing value
    result = b.send(p)
    assert result.ok  # validation warning but dispatch proceeds


def test_invalid_payload_strict_rejected():
    b = _bridge(strict_validation=True)
    p = KratosPayload(payload_type=PayloadType.METRIC, body={})
    result = b.send(p)
    assert not result.ok
    assert result.rejection_reason == "validation_failed"
    assert result.stage == "serialize"


def test_validation_info_attached():
    b = _bridge()
    result = b.send(KratosPayload.status_update("OK", {}))
    assert result.validation is not None


# ---------------------------------------------------------------------------
# Routing integration
# ---------------------------------------------------------------------------

def test_routing_info_attached():
    b = _bridge()
    result = b.send(KratosPayload.alert("X", "Y"))
    assert result.routing is not None
    assert result.routing.primary_path == "/alerts"


def test_alert_routed_to_alerts_view():
    b = _bridge()
    result = b.send_alert("Test", "msg")
    assert result.routing.primary_path == "/alerts"


def test_metric_routed_to_metrics_view():
    b = _bridge()
    result = b.send_metric("count", 1.0)
    assert result.routing.primary_path == "/metrics"


# ---------------------------------------------------------------------------
# Dispatch integration
# ---------------------------------------------------------------------------

def test_dispatch_info_attached():
    b = _bridge()
    result = b.send(KratosPayload.status_update("X", {}))
    assert result.dispatch is not None
    assert result.dispatch.dry_run is True


def test_dry_run_marked():
    b = _bridge()
    result = b.send(KratosPayload.status_update("X", {}))
    assert result.dispatch.dry_run is True


# ---------------------------------------------------------------------------
# send_many
# ---------------------------------------------------------------------------

def test_send_many():
    b = _bridge()
    payloads = [
        KratosPayload.status_update("A", {}),
        KratosPayload.metric("b", 1.0),
        KratosPayload.alert("C", "msg"),
    ]
    results = b.send_many(payloads)
    assert len(results) == 3
    assert all(r.ok for r in results)


def test_send_many_partial_failure_strict():
    b = _bridge(strict_validation=True)
    good = KratosPayload.status_update("OK", {})
    bad = KratosPayload(payload_type=PayloadType.METRIC, body={})
    results = b.send_many([good, bad])
    ok_results = [r for r in results if r.ok]
    failed = [r for r in results if not r.ok]
    assert len(ok_results) == 1
    assert len(failed) == 1


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def test_stats_empty():
    b = _bridge()
    s = b.stats()
    assert s["total"] == 0
    assert s["ok"] == 0


def test_stats_after_sends():
    b = _bridge()
    b.send(KratosPayload.status_update("A", {}))
    b.send(KratosPayload.metric("b", 1.0))
    s = b.stats()
    assert s["total"] == 2
    assert s["ok"] == 2
    assert s["rejected"] == 0


def test_stats_rejection_counted():
    b = _bridge(strict_validation=True)
    b.send(KratosPayload(payload_type=PayloadType.METRIC, body={}))
    s = b.stats()
    assert s["rejected"] == 1


# ---------------------------------------------------------------------------
# BridgeResult
# ---------------------------------------------------------------------------

def test_bridge_result_to_dict():
    b = _bridge()
    result = b.send(KratosPayload.status_update("OK", {}))
    d = result.to_dict()
    assert "result_id" in d
    assert d["ok"] is True
    assert d["stage"] == "complete"


def test_results_list():
    b = _bridge()
    b.send(KratosPayload.status_update("A", {}))
    b.send(KratosPayload.status_update("B", {}))
    assert len(b.results()) == 2


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def test_config_to_dict():
    cfg = BridgeConfig(dry_run=True, strict_validation=False, fallback_view="/custom")
    d = cfg.to_dict()
    assert d["dry_run"] is True
    assert d["fallback_view"] == "/custom"
