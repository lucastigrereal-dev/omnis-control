"""Tests for P24 Cockpit Renderer."""
import json

import pytest

from src.live_cockpit.models import CockpitModule, CockpitSnapshot
from src.live_cockpit.renderer import CockpitRenderer


class TestCockpitRenderer:
    @pytest.fixture
    def renderer(self):
        return CockpitRenderer(width=80)

    @pytest.fixture
    def snapshot(self):
        s = CockpitSnapshot.new()
        s.active_missions = [{"id": "m1", "summary": "test mission"}]
        s.missions_today = 3
        s.missions_completed_today = 2
        s.pending_approvals = 1

        s.active_campaigns = 2
        s.pending_deliveries = 1
        s.publish_queue_size = 5

        m = CockpitModule.new("P20", "omnis_supreme")
        m.status = "healthy"
        m.imports_ok = True
        s.modules = [m]
        s.modules_total = 1
        s.modules_healthy = 1

        s.autonomous_runs_active = 1
        s.memory_sources_available = 3
        s.recent_learnings = ["learn_1", "learn_2"]
        s.open_capability_gaps = 2
        s.disk_percent_free = 42.5
        s.containers_healthy = 5
        s.containers_unhealthy = 1

        s.alerts = [{"severity": "high", "module": "P20", "message": "test alert"}]

        return s

    def test_render_full_contains_header(self, renderer, snapshot):
        out = renderer.render(snapshot)
        assert "OMNIS LIVE COCKPIT SUPREME" in out
        assert snapshot.snapshot_id in out

    def test_render_full_contains_status(self, renderer, snapshot):
        out = renderer.render(snapshot)
        assert snapshot.overall_status.upper() in out

    def test_render_full_contains_missions_section(self, renderer, snapshot):
        out = renderer.render(snapshot)
        assert "MISSOES" in out
        assert "Ativas: 1" in out
        assert "Criadas hoje: 3" in out

    def test_render_full_contains_pipeline_section(self, renderer, snapshot):
        out = renderer.render(snapshot)
        assert "PIPELINE" in out
        assert "Campanhas ativas: 2" in out

    def test_render_full_contains_saude_section(self, renderer, snapshot):
        out = renderer.render(snapshot)
        assert "SAUDE" in out
        assert "Modulos: 1/1 healthy" in out

    def test_render_full_contains_autonomous_section(self, renderer, snapshot):
        out = renderer.render(snapshot)
        assert "AUTONOMOUS" in out
        assert "Runs ativas: 1" in out

    def test_render_full_contains_memory_section(self, renderer, snapshot):
        out = renderer.render(snapshot)
        assert "MEMORIA" in out
        assert "Fontes de memoria: 3" in out
        assert "Gaps de capability abertos: 2" in out

    def test_render_full_contains_alerts_section(self, renderer, snapshot):
        out = renderer.render(snapshot)
        assert "ALERTS" in out
        assert "test alert" in out

    def test_render_full_contains_modules_detail(self, renderer, snapshot):
        out = renderer.render(snapshot)
        assert "P20" in out
        assert "omnis_supreme" in out

    def test_render_full_disk_unavailable_when_negative(self, renderer, snapshot):
        snapshot.disk_percent_free = -1.0
        out = renderer.render(snapshot)
        assert "unavailable" in out.lower()

    def test_render_compact_fits_one_screen(self, renderer, snapshot):
        out = renderer.render_compact(snapshot)
        lines = out.split("\n")
        assert len(lines) <= 10

    def test_render_compact_contains_key_metrics(self, renderer, snapshot):
        out = renderer.render_compact(snapshot)
        assert snapshot.snapshot_id in out
        assert snapshot.overall_status.upper() in out

    def test_render_compact_shows_errors(self, renderer, snapshot):
        snapshot.collection_errors = ["observability: timeout"]
        out = renderer.render_compact(snapshot)
        assert "ERRORS" in out

    def test_render_json_is_valid(self, renderer, snapshot):
        out = renderer.render_json(snapshot)
        data = json.loads(out)
        assert data["snapshot_id"] == snapshot.snapshot_id
        assert data["missions_today"] == 3
        assert len(data["modules"]) == 1

    def test_render_markdown_has_headers(self, renderer, snapshot):
        out = renderer.render_markdown(snapshot)
        assert "# OMNIS" in out
        assert "## Missoes" in out
        assert "## Pipeline" in out
        assert "## Saude" in out
        assert "## Alerts" in out

    def test_render_empty_snapshot_no_error(self, renderer):
        s = CockpitSnapshot.new()
        out = renderer.render(s)
        assert "OMNIS LIVE COCKPIT SUPREME" in out
        assert "No alerts" in out
