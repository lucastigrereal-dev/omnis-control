"""Tests for P24 Alert Aggregator."""
import pytest

from src.live_cockpit.alerts import AlertAggregator, SEVERITY_ORDER
from src.live_cockpit.models import CockpitModule, CockpitSnapshot


class TestAlertAggregator:
    @pytest.fixture
    def agg(self):
        return AlertAggregator()

    def test_collect_alerts_from_modules(self, agg):
        snap = CockpitSnapshot.new()
        m = CockpitModule.new("P20", "omnis_supreme")
        m.alerts = ["test failing"]
        snap.modules = [m]
        alerts = agg.collect_alerts(snap)
        assert len(alerts) == 1
        assert alerts[0]["module"] == "P20"
        assert alerts[0]["severity"] == "high"  # "fail" in message

    def test_collect_alerts_empty(self, agg):
        snap = CockpitSnapshot.new()
        alerts = agg.collect_alerts(snap)
        assert alerts == []

    def test_collect_alerts_from_collection_errors(self, agg):
        snap = CockpitSnapshot.new()
        snap.collection_errors = ["observability: no data"]
        alerts = agg.collect_alerts(snap)
        assert len(alerts) == 1
        assert alerts[0]["severity"] == "critical"

    def test_collect_alerts_from_collection_warnings(self, agg):
        snap = CockpitSnapshot.new()
        snap.collection_warnings = ["observability: slow response"]
        alerts = agg.collect_alerts(snap)
        assert len(alerts) == 1
        assert alerts[0]["severity"] == "medium"

    def test_prioritize_critical_before_high(self, agg):
        alerts = [
            {"severity": "low", "message": "l"},
            {"severity": "critical", "message": "c"},
            {"severity": "high", "message": "h"},
        ]
        sorted_alerts = agg.prioritize(alerts)
        assert sorted_alerts[0]["severity"] == "critical"
        assert sorted_alerts[1]["severity"] == "high"
        assert sorted_alerts[2]["severity"] == "low"

    def test_prioritize_unknown_severity_last(self, agg):
        alerts = [
            {"severity": "unknown_sev", "message": "x"},
            {"severity": "critical", "message": "c"},
        ]
        sorted_alerts = agg.prioritize(alerts)
        assert sorted_alerts[0]["severity"] == "critical"
        assert sorted_alerts[-1]["severity"] == "unknown_sev"

    def test_summary_single(self, agg):
        alerts = [{"severity": "critical", "message": "error"}]
        s = agg.summary(alerts)
        assert "1 critical" in s

    def test_summary_multiple(self, agg):
        alerts = [
            {"severity": "critical", "message": "c1"},
            {"severity": "critical", "message": "c2"},
            {"severity": "high", "message": "h1"},
            {"severity": "medium", "message": "m1"},
        ]
        s = agg.summary(alerts)
        assert "2 critical" in s
        assert "1 high" in s
        assert "1 medium" in s

    def test_summary_empty(self, agg):
        s = agg.summary([])
        assert s == "0 alerts"

    def test_summary_omits_zero_counts(self, agg):
        alerts = [{"severity": "high", "message": "h1"}]
        s = agg.summary(alerts)
        assert "critical" not in s
        assert "1 high" in s


class TestSeverityOrder:
    def test_critical_is_lowest(self):
        assert SEVERITY_ORDER["critical"] == 0

    def test_info_is_highest(self):
        assert SEVERITY_ORDER["info"] == 4

    def test_order_is_strict(self):
        assert SEVERITY_ORDER["critical"] < SEVERITY_ORDER["high"]
        assert SEVERITY_ORDER["high"] < SEVERITY_ORDER["medium"]
        assert SEVERITY_ORDER["medium"] < SEVERITY_ORDER["low"]
        assert SEVERITY_ORDER["low"] < SEVERITY_ORDER["info"]
