"""Tests for W119 — CRM Export."""
from __future__ import annotations

import pytest
import tempfile
import json
from pathlib import Path

from src.sales.leads import LeadRegistry
from src.sales.deals import DealRegistry
from src.sales.timeline import ContactTimeline
from src.sales.dashboard import SalesDashboard, SalesMetrics
from src.sales.export import CRMExporter, CRMExportBundle


class TestCRMExportBundle:
    def test_create_bundle(self):
        b = CRMExportBundle(export_id="e1", leads_csv="a,b", deals_csv="x,y")
        assert b.export_id == "e1"
        assert b.leads_csv == "a,b"
        assert b.dry_run is True

    def test_to_dict(self):
        b = CRMExportBundle(export_id="e2", leads_csv="col1,col2", deals_csv="a,b")
        d = b.to_dict()
        assert d["export_id"] == "e2"


class TestCRMExporter:
    def setup_method(self):
        self.exporter = CRMExporter()
        self.leads = LeadRegistry()
        self.deals = DealRegistry()

    def _populate(self):
        self.leads.create(name="Hotel A", company="Co A", segment="hotel")
        self.leads.create(name="Rest B", company="Co B", segment="restaurante")
        self.deals.create(lead_id=self.leads.list_all()[0].lead_id, title="Deal 1", value=350.0)
        self.deals.create(lead_id=self.leads.list_all()[1].lead_id, title="Deal 2", value=990.0)

    def test_export_leads_csv(self):
        self._populate()
        bundle = self.exporter.export(self.leads, self.deals)
        assert "Hotel A" in bundle.leads_csv
        assert "Co A" in bundle.leads_csv
        assert "lead_id" in bundle.leads_csv

    def test_export_deals_csv(self):
        self._populate()
        bundle = self.exporter.export(self.leads, self.deals)
        assert "Deal 1" in bundle.deals_csv
        assert "350.0" in bundle.deals_csv

    def test_export_empty_leads_csv(self):
        bundle = self.exporter.export(self.leads, self.deals)
        assert bundle.leads_csv == ""

    def test_export_empty_deals_csv(self):
        bundle = self.exporter.export(self.leads, self.deals)
        assert bundle.deals_csv == ""

    def test_export_json(self):
        self._populate()
        bundle = self.exporter.export(self.leads, self.deals)
        data = json.loads(bundle.full_json)
        assert len(data["leads"]) == 2
        assert len(data["deals"]) == 2

    def test_export_with_timeline(self):
        self._populate()
        timeline = ContactTimeline()
        timeline.add_note("Primeira nota", lead_id=self.leads.list_all()[0].lead_id)
        bundle = self.exporter.export(self.leads, self.deals, timeline)
        assert "Primeira nota" in bundle.timeline_csv

    def test_export_empty_timeline(self):
        self._populate()
        timeline = ContactTimeline()
        bundle = self.exporter.export(self.leads, self.deals, timeline)
        assert bundle.timeline_csv == ""

    def test_export_with_metrics(self):
        self._populate()
        dashboard = SalesDashboard()
        metrics = dashboard.compute(self.deals)
        bundle = self.exporter.export(self.leads, self.deals, metrics=metrics)
        assert "Sales Dashboard" in bundle.dashboard_md

    def test_export_to_dir(self):
        self._populate()
        dashboard = SalesDashboard()
        metrics = dashboard.compute(self.deals)
        with tempfile.TemporaryDirectory() as tmp:
            files = self.exporter.export_to_dir(tmp, self.leads, self.deals, metrics=metrics)
            assert len(files) == 4  # leads.csv, deals.csv, dashboard.md, crm_export.json (no timeline)
            assert Path(tmp, "leads.csv").exists()
            assert Path(tmp, "deals.csv").exists()
            assert Path(tmp, "dashboard.md").exists()
            assert Path(tmp, "crm_export.json").exists()

            content = Path(tmp, "leads.csv").read_text(encoding="utf-8")
            assert "Hotel A" in content

    def test_export_to_dir_with_timeline(self):
        self._populate()
        timeline = ContactTimeline()
        timeline.add_note("Test event")
        dashboard = SalesDashboard()
        metrics = dashboard.compute(self.deals)
        with tempfile.TemporaryDirectory() as tmp:
            files = self.exporter.export_to_dir(tmp, self.leads, self.deals, timeline, metrics)
            assert len(files) == 5
            assert Path(tmp, "timeline.csv").exists()

    def test_no_external_calls(self):
        self._populate()
        bundle = self.exporter.export(self.leads, self.deals)
        assert bundle.dry_run is True

    def test_csv_has_header_and_data(self):
        self._populate()
        bundle = self.exporter.export(self.leads, self.deals)
        lines = bundle.leads_csv.strip().split("\r\n")
        assert len(lines) >= 3  # header + 2 data rows

    def test_json_is_valid(self):
        self._populate()
        bundle = self.exporter.export(self.leads, self.deals)
        data = json.loads(bundle.full_json)
        assert isinstance(data, dict)
        assert "leads" in data
        assert "deals" in data
