"""W166 — Tests for KratosHealthMonitor."""
import pytest
from src.kratos_bridge.health_monitor import (
    HealthCheck,
    HealthStatus,
    Heartbeat,
    KratosHealthMonitor,
)


# ---------------------------------------------------------------------------
# HealthCheck
# ---------------------------------------------------------------------------

def test_check_ok_factory():
    c = HealthCheck.ok("dispatcher", latency_ms=50.0)
    assert c.status == HealthStatus.HEALTHY
    assert c.latency_ms == 50.0


def test_check_degraded_factory():
    c = HealthCheck.degraded("dispatcher", "slow")
    assert c.status == HealthStatus.DEGRADED


def test_check_unhealthy_factory():
    c = HealthCheck.unhealthy("dispatcher", "timeout")
    assert c.status == HealthStatus.UNHEALTHY


def test_check_round_trip():
    c = HealthCheck.ok("c1", 100.0)
    c2 = HealthCheck.from_dict(c.to_dict())
    assert c2.component == "c1"
    assert c2.status == HealthStatus.HEALTHY
    assert c2.latency_ms == 100.0


# ---------------------------------------------------------------------------
# Heartbeat
# ---------------------------------------------------------------------------

def test_heartbeat_defaults():
    hb = Heartbeat(sequence=1)
    assert not hb.acknowledged
    assert hb.ack_at == ""


def test_heartbeat_round_trip():
    hb = Heartbeat(sequence=5, acknowledged=True, ack_at="2026-01-01")
    hb2 = Heartbeat.from_dict(hb.to_dict())
    assert hb2.sequence == 5
    assert hb2.acknowledged is True


# ---------------------------------------------------------------------------
# check_component
# ---------------------------------------------------------------------------

def test_low_latency_healthy():
    m = KratosHealthMonitor()
    c = m.check_component("bridge", latency_ms=100.0)
    assert c.status == HealthStatus.HEALTHY


def test_medium_latency_degraded():
    m = KratosHealthMonitor()
    c = m.check_component("bridge", latency_ms=600.0)
    assert c.status == HealthStatus.DEGRADED


def test_high_latency_unhealthy():
    m = KratosHealthMonitor()
    c = m.check_component("bridge", latency_ms=2100.0)
    assert c.status == HealthStatus.UNHEALTHY


def test_record_check_manual():
    m = KratosHealthMonitor()
    c = HealthCheck.ok("router", 10.0)
    m.record_check(c)
    assert m.latest_check("router").status == HealthStatus.HEALTHY


# ---------------------------------------------------------------------------
# Heartbeat
# ---------------------------------------------------------------------------

def test_send_heartbeat_increments_sequence():
    m = KratosHealthMonitor()
    hb1 = m.send_heartbeat()
    hb2 = m.send_heartbeat()
    assert hb1.sequence == 1
    assert hb2.sequence == 2


def test_acknowledge_heartbeat():
    m = KratosHealthMonitor()
    hb = m.send_heartbeat()
    assert m.acknowledge_heartbeat(hb.beat_id)
    assert hb.acknowledged


def test_acknowledge_missing_returns_false():
    m = KratosHealthMonitor()
    assert not m.acknowledge_heartbeat("nonexistent")


def test_missed_beats_count():
    m = KratosHealthMonitor()
    hb1 = m.send_heartbeat()
    hb2 = m.send_heartbeat()
    m.acknowledge_heartbeat(hb1.beat_id)
    assert m.missed_beats() == 1


def test_no_missed_when_all_acked():
    m = KratosHealthMonitor()
    hb = m.send_heartbeat()
    m.acknowledge_heartbeat(hb.beat_id)
    assert m.missed_beats() == 0


# ---------------------------------------------------------------------------
# Overall health report
# ---------------------------------------------------------------------------

def test_all_healthy():
    m = KratosHealthMonitor()
    m.check_component("a", 10.0)
    m.check_component("b", 20.0)
    report = m.report()
    assert report.overall == HealthStatus.HEALTHY


def test_one_degraded_makes_overall_degraded():
    m = KratosHealthMonitor()
    m.check_component("a", 10.0)
    m.check_component("b", 600.0)
    report = m.report()
    assert report.overall == HealthStatus.DEGRADED


def test_one_unhealthy_makes_overall_unhealthy():
    m = KratosHealthMonitor()
    m.check_component("a", 10.0)
    m.check_component("b", 3000.0)
    report = m.report()
    assert report.overall == HealthStatus.UNHEALTHY


def test_missed_beats_degraded():
    m = KratosHealthMonitor()
    m.check_component("a", 10.0)
    m.send_heartbeat()
    m.send_heartbeat()
    # 2 unacked = DEGRADED threshold
    report = m.report()
    assert report.overall in (HealthStatus.DEGRADED, HealthStatus.UNHEALTHY)


def test_missed_beats_unhealthy():
    m = KratosHealthMonitor()
    m.check_component("a", 10.0)
    for _ in range(5):
        m.send_heartbeat()
    report = m.report()
    assert report.overall == HealthStatus.UNHEALTHY


def test_no_checks_unknown():
    m = KratosHealthMonitor()
    report = m.report()
    assert report.overall == HealthStatus.UNKNOWN


def test_is_healthy():
    m = KratosHealthMonitor()
    m.check_component("a", 10.0)
    assert m.is_healthy()


def test_is_not_healthy():
    m = KratosHealthMonitor()
    m.check_component("a", 3000.0)
    assert not m.is_healthy()


# ---------------------------------------------------------------------------
# Latest check
# ---------------------------------------------------------------------------

def test_latest_check_returns_last():
    m = KratosHealthMonitor()
    m.check_component("a", 10.0)
    m.check_component("a", 3000.0)
    latest = m.latest_check("a")
    assert latest.status == HealthStatus.UNHEALTHY


def test_latest_check_missing():
    m = KratosHealthMonitor()
    assert m.latest_check("nonexistent") is None


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def test_report_to_dict():
    m = KratosHealthMonitor()
    m.check_component("a", 50.0)
    r = m.report()
    d = r.to_dict()
    assert "overall" in d
    assert "checks" in d
    assert len(d["checks"]) == 1


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def test_stats():
    m = KratosHealthMonitor()
    m.check_component("a", 10.0)
    m.check_component("b", 20.0)
    hb = m.send_heartbeat()
    m.acknowledge_heartbeat(hb.beat_id)
    m.send_heartbeat()  # missed
    s = m.stats()
    assert "a" in s["components"]
    assert s["total_heartbeats"] == 2
    assert s["acknowledged"] == 1
    assert s["missed"] == 1
