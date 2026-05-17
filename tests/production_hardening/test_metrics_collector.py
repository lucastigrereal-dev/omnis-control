"""W176 — Tests for MetricsCollector."""
import pytest
from src.production_hardening.metrics_collector import (
    MetricPoint,
    MetricSummary,
    MetricType,
    MetricsCollector,
)


def _col(module: str = "test") -> MetricsCollector:
    return MetricsCollector(module=module)


# ---------------------------------------------------------------------------
# MetricPoint
# ---------------------------------------------------------------------------

def test_point_defaults():
    p = MetricPoint(name="latency", value=10.5)
    assert p.metric_type == MetricType.GAUGE
    assert p.tags == {}


def test_point_round_trip():
    p = MetricPoint(name="reqs", value=5.0, metric_type=MetricType.COUNTER, tags={"env": "test"})
    p2 = MetricPoint.from_dict(p.to_dict())
    assert p2.name == "reqs"
    assert p2.metric_type == MetricType.COUNTER
    assert p2.tags == {"env": "test"}


# ---------------------------------------------------------------------------
# MetricSummary
# ---------------------------------------------------------------------------

def test_summary_empty():
    s = MetricSummary("x")
    assert s.count == 0
    assert s.avg == 0.0


def test_summary_update():
    s = MetricSummary("x")
    s.update(10.0)
    s.update(20.0)
    assert s.count == 2
    assert s.avg == 15.0
    assert s.min_val == 10.0
    assert s.max_val == 20.0


def test_summary_to_dict():
    s = MetricSummary("latency")
    s.update(5.0)
    d = s.to_dict()
    assert d["count"] == 1
    assert d["avg"] == 5.0
    assert d["min"] == 5.0
    assert d["max"] == 5.0


def test_summary_to_dict_empty():
    s = MetricSummary("x")
    d = s.to_dict()
    assert d["min"] == 0.0
    assert d["max"] == 0.0


# ---------------------------------------------------------------------------
# record
# ---------------------------------------------------------------------------

def test_record_gauge():
    col = _col()
    p = col.gauge("cpu", 45.2)
    assert p.name == "cpu"
    assert p.value == 45.2
    assert p.metric_type == MetricType.GAUGE


def test_record_histogram():
    col = _col()
    p = col.histogram("req_duration", 120.5)
    assert p.metric_type == MetricType.HISTOGRAM


def test_record_with_tags():
    col = _col()
    p = col.gauge("cpu", 50.0, tags={"region": "br"})
    assert p.tags == {"region": "br"}


def test_record_updates_summary():
    col = _col()
    col.gauge("mem", 100.0)
    col.gauge("mem", 200.0)
    s = col.summary("mem")
    assert s.count == 2
    assert s.avg == 150.0


# ---------------------------------------------------------------------------
# increment
# ---------------------------------------------------------------------------

def test_increment_starts_at_zero():
    col = _col()
    val = col.increment("requests")
    assert val == 1.0


def test_increment_accumulates():
    col = _col()
    col.increment("requests")
    col.increment("requests")
    col.increment("requests", by=5.0)
    assert col.counter_value("requests") == 7.0


def test_increment_missing_counter():
    col = _col()
    assert col.counter_value("missing") == 0.0


# ---------------------------------------------------------------------------
# time_ms
# ---------------------------------------------------------------------------

def test_time_ms():
    col = _col()
    p = col.time_ms("db_query", 25.3)
    assert "duration_ms" in p.name
    assert p.value == 25.3


# ---------------------------------------------------------------------------
# points
# ---------------------------------------------------------------------------

def test_points_all():
    col = _col()
    col.gauge("a", 1.0)
    col.gauge("b", 2.0)
    assert len(col.points()) == 2


def test_points_filtered():
    col = _col()
    col.gauge("a", 1.0)
    col.gauge("b", 2.0)
    col.gauge("a", 3.0)
    pts = col.points("a")
    assert len(pts) == 2
    assert all(p.name == "a" for p in pts)


# ---------------------------------------------------------------------------
# all_summaries
# ---------------------------------------------------------------------------

def test_all_summaries():
    col = _col()
    col.gauge("a", 1.0)
    col.gauge("b", 2.0)
    summaries = col.all_summaries()
    assert "a" in summaries
    assert "b" in summaries


# ---------------------------------------------------------------------------
# reset
# ---------------------------------------------------------------------------

def test_reset():
    col = _col()
    col.gauge("a", 1.0)
    col.increment("c")
    col.reset()
    assert col.points() == []
    assert col.counter_value("c") == 0.0
    assert col.summary("a") is None


# ---------------------------------------------------------------------------
# snapshot
# ---------------------------------------------------------------------------

def test_snapshot():
    col = _col(module="bridge")
    col.gauge("cpu", 50.0)
    col.increment("reqs")
    snap = col.snapshot()
    assert snap["module"] == "bridge"
    assert snap["total_points"] >= 2
    assert "cpu" in snap["metrics"]
    assert "reqs" in snap["counters"]


def test_snapshot_empty():
    col = _col()
    snap = col.snapshot()
    assert snap["total_points"] == 0
    assert snap["metrics"] == []
