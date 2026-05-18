"""Tests for SquadSelector — squad selection, assignment, capabilities."""
from __future__ import annotations

import pytest

from src.agentic.squad_selector import (
    SquadSelector,
    SquadDefinition,
    SquadMember,
    SquadAssignment,
    _SQUADS,
    _FALLBACK_SQUAD,
)


@pytest.fixture
def selector():
    return SquadSelector()


# ── SquadMember ────────────────────────────────────────────────────────

class TestSquadMember:
    def test_to_dict(self):
        m = SquadMember(role="Tester", skill_id="s1", intent="analyze", primary=True)
        d = m.to_dict()
        assert d["role"] == "Tester"
        assert d["skill_id"] == "s1"
        assert d["primary"] is True


# ── SquadDefinition ────────────────────────────────────────────────────

class TestSquadDefinition:
    def test_primary_member_first_primary(self):
        squad = SquadDefinition(
            squad_id="SQD-01", name="Test", sector="sales",
            description="x",
            members=[
                SquadMember(role="A", skill_id="a", intent="read", primary=False),
                SquadMember(role="B", skill_id="b", intent="create", primary=True),
                SquadMember(role="C", skill_id="c", intent="analyze", primary=False),
            ],
        )
        assert squad.primary_member is not None
        assert squad.primary_member.role == "B"

    def test_primary_member_fallback_to_first(self):
        squad = SquadDefinition(
            squad_id="SQD-02", name="Test", sector="general",
            description="x",
            members=[
                SquadMember(role="First", skill_id="f1", intent="read"),
            ],
        )
        assert squad.primary_member is not None
        assert squad.primary_member.role == "First"

    def test_primary_member_empty_returns_none(self):
        squad = SquadDefinition(
            squad_id="SQD-03", name="Empty", sector="general",
            description="x", members=[],
        )
        assert squad.primary_member is None

    def test_to_dict(self):
        squad = _SQUADS["marketing"]
        d = squad.to_dict()
        assert d["squad_id"] == "SQD-MKT"
        assert len(d["members"]) == 4


# ── SquadAssignment ────────────────────────────────────────────────────

class TestSquadAssignment:
    def test_to_dict(self, selector):
        assignment = selector.assign("MIS-001", "marketing")
        d = assignment.to_dict()
        assert d["mission_id"] == "MIS-001"
        assert d["squad"]["squad_id"] == "SQD-MKT"


# ── select ─────────────────────────────────────────────────────────────

class TestSelect:
    def test_marketing_selects_marketing_squad(self, selector):
        squad = selector.select("marketing")
        assert squad.squad_id == "SQD-MKT"
        assert squad.name == "Marketing Squad"

    def test_sales_selects_sales_squad(self, selector):
        squad = selector.select("sales")
        assert squad.squad_id == "SQD-SALES"

    def test_app_factory_selects_app_factory_squad(self, selector):
        squad = selector.select("app_factory")
        assert squad.squad_id == "SQD-APP"

    def test_computer_ops_selects_computer_ops_squad(self, selector):
        squad = selector.select("computer_ops")
        assert squad.squad_id == "SQD-OPS"

    def test_unknown_sector_falls_back(self, selector):
        squad = selector.select("unknown_sector")
        assert squad.squad_id == "SQD-GEN"
        assert squad.sector == "general"

    def test_general_falls_back(self, selector):
        squad = selector.select("general")
        assert squad.squad_id == "SQD-GEN"


# ── assign ─────────────────────────────────────────────────────────────

class TestAssign:
    def test_assign_includes_reason(self, selector):
        assignment = selector.assign("MIS-MKT-001", "marketing")
        assert "marketing" in assignment.reason.lower()
        assert "SQD-MKT" in assignment.reason or assignment.squad.squad_id == "SQD-MKT"

    def test_assign_sets_timestamp(self, selector):
        assignment = selector.assign("MIS-001", "sales")
        assert assignment.assembled_at != ""


# ── list_all ───────────────────────────────────────────────────────────

class TestListAll:
    def test_returns_4_squads(self, selector):
        squads = selector.list_all()
        assert len(squads) == 4

    def test_all_have_members(self, selector):
        for squad in selector.list_all():
            assert len(squad.members) > 0


# ── capabilities and exports ───────────────────────────────────────────

class TestCapabilities:
    def test_marketing_capabilities(self, selector):
        caps = selector.get_capabilities("marketing")
        assert len(caps) == 4

    def test_marketing_exports(self, selector):
        fmts = selector.get_export_formats("marketing")
        assert "csv" in fmts

    def test_app_factory_exports_zip(self, selector):
        fmts = selector.get_export_formats("app_factory")
        assert "zip" in fmts


# ── available_sectors ──────────────────────────────────────────────────

def test_available_sectors(selector):
    sectors = selector.available_sectors
    assert "marketing" in sectors
    assert "sales" in sectors
    assert "app_factory" in sectors
    assert "computer_ops" in sectors


# ── squad definitions integrity ────────────────────────────────────────

class TestSquadIntegrity:
    def test_all_squads_have_ids(self):
        for s in _SQUADS.values():
            assert s.squad_id.startswith("SQD-")

    def test_marketing_has_4_members(self):
        assert len(_SQUADS["marketing"].members) == 4

    def test_sales_has_4_members(self):
        assert len(_SQUADS["sales"].members) == 4

    def test_app_factory_has_4_members(self):
        assert len(_SQUADS["app_factory"].members) == 4

    def test_computer_ops_has_4_members(self):
        assert len(_SQUADS["computer_ops"].members) == 4

    def test_every_squad_has_one_primary(self):
        for s in _SQUADS.values():
            primary_count = sum(1 for m in s.members if m.primary)
            assert primary_count == 1, f"{s.squad_id} has {primary_count} primary members"

    def test_marketing_squad_has_publisher(self):
        mkt = _SQUADS["marketing"]
        roles = [m.role for m in mkt.members]
        assert any("Publisher" in r for r in roles)

    def test_sales_squad_has_lead_qualifier(self):
        sales = _SQUADS["sales"]
        roles = [m.role for m in sales.members]
        assert any("Lead" in r for r in roles)
