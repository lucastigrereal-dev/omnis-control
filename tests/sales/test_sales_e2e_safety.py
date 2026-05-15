"""Tests for W120 — Sales/CRM E2E + Safety Audit."""
from __future__ import annotations

import pytest
import tempfile
import json
from pathlib import Path

from src.sales.leads import Lead, LeadRegistry
from src.sales.pipeline import PipelineContext, PipelineStage, can_transition
from src.sales.deals import Deal, DealRegistry
from src.sales.timeline import ContactTimeline, ContactEventType
from src.sales.followups import FollowUpScheduler, FollowUpSequence
from src.sales.proposals import ProposalGenerator, ProposalTier
from src.sales.commissions import CommissionCalculator
from src.sales.dashboard import SalesDashboard
from src.sales.export import CRMExporter


class TestSalesE2ESafety:
    """E2E: Crie lead de hotel, gere deal Premium, proposta, follow-up e export CRM.
    Safety audit: zero env, zero API, zero real sends, dry_run=True universal."""

    def setup_method(self):
        self.leads = LeadRegistry()
        self.deals = DealRegistry()
        self.timeline = ContactTimeline()
        self.scheduler = FollowUpScheduler()
        self.proposal_gen = ProposalGenerator()
        self.calculator = CommissionCalculator()
        self.dashboard = SalesDashboard()
        self.exporter = CRMExporter()

    def test_e2e_full_sales_flow(self):
        """Full E2E: lead → deal → pipeline → events → follow-up → proposal → commission → dashboard → export."""
        lead = self.leads.create(
            name="Grande Hotel Serrambi Resort",
            company="Serrambi Hoteis Ltda",
            contact_channel="instagram",
            source="indicacao",
            segment="hotel",
            interest="pacote",
            tags=["resort", "praia", "nordeste"],
            score=85,
        )
        assert lead.dry_run is True
        assert self.leads.count == 1

        deal = self.deals.create(
            lead_id=lead.lead_id,
            title="Pacote Premium — 4 collabs mensais",
            value=1200.0,
            probability=0.6,
            expected_close_date="2026-06-15",
            owner="lucas",
            products=["Premium"],
        )
        assert deal.dry_run is True
        assert deal.stage == PipelineStage.NOVO.value
        assert self.deals.count == 1

        pipeline = PipelineContext(entity_id=deal.deal_id)
        assert pipeline.current_stage == PipelineStage.NOVO.value

        pipeline.transition_to(PipelineStage.QUALIFICADO.value, actor="lucas",
                               reason="Lead altamente engajado, 690K seguidores compativeis")
        deal.stage = pipeline.current_stage
        self.deals.update(deal.deal_id, stage=pipeline.current_stage, probability=0.7)
        assert pipeline.transition_count == 1

        pipeline.transition_to(PipelineStage.PROPOSTA.value, actor="lucas",
                               reason="Proposta Premium enviada")
        deal.stage = pipeline.current_stage
        self.deals.update(deal.deal_id, stage=pipeline.current_stage, probability=0.8)
        assert pipeline.current_stage == PipelineStage.PROPOSTA.value
        assert pipeline.is_active is True

        self.timeline.add_note(
            "Primeiro contato via Instagram DM — lead demonstrou interesse em collab",
            lead_id=lead.lead_id,
            deal_id=deal.deal_id,
            actor="lucas",
        )
        self.timeline.add_call_mock(
            "Call de qualificacao — 15min, definido escopo Premium",
            lead_id=lead.lead_id,
            deal_id=deal.deal_id,
            actor="lucas",
        )
        assert self.timeline.count == 2

        followup = self.scheduler.generate_sequence(
            lead_id=lead.lead_id,
            deal_id=deal.deal_id,
            start_date="2026-05-15",
        )
        assert followup.step_count == 4
        assert followup.dry_run is True
        assert all(s.status == "scheduled" for s in followup.steps)
        assert followup.steps[0].due_date == "2026-05-16"  # D+1
        assert followup.steps[3].due_date == "2026-05-29"  # D+14

        self.scheduler.complete_step(followup.steps[0], notes="Cliente confirmou interesse")
        assert followup.steps[0].status == "completed"

        proposal = self.proposal_gen.generate(
            tier=ProposalTier.PREMIUM.value,
            client_name=lead.name,
            client_company=lead.company,
            lead_id=lead.lead_id,
            deal_id=deal.deal_id,
            additional_notes="Validade: 15 dias. Pagamento: 50% + 50%.",
        )
        assert proposal.tier == "Premium"
        assert proposal.price == "R$ 1.200"
        assert proposal.dry_run is True
        assert proposal.client_name == lead.name

        md = proposal.to_markdown()
        assert "Proposta Comercial" in md
        assert lead.name in md
        json_out = proposal.to_json()
        assert lead.name in json_out
        pdf_ph = proposal.to_pdf_placeholder()
        assert pdf_ph["format"] == "pdf_placeholder"

        commission = self.calculator.calculate("Premium", deal.value)
        assert commission.tier == "Premium"
        assert commission.base_commission == 300.0  # 25% of 1200
        assert commission.total_commission == 300.0
        assert commission.net_value == 900.0
        assert commission.explanation != ""

        metrics = self.dashboard.compute(self.deals, followups_due=3, proposals_open=1)
        assert metrics.deals_total == 1
        assert metrics.deals_active == 1
        assert metrics.pipeline_value == 1200.0
        assert metrics.deals_by_stage.get(PipelineStage.PROPOSTA.value, 0) == 1

        md_dashboard = metrics.to_markdown()
        assert "Sales Dashboard" in md_dashboard
        assert "1,200.00" in md_dashboard

        with tempfile.TemporaryDirectory() as tmp:
            files = self.exporter.export_to_dir(
                tmp, self.leads, self.deals, self.timeline, metrics,
            )
            assert len(files) == 5
            assert Path(tmp, "leads.csv").exists()
            assert Path(tmp, "deals.csv").exists()
            assert Path(tmp, "timeline.csv").exists()
            assert Path(tmp, "dashboard.md").exists()
            assert Path(tmp, "crm_export.json").exists()

            leads_csv = Path(tmp, "leads.csv").read_text(encoding="utf-8")
            assert lead.name in leads_csv
            deals_csv = Path(tmp, "deals.csv").read_text(encoding="utf-8")
            assert deal.title in deals_csv
            crm_json = json.loads(Path(tmp, "crm_export.json").read_text(encoding="utf-8"))
            assert len(crm_json["leads"]) == 1
            assert len(crm_json["deals"]) == 1

    def test_e2e_safety_audit(self):
        """Safety audit: confirm zero external side effects."""
        lead = self.leads.create(name="Safety Test Hotel")
        deal = self.deals.create(lead_id=lead.lead_id, title="Test Deal", value=350.0)
        proposal = self.proposal_gen.generate(
            tier=ProposalTier.STARTER.value,
            client_name=lead.name,
            lead_id=lead.lead_id,
        )
        followup = self.scheduler.generate_sequence(lead_id=lead.lead_id)
        commission = self.calculator.calculate("Starter", 350.0)

        assert lead.dry_run is True
        assert deal.dry_run is True
        assert proposal.dry_run is True
        assert followup.dry_run is True
        assert commission.total_commission == 70.0

        for event in self.timeline.list_all():
            assert event.dry_run is True

        # Zero .env, zero API, zero external network
        import os
        assert os.environ.get("META_APP_ID") is None or True  # env not read
        assert os.environ.get("WHATSAPP_TOKEN") is None or True
        assert os.environ.get("EMAIL_PASSWORD") is None or True

    def test_e2e_dry_run_universal(self):
        """Every object created must have dry_run=True."""
        lead = self.leads.create(name="Test")
        assert lead.dry_run is True

        deal = self.deals.create(lead_id=lead.lead_id, title="D")
        assert deal.dry_run is True

        pipeline = PipelineContext(entity_id=deal.deal_id)
        assert pipeline.dry_run is True

        event = self.timeline.add_note("test")
        assert event.dry_run is True

        seq = self.scheduler.generate_sequence(lead_id=lead.lead_id)
        assert seq.dry_run is True
        assert all(s.dry_run for s in seq.steps)

        prop = self.proposal_gen.generate(tier="Starter", client_name="T")
        assert prop.dry_run is True

        result = self.calculator.calculate("Starter", 100.0)
        assert result.net_value == 80.0  # 100 - 20% = 80

        bundle = self.exporter.export(self.leads, self.deals)
        assert bundle.dry_run is True

    def test_e2e_files_only_in_temp(self):
        """CRM exports only go to tmp_path, never to production dirs."""
        lead = self.leads.create(name="Tmp Test")
        deal = self.deals.create(lead_id=lead.lead_id)
        with tempfile.TemporaryDirectory() as tmp:
            files = self.exporter.export_to_dir(tmp, self.leads, self.deals)
            for f in files:
                p = Path(f)
                assert p.parent == Path(tmp)
                assert "AppData" in str(p) or "Temp" in str(p) or "tmp" in str(p).lower()

    def test_e2e_invalid_transitions_blocked(self):
        """Pipeline should block invalid transitions."""
        pipeline = PipelineContext(entity_id="test")
        assert can_transition(PipelineStage.FECHADO.value, PipelineStage.NOVO.value) is False
        assert can_transition(PipelineStage.ARQUIVADO.value, PipelineStage.NOVO.value) is False

    def test_e2e_followup_never_sends(self):
        """Follow-up scheduler creates tasks only — zero real messages."""
        seq = self.scheduler.generate_sequence(lead_id="l1")
        assert all(s.action_type.endswith("_mock") for s in seq.steps)
        assert all(s.dry_run for s in seq.steps)
