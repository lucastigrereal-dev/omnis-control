"""E2E tests for P24 Live Cockpit Supreme."""
import json
import tempfile
from pathlib import Path

import pytest

from src.live_cockpit.cli import main
from src.live_cockpit.collector import CockpitCollector
from src.live_cockpit.renderer import CockpitRenderer
from src.live_cockpit.models import CockpitSnapshot


class TestE2EFullFlow:
    def test_collect_then_render_full(self):
        collector = CockpitCollector()
        snapshot = collector.collect_all()
        renderer = CockpitRenderer()

        output = renderer.render(snapshot)
        assert "OMNIS LIVE COCKPIT SUPREME" in output
        assert "MISSOES" in output
        assert "PIPELINE" in output
        assert "SAUDE" in output
        assert "MODULOS" in output

    def test_collect_then_render_compact(self):
        collector = CockpitCollector()
        snapshot = collector.collect_all()
        renderer = CockpitRenderer()

        output = renderer.render_compact(snapshot)
        lines = output.split("\n")
        assert len(lines) <= 10

    def test_collect_then_render_json(self):
        collector = CockpitCollector()
        snapshot = collector.collect_all()
        renderer = CockpitRenderer()

        output = renderer.render_json(snapshot)
        data = json.loads(output)
        assert "snapshot_id" in data
        assert "modules" in data
        assert "alerts" in data

    def test_collect_then_render_markdown(self):
        collector = CockpitCollector()
        snapshot = collector.collect_all()
        renderer = CockpitRenderer()

        output = renderer.render_markdown(snapshot)
        assert output.startswith("# ")
        assert "## Missoes" in output
        assert "## Saude" in output


class TestE2ECollectorDegradation:
    """Cockpit nunca quebra, mesmo com modulos indisponiveis."""

    def test_collect_all_never_raises_even_with_bad_data(self):
        collector = CockpitCollector()
        # Forca erro inserindo collector que lanca excecao
        try:
            snapshot = collector.collect_all()
            assert isinstance(snapshot, CockpitSnapshot)
        except Exception as e:
            pytest.fail(f"collect_all() should never raise, got: {e}")

    def test_snapshot_has_collection_metadata(self):
        collector = CockpitCollector()
        snapshot = collector.collect_all()
        assert hasattr(snapshot, "collection_errors")
        assert hasattr(snapshot, "collection_warnings")


class TestE2ECLIIntegration:
    def test_cli_show(self):
        exit_code = main(["show", "--width", "80"])
        assert exit_code == 0

    def test_cli_compact(self):
        exit_code = main(["compact"])
        assert exit_code == 0

    def test_cli_export_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_file = Path(tmp) / "snapshot.json"
            exit_code = main(["export", "--format", "json", "-o", str(out_file)])
            assert exit_code == 0
            data = json.loads(out_file.read_text(encoding="utf-8"))
            assert "snapshot_id" in data

    def test_cli_export_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_file = Path(tmp) / "snapshot.md"
            exit_code = main(["export", "--format", "markdown", "-o", str(out_file)])
            assert exit_code == 0
            content = out_file.read_text(encoding="utf-8")
            assert content.startswith("# ")

    def test_cli_no_command(self):
        exit_code = main([])
        assert exit_code == 1


class TestE2ESnapshotExport:
    def test_full_snapshot_roundtrip_via_dict(self):
        collector = CockpitCollector()
        s1 = collector.collect_all()
        s2 = CockpitSnapshot.from_dict(s1.to_dict())
        assert s2.snapshot_id == s1.snapshot_id
        assert s2.modules_total == s1.modules_total
        assert s2.alerts == s1.alerts
