"""Tests for P24 Live Cockpit models."""
import json

import pytest

from src.live_cockpit.errors import (
    CockpitError,
    CollectionError,
    ExportError,
    ModuleUnreachableError,
    RenderError,
)
from src.live_cockpit.models import CockpitModule, CockpitSnapshot


class TestCockpitModule:
    def test_new_creates_with_unknown_status(self):
        m = CockpitModule.new("P20", "omnis_supreme")
        assert m.module_name == "P20"
        assert m.namespace == "omnis_supreme"
        assert m.status == "unknown"
        assert m.test_count == 0
        assert m.test_pass_rate == 0.0
        assert m.imports_ok is False
        assert m.alerts == []
        assert m.last_validated != ""

    def test_is_healthy(self):
        m = CockpitModule.new("P20", "omnis_supreme")
        m.status = "healthy"
        assert m.is_healthy is True
        assert m.is_degraded is False
        assert m.is_error is False

    def test_is_degraded(self):
        m = CockpitModule.new("P20", "omnis_supreme")
        m.status = "degraded"
        assert m.is_degraded is True
        assert m.is_healthy is False

    def test_is_error(self):
        m = CockpitModule.new("P20", "omnis_supreme")
        m.status = "error"
        assert m.is_error is True

    def test_alerts_list_mutable(self):
        m = CockpitModule.new("P20", "omnis_supreme")
        m.alerts.append("test failing")
        assert len(m.alerts) == 1

    def test_to_dict(self):
        m = CockpitModule.new("P16", "observability_local")
        m.status = "healthy"
        m.test_count = 10
        m.test_pass_rate = 0.9
        d = m.to_dict()
        assert d["module_name"] == "P16"
        assert d["status"] == "healthy"
        assert d["test_count"] == 10
        assert d["test_pass_rate"] == 0.9

    def test_from_dict_roundtrip(self):
        m = CockpitModule.new("P20", "omnis_supreme")
        m.status = "healthy"
        m.test_count = 20
        m.test_pass_rate = 1.0
        m.imports_ok = True
        m.alerts = ["alert_1"]
        m2 = CockpitModule.from_dict(m.to_dict())
        assert m2.module_name == m.module_name
        assert m2.status == m.status
        assert m2.test_count == m.test_count
        assert m2.alerts == m.alerts


class TestCockpitSnapshot:
    def test_new_creates_empty_snapshot(self):
        s = CockpitSnapshot.new()
        assert s.snapshot_id.startswith("ckp_")
        assert len(s.snapshot_id) == 12
        assert s.generated_at != ""
        assert s.active_missions == []
        assert s.missions_today == 0
        assert s.missions_completed_today == 0
        assert s.pending_approvals == 0
        assert s.active_campaigns == 0
        assert s.pending_deliveries == 0
        assert s.publish_queue_size == 0
        assert s.modules_healthy == 0
        assert s.modules_total == 0
        assert s.tests_passing == 0
        assert s.tests_failing == 0
        assert s.alerts == []
        assert s.modules == []
        assert s.autonomous_runs_active == 0
        assert s.autonomous_runs_paused == 0
        assert s.memory_sources_available == 0
        assert s.recent_learnings == []
        assert s.open_capability_gaps == 0
        assert s.disk_percent_free == 0.0
        assert s.containers_healthy == 0
        assert s.containers_unhealthy == 0

    def test_is_complete_no_errors(self):
        s = CockpitSnapshot.new()
        assert s.is_complete is True

    def test_is_complete_with_errors(self):
        s = CockpitSnapshot.new()
        s.collection_errors.append("P20 unreachable")
        assert s.is_complete is False

    def test_overall_status_healthy(self):
        s = CockpitSnapshot.new()
        s.modules_total = 5
        s.modules_healthy = 5
        assert s.overall_status == "healthy"

    def test_overall_status_degraded_modules(self):
        s = CockpitSnapshot.new()
        s.modules_total = 5
        s.modules_healthy = 3
        assert s.overall_status == "degraded"

    def test_overall_status_critical_alert(self):
        s = CockpitSnapshot.new()
        s.alerts = [{"severity": "critical", "message": "test"}]
        assert s.overall_status == "critical"

    def test_overall_status_collection_failed(self):
        s = CockpitSnapshot.new()
        s.collection_errors = ["P20 error"]
        assert s.overall_status == "degraded"

    def test_to_dict_includes_modules(self):
        s = CockpitSnapshot.new()
        s.active_missions = [{"id": "1", "summary": "test"}]
        m = CockpitModule.new("P20", "omnis_supreme")
        m.status = "healthy"
        s.modules = [m]
        s.modules_total = 1
        s.modules_healthy = 1
        d = s.to_dict()
        assert len(d["active_missions"]) == 1
        assert len(d["modules"]) == 1
        assert d["modules"][0]["status"] == "healthy"

    def test_from_dict_roundtrip(self):
        s = CockpitSnapshot.new()
        s.missions_today = 5
        s.modules_total = 3
        s.modules_healthy = 2
        s.disk_percent_free = 45.5
        m = CockpitModule.new("P20", "omnis_supreme")
        m.status = "healthy"
        s.modules = [m]
        s.recent_learnings = ["learning 1", "learning 2"]

        s2 = CockpitSnapshot.from_dict(s.to_dict())
        assert s2.missions_today == 5
        assert s2.modules_total == 3
        assert s2.modules_healthy == 2
        assert s2.disk_percent_free == 45.5
        assert len(s2.modules) == 1
        assert s2.modules[0].status == "healthy"
        assert s2.recent_learnings == ["learning 1", "learning 2"]


class TestErrors:
    def test_cockpit_error_is_exception(self):
        with pytest.raises(CockpitError):
            raise CockpitError("base error")

    def test_module_unreachable_extends_base(self):
        with pytest.raises(CockpitError):
            raise ModuleUnreachableError("cannot import")

    def test_collection_error_extends_base(self):
        with pytest.raises(CockpitError):
            raise CollectionError("collect failed")

    def test_render_error_extends_base(self):
        with pytest.raises(CockpitError):
            raise RenderError("render failed")

    def test_export_error_extends_base(self):
        with pytest.raises(CockpitError):
            raise ExportError("export failed")

    def test_all_are_exceptions(self):
        for cls in [ModuleUnreachableError, CollectionError, RenderError, ExportError]:
            assert issubclass(cls, Exception)
