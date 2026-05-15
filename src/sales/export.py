"""W119 — CRM Export (CSV, JSON, Markdown)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import csv
import io
import json
from pathlib import Path

from src.sales.leads import LeadRegistry
from src.sales.deals import DealRegistry
from src.sales.timeline import ContactTimeline
from src.sales.dashboard import SalesMetrics


@dataclass
class CRMExportBundle:
    """Bundle of all CRM exports."""

    export_id: str
    leads_csv: str = ""
    deals_csv: str = ""
    timeline_csv: str = ""
    dashboard_md: str = ""
    full_json: str = ""
    exported_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    dry_run: bool = True

    def to_dict(self) -> dict:
        return {
            "export_id": self.export_id,
            "leads_csv": self.leads_csv,
            "deals_csv": self.deals_csv,
            "timeline_csv": self.timeline_csv,
            "dashboard_md": self.dashboard_md,
            "full_json": self.full_json,
            "exported_at": self.exported_at,
            "dry_run": self.dry_run,
        }


class CRMExporter:
    """Exports CRM data to CSV/JSON/Markdown — zero external calls, zero real sends."""

    def export(
        self,
        leads: LeadRegistry,
        deals: DealRegistry,
        timeline: ContactTimeline | None = None,
        metrics: SalesMetrics | None = None,
    ) -> CRMExportBundle:
        import uuid

        return CRMExportBundle(
            export_id=str(uuid.uuid4())[:12],
            leads_csv=self._leads_to_csv(leads),
            deals_csv=self._deals_to_csv(deals),
            timeline_csv=self._timeline_to_csv(timeline),
            dashboard_md=metrics.to_markdown() if metrics else "",
            full_json=self._to_json(leads, deals, timeline, metrics),
        )

    def export_to_dir(
        self,
        output_dir: str | Path,
        leads: LeadRegistry,
        deals: DealRegistry,
        timeline: ContactTimeline | None = None,
        metrics: SalesMetrics | None = None,
    ) -> list[str]:
        """Write export files to a directory. Returns list of file paths."""
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        bundle = self.export(leads, deals, timeline, metrics)
        files: list[str] = []

        paths = [
            (out / "leads.csv", bundle.leads_csv),
            (out / "deals.csv", bundle.deals_csv),
            (out / "timeline.csv", bundle.timeline_csv),
            (out / "dashboard.md", bundle.dashboard_md),
            (out / "crm_export.json", bundle.full_json),
        ]
        for p, content in paths:
            if content:
                p.write_text(content, encoding="utf-8")
                files.append(str(p))
        return files

    def _leads_to_csv(self, leads: LeadRegistry) -> str:
        buf = io.StringIO()
        all_leads = leads.list_all()
        if not all_leads:
            return ""
        w = csv.DictWriter(buf, fieldnames=list(all_leads[0].to_dict().keys()),
                           extrasaction="ignore")
        w.writeheader()
        for l in all_leads:
            w.writerow(l.to_dict())
        return buf.getvalue()

    def _deals_to_csv(self, deals: DealRegistry) -> str:
        buf = io.StringIO()
        all_deals = deals.list_all()
        if not all_deals:
            return ""
        w = csv.DictWriter(buf, fieldnames=list(all_deals[0].to_dict().keys()),
                           extrasaction="ignore")
        w.writeheader()
        for d in all_deals:
            w.writerow(d.to_dict())
        return buf.getvalue()

    def _timeline_to_csv(self, timeline: ContactTimeline | None) -> str:
        if not timeline or timeline.count == 0:
            return ""
        buf = io.StringIO()
        events = timeline.list_all()
        w = csv.DictWriter(buf, fieldnames=list(events[0].to_dict().keys()),
                           extrasaction="ignore")
        w.writeheader()
        for e in events:
            w.writerow(e.to_dict())
        return buf.getvalue()

    def _to_json(
        self,
        leads: LeadRegistry,
        deals: DealRegistry,
        timeline: ContactTimeline | None,
        metrics: SalesMetrics | None,
    ) -> str:
        data: dict = {
            "leads": [l.to_dict() for l in leads.list_all()],
            "deals": [d.to_dict() for d in deals.list_all()],
        }
        if timeline:
            data["timeline"] = timeline.to_dict_list()
        if metrics:
            data["metrics"] = metrics.to_dict()
        return json.dumps(data, ensure_ascii=False, indent=2)
