"""Tests for W116 — Proposal Generator."""
from __future__ import annotations

import pytest

from src.sales.proposals import (
    Proposal,
    ProposalGenerator,
    ProposalTier,
    TIER_DETAILS,
)


class TestProposal:
    def test_create_proposal(self):
        p = Proposal(proposal_id="p1", tier="Growth", client_name="Hotel Teste")
        assert p.proposal_id == "p1"
        assert p.tier == "Growth"
        assert p.client_name == "Hotel Teste"
        assert p.dry_run is True

    def test_expiration_auto_set(self):
        p = Proposal(proposal_id="p2", expiration_days=15)
        assert p.expires_at != ""

    def test_to_dict_roundtrip(self):
        p = Proposal(
            proposal_id="p3",
            lead_id="l1",
            deal_id="d1",
            client_name="Resort Costa Azul",
            tier=ProposalTier.PREMIUM.value,
            price="R$ 1.200",
            scope=["4 collabs", "3+ perfis", "SEOgram + stories"],
        )
        d = p.to_dict()
        restored = Proposal.from_dict(d)
        assert restored.proposal_id == "p3"
        assert restored.client_name == "Resort Costa Azul"
        assert restored.price == "R$ 1.200"

    def test_to_markdown(self):
        p = Proposal(proposal_id="p4", tier="Starter", client_name="Pousada Sol",
                     price="R$ 350", scope=["1 collab"])
        md = p.to_markdown()
        assert "Proposta Comercial" in md
        assert "p4" in md
        assert "Pousada Sol" in md
        assert "Starter" in md

    def test_to_json(self):
        p = Proposal(proposal_id="p5", tier="Growth", client_name="Test")
        j = p.to_json()
        assert "p5" in j
        assert "Growth" in j

    def test_to_pdf_placeholder(self):
        p = Proposal(proposal_id="p6", tier="Starter", client_company="Hotel X")
        placeholder = p.to_pdf_placeholder()
        assert placeholder["format"] == "pdf_placeholder"
        assert "Hotel X" in placeholder["title"]

    def test_dry_run_default(self):
        p = Proposal(proposal_id="p7")
        assert p.dry_run is True


class TestProposalGenerator:
    def setup_method(self):
        self.generator = ProposalGenerator()

    def test_generate_starter(self):
        p = self.generator.generate(
            tier=ProposalTier.STARTER.value,
            client_name="Hotel Econômico",
            lead_id="l1",
        )
        assert p.tier == "Starter"
        assert p.price == "R$ 350"
        assert len(p.scope) == 3
        assert p.client_name == "Hotel Econômico"

    def test_generate_growth(self):
        p = self.generator.generate(
            tier=ProposalTier.GROWTH.value,
            client_name="Resort Premium",
            lead_id="l2",
            deal_id="d2",
        )
        assert p.tier == "Growth"
        assert p.price == "R$ 990/mês"
        assert len(p.scope) == 4
        assert p.deal_id == "d2"

    def test_generate_premium(self):
        p = self.generator.generate(
            tier=ProposalTier.PREMIUM.value,
            client_name="Grande Rede Hoteleira",
        )
        assert p.tier == "Premium"
        assert p.price == "R$ 1.200"
        assert len(p.scope) == 4

    def test_generate_all_tiers(self):
        proposals = self.generator.generate_all_tiers(client_name="Hotel Teste")
        assert len(proposals) == 3
        tiers = {p.tier for p in proposals}
        assert "Starter" in tiers
        assert "Growth" in tiers
        assert "Premium" in tiers

    def test_no_email_send(self):
        p = self.generator.generate(tier="Growth", client_name="Test")
        assert p.dry_run is True
        # No email, no API, no external call — markdown/json only

    def test_pdf_is_placeholder(self):
        p = self.generator.generate(tier="Growth", client_name="Test")
        placeholder = p.to_pdf_placeholder()
        assert "placeholder" in placeholder["format"]

    def test_custom_offer(self):
        p = self.generator.generate(
            tier="Premium",
            client_name="Test",
            offer="Oferta customizada com stories extras",
        )
        assert "customizada" in p.offer
