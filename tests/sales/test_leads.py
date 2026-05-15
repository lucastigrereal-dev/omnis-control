"""Tests for W111 — Lead model + LeadRegistry."""
from __future__ import annotations

import pytest
import tempfile
from pathlib import Path

from src.sales.leads import Lead, LeadRegistry


class TestLead:
    def test_create_lead_minimal(self):
        lead = Lead(lead_id="l1", name="Hotel Serra Azul")
        assert lead.lead_id == "l1"
        assert lead.name == "Hotel Serra Azul"
        assert lead.status == "novo"
        assert lead.dry_run is True
        assert lead.score == 0

    def test_create_lead_full(self):
        lead = Lead(
            lead_id="l2",
            name="Restaurante Mar Azul",
            company="Mar Azul Ltda",
            contact_channel="instagram",
            source="indicacao",
            segment="restaurante",
            interest="collab",
            tags=["gastronomia", "praia"],
            score=75,
        )
        assert lead.company == "Mar Azul Ltda"
        assert lead.segment == "restaurante"
        assert "gastronomia" in lead.tags
        assert lead.score == 75

    def test_to_dict_roundtrip(self):
        lead = Lead(
            lead_id="l3",
            name="Agência Turismo Total",
            company="Turismo Total SA",
            contact_channel="whatsapp",
            source="prospeccao",
            segment="agencia",
            tags=["turismo", "nordeste"],
            score=60,
        )
        d = lead.to_dict()
        restored = Lead.from_dict(d)
        assert restored.lead_id == "l3"
        assert restored.name == "Agência Turismo Total"
        assert restored.company == "Turismo Total SA"
        assert restored.tags == ["turismo", "nordeste"]

    def test_to_markdown(self):
        lead = Lead(lead_id="l4", name="Pousada Sol", company="Sol RN", tags=["praia"])
        md = lead.to_markdown()
        assert "Pousada Sol" in md
        assert "l4" in md
        assert "praia" in md

    def test_touch_updates_timestamp(self):
        import time
        lead = Lead(lead_id="l5", name="Test")
        old = lead.updated_at
        time.sleep(0.01)
        lead.touch()
        assert lead.updated_at != old

    def test_dry_run_default(self):
        lead = Lead(lead_id="l6", name="Test")
        assert lead.dry_run is True

    def test_no_real_contact_stored(self):
        lead = Lead(lead_id="l7", name="Test", contact_value="mock_contact_123")
        assert lead.contact_value == "mock_contact_123"


class TestLeadRegistry:
    def test_create_and_get(self):
        registry = LeadRegistry()
        lead = registry.create(name="Hotel Teste")
        assert registry.count == 1
        fetched = registry.get(lead.lead_id)
        assert fetched is not None
        assert fetched.name == "Hotel Teste"

    def test_create_multiple(self):
        registry = LeadRegistry()
        registry.create(name="Lead 1")
        registry.create(name="Lead 2")
        registry.create(name="Lead 3")
        assert registry.count == 3

    def test_list_all(self):
        registry = LeadRegistry()
        registry.create(name="A")
        registry.create(name="B")
        assert len(registry.list_all()) == 2

    def test_list_by_status(self):
        registry = LeadRegistry()
        registry.create(name="Active")
        lead = registry.create(name="Qualified")
        registry.update(lead.lead_id, status="qualificado")
        qualified = registry.list_by_status("qualificado")
        assert len(qualified) == 1
        assert qualified[0].name == "Qualified"

    def test_list_by_segment(self):
        registry = LeadRegistry()
        registry.create(name="Hotel 1", segment="hotel")
        registry.create(name="Rest 1", segment="restaurante")
        assert len(registry.list_by_segment("hotel")) == 1
        assert len(registry.list_by_segment("restaurante")) == 1

    def test_list_by_source(self):
        registry = LeadRegistry()
        registry.create(name="Lead A", source="instagram")
        registry.create(name="Lead B", source="indicacao")
        assert len(registry.list_by_source("instagram")) == 1

    def test_update_lead(self):
        registry = LeadRegistry()
        lead = registry.create(name="Old Name")
        updated = registry.update(lead.lead_id, name="New Name", score=80)
        assert updated is not None
        assert updated.name == "New Name"
        assert updated.score == 80

    def test_update_nonexistent(self):
        registry = LeadRegistry()
        result = registry.update("nonexistent", name="X")
        assert result is None

    def test_delete_lead(self):
        registry = LeadRegistry()
        lead = registry.create(name="To Delete")
        assert registry.count == 1
        assert registry.delete(lead.lead_id) is True
        assert registry.count == 0
        assert registry.get(lead.lead_id) is None

    def test_delete_nonexistent(self):
        registry = LeadRegistry()
        assert registry.delete("nonexistent") is False

    def test_file_backed_save_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            # Save
            reg1 = LeadRegistry(storage_dir=tmp)
            reg1.create(name="File Lead 1", company="Co 1")
            reg1.create(name="File Lead 2", company="Co 2")
            assert reg1.count == 2

            # Load
            reg2 = LeadRegistry.load(tmp)
            assert reg2.count == 2
            names = {l.name for l in reg2.list_all()}
            assert "File Lead 1" in names
            assert "File Lead 2" in names

    def test_to_jsonl(self):
        registry = LeadRegistry()
        registry.create(name="JSONL Test")
        jsonl = registry.to_jsonl()
        assert "JSONL Test" in jsonl
        assert "lead_id" in jsonl

    def test_no_external_calls(self):
        registry = LeadRegistry()
        lead = registry.create(name="Safe Lead")
        assert lead.dry_run is True
        assert lead.contact_value == ""
        # Zero network, zero env, zero API
