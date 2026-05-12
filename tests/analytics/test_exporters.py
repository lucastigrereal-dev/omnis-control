"""Tests for P13 Analytics/BI exporters."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from src.analytics.errors import ExportError
from src.analytics.exporters import export_dashboard_json, export_report_markdown
from src.analytics.models import DashboardSpec, MetricDefinition, ReportSpec


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════

def _dashboard(**kw) -> DashboardSpec:
    return DashboardSpec.new(
        title=kw.pop("title", "Test Dashboard"),
        description=kw.pop("description", "A test dashboard."),
        **kw,
    )


def _report(**kw) -> ReportSpec:
    return ReportSpec.new(
        title=kw.pop("title", "Test Report"),
        description=kw.pop("description", "A test report."),
        **kw,
    )


# ═══════════════════════════════════════════════════════════════
# export_dashboard_json
# ═══════════════════════════════════════════════════════════════

class TestExportDashboardJson:
    def test_export_creates_file(self):
        spec = _dashboard()
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "dash.json"
            result = export_dashboard_json(spec, out)
            assert result.exists()
            assert result.suffix == ".json"

    def test_export_contains_meta_and_dashboard(self):
        spec = _dashboard(title="KPI Overview")
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "dash.json"
            export_dashboard_json(spec, out)
            data = json.loads(out.read_text(encoding="utf-8"))
            assert data["meta"]["exporter"] == "P13 Analytics/BI"
            assert data["meta"]["dry_run"] is True
            assert data["dashboard"]["title"] == "KPI Overview"

    def test_export_creates_parent_dirs(self):
        spec = _dashboard()
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "deep" / "nested" / "dash.json"
            result = export_dashboard_json(spec, out)
            assert result.exists()

    def test_export_round_trip(self):
        spec = _dashboard(
            title="Round Trip Dash",
            widgets=[{"type": "kpi_card", "title": "Views", "metric_id": "met_abc"}],
        )
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "dash.json"
            export_dashboard_json(spec, out)
            data = json.loads(out.read_text(encoding="utf-8"))
            restored = DashboardSpec.from_dict(data["dashboard"])
            assert restored.id == spec.id
            assert restored.title == spec.title
            assert restored.widgets == spec.widgets

    def test_export_with_widgets(self):
        widgets = [
            {"type": "line_chart", "title": "Trend", "metric_id": "met_1"},
            {"type": "bar_chart", "title": "Breakdown", "metric_id": "met_2"},
        ]
        spec = _dashboard(widgets=widgets)
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "dash.json"
            export_dashboard_json(spec, out)
            data = json.loads(out.read_text(encoding="utf-8"))
            assert len(data["dashboard"]["widgets"]) == 2


# ═══════════════════════════════════════════════════════════════
# export_report_markdown
# ═══════════════════════════════════════════════════════════════

class TestExportReportMarkdown:
    def test_export_creates_file(self):
        spec = _report()
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "report.md"
            result = export_report_markdown(spec, out)
            assert result.exists()
            assert result.suffix == ".md"

    def test_export_contains_title_and_description(self):
        spec = _report(title="Weekly Report", description="Week 19 summary.")
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "report.md"
            export_report_markdown(spec, out)
            content = out.read_text(encoding="utf-8")
            assert "# Weekly Report" in content
            assert "Week 19 summary" in content

    def test_export_contains_metadata(self):
        spec = _report()
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "report.md"
            export_report_markdown(spec, out)
            content = out.read_text(encoding="utf-8")
            assert f"`{spec.id}`" in content
            assert "dry-run" in content

    def test_export_with_sections(self):
        sections = [
            {"title": "Overview", "type": "summary", "content": "Everything is running smoothly."},
            {"title": "Metrics", "type": "charts", "content": ["Metric A: +10%", "Metric B: -2%"], "charts": [{"title": "Growth", "type": "line_chart", "metric_id": "met_abc"}]},
        ]
        spec = _report(sections=sections)
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "report.md"
            export_report_markdown(spec, out)
            content = out.read_text(encoding="utf-8")
            assert "## Overview" in content
            assert "_Type: summary_" in content
            assert "Everything is running smoothly" in content
            assert "## Metrics" in content
            assert "- Metric A: +10%" in content
            assert "### Charts" in content
            assert "line_chart" in content
            assert "Generated by P13 Analytics/BI Skeleton" in content

    def test_export_empty_sections(self):
        spec = _report(sections=[])
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "report.md"
            export_report_markdown(spec, out)
            content = out.read_text(encoding="utf-8")
            assert "# Test Report" in content

    def test_export_creates_parent_dirs(self):
        spec = _report()
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "a" / "b" / "c" / "report.md"
            result = export_report_markdown(spec, out)
            assert result.exists()
