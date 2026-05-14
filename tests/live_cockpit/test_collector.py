"""Tests for P24 Cockpit Collector."""
import pytest

from src.live_cockpit.collector import CockpitCollector
from src.live_cockpit.models import CockpitSnapshot


class TestCockpitCollectorInit:
    def test_creates_with_defaults(self):
        c = CockpitCollector()
        assert c.dry_run is True
        assert c.alert_aggregator is not None

    def test_creates_with_dry_run_false(self):
        c = CockpitCollector(dry_run=False)
        assert c.dry_run is False


class TestCollectAll:
    @pytest.fixture
    def collector(self):
        return CockpitCollector()

    def test_collect_all_returns_snapshot(self, collector):
        result = collector.collect_all()
        assert isinstance(result, CockpitSnapshot)
        assert result.snapshot_id.startswith("ckp_")
        assert result.generated_at != ""

    def test_collect_all_has_modules(self, collector):
        result = collector.collect_all()
        assert result.modules_total > 0
        assert len(result.modules) > 0
        assert result.modules_total == len(result.modules)

    def test_collect_all_has_alerts(self, collector):
        result = collector.collect_all()
        assert isinstance(result.alerts, list)

    def test_collect_all_never_raises(self, collector):
        """Principio fundamental: cockpit nunca quebra."""
        try:
            collector.collect_all()
        except Exception as e:
            pytest.fail(f"collect_all() raised {e}")

    def test_collect_all_counts_healthy_modules(self, collector):
        result = collector.collect_all()
        assert result.modules_healthy <= result.modules_total


class TestIndividualCollectors:
    @pytest.fixture
    def collector(self):
        return CockpitCollector()

    def test_collect_missions(self, collector):
        data = collector.collect_missions()
        assert "active_missions" in data
        assert "missions_today" in data
        assert "missions_completed_today" in data
        assert "pending_approvals" in data
        assert isinstance(data["active_missions"], list)

    def test_collect_campaigns(self, collector):
        data = collector.collect_campaigns()
        assert "active_campaigns" in data

    def test_collect_deliveries(self, collector):
        data = collector.collect_deliveries()
        assert "pending_deliveries" in data

    def test_collect_publish_queue(self, collector):
        data = collector.collect_publish_queue()
        assert "publish_queue_size" in data

    def test_collect_observability(self, collector):
        data = collector.collect_observability()
        assert "tests_passing" in data
        assert "tests_failing" in data

    def test_collect_memory(self, collector):
        data = collector.collect_memory()
        assert "memory_sources_available" in data
        assert "recent_learnings" in data

    def test_collect_capability_gaps(self, collector):
        data = collector.collect_capability_gaps()
        assert "open_capability_gaps" in data

    def test_collect_autonomous(self, collector):
        data = collector.collect_autonomous()
        assert "autonomous_runs_active" in data
        assert "autonomous_runs_paused" in data

    def test_collect_system_health(self, collector):
        data = collector.collect_system_health()
        assert "disk_percent_free" in data
        assert "containers_healthy" in data
        assert "containers_unhealthy" in data

    def test_collect_module_health(self, collector):
        data = collector.collect_module_health()
        assert "modules" in data
        assert len(data["modules"]) > 0
        m = data["modules"][0]
        assert hasattr(m, "module_name")
        assert hasattr(m, "status")
        assert hasattr(m, "imports_ok")
