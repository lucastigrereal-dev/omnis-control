"""Onda 9 FIO 3 — skill activation: planned→active in SkillCatalog."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from src.capability_forge_real.activator import activate_capability, capability_to_skill_definition
from src.capability_forge_real.builder import CapabilityBuilder
from src.capability_forge_real.models import (
    CapabilityProposal,
    PROPOSAL_STATUS_APPROVED,
    IMPL_TYPE_CLI_WRAPPER,
    IMPL_TYPE_MANUAL_PROCESS,
)
from src.skills_bridge.models import SkillDefinition, SkillRisk
from src.skills_bridge.skill_catalog import SkillCatalog


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def caps_yaml(tmp_path) -> Path:
    """A minimal capabilities.yaml with one planned capability."""
    p = tmp_path / "capabilities.yaml"
    data = {
        "capabilities": {
            "hotel_lead_scorer": {
                "sector": "comercial",
                "output": "Scores hotel leads by engagement potential",
                "risk_level": "low",
                "status": "planned",
                "implementation_type": "cli_wrapper",
                "proposal_id": "prop_abc12345",
                "keywords": ["hotel", "lead", "scoring"],
            }
        }
    }
    p.write_text(yaml.dump(data, allow_unicode=True), encoding="utf-8")
    return p


@pytest.fixture
def skills_json(tmp_path) -> Path:
    """An empty skills.json catalog."""
    p = tmp_path / "skills.json"
    p.write_text(json.dumps({"skills": []}), encoding="utf-8")
    return p


@pytest.fixture
def approved_cli_proposal():
    p = CapabilityProposal.from_gap(
        gap_id="gap_fio3_001",
        capability_name="hotel_lead_scorer",
        sector="comercial",
        desired_output="Scores hotel leads by engagement potential",
        risk_level="low",
        implementation_type=IMPL_TYPE_CLI_WRAPPER,
    )
    p.status = PROPOSAL_STATUS_APPROVED
    return p


# ── SkillDefinition.status ────────────────────────────────────────────────────

class TestSkillDefinitionStatus:
    def test_default_status_is_active(self):
        sd = SkillDefinition()
        assert sd.status == "active"

    def test_status_in_to_dict(self):
        sd = SkillDefinition(skill_id="x", name="X")
        d = sd.to_dict()
        assert d["status"] == "active"

    def test_status_from_dict_planned(self):
        sd = SkillDefinition.from_dict({"skill_id": "x", "name": "X", "status": "planned"})
        assert sd.status == "planned"

    def test_status_from_dict_defaults_active(self):
        sd = SkillDefinition.from_dict({"skill_id": "x", "name": "X"})
        assert sd.status == "active"


# ── SkillCatalog.activate_skill ───────────────────────────────────────────────

class TestSkillCatalogActivateSkill:
    def test_activate_skill_sets_active(self):
        catalog = SkillCatalog()
        skill = SkillDefinition(skill_id="my_skill", status="planned")
        catalog.add_skill(skill)
        result = catalog.activate_skill("my_skill")
        assert result is True
        assert catalog._skills["my_skill"].status == "active"

    def test_activate_unknown_skill_returns_false(self):
        catalog = SkillCatalog()
        assert catalog.activate_skill("nonexistent") is False

    def test_write_skill_appends_to_json(self, skills_json):
        catalog = SkillCatalog(catalog_path=str(skills_json))
        skill = SkillDefinition(skill_id="new_skill", name="New Skill", status="active")
        catalog.write_skill(skill)
        data = json.loads(skills_json.read_text())
        ids = [s["skill_id"] for s in data["skills"]]
        assert "new_skill" in ids

    def test_write_skill_no_duplicate(self, skills_json):
        catalog = SkillCatalog(catalog_path=str(skills_json))
        skill = SkillDefinition(skill_id="new_skill", name="New Skill")
        catalog.write_skill(skill)
        catalog.write_skill(skill)
        data = json.loads(skills_json.read_text())
        assert len([s for s in data["skills"] if s["skill_id"] == "new_skill"]) == 1

    def test_write_skill_noop_without_path(self):
        catalog = SkillCatalog()
        skill = SkillDefinition(skill_id="phantom", name="Phantom")
        catalog.write_skill(skill)


# ── capability_to_skill_definition ───────────────────────────────────────────

class TestCapabilityToSkillDefinition:
    def test_basic_conversion(self, caps_yaml):
        raw = yaml.safe_load(caps_yaml.read_text())
        cap_data = raw["capabilities"]["hotel_lead_scorer"]
        skill = capability_to_skill_definition("hotel_lead_scorer", cap_data)
        assert skill.skill_id == "hotel_lead_scorer"
        assert skill.description == "Scores hotel leads by engagement potential"
        assert skill.tier == "generated"
        assert skill.status == "active"
        assert skill.category == "comercial"

    def test_tags_from_keywords(self, caps_yaml):
        raw = yaml.safe_load(caps_yaml.read_text())
        cap_data = raw["capabilities"]["hotel_lead_scorer"]
        skill = capability_to_skill_definition("hotel_lead_scorer", cap_data)
        assert "hotel" in skill.tags

    def test_risk_mapping_low(self, caps_yaml):
        raw = yaml.safe_load(caps_yaml.read_text())
        cap_data = raw["capabilities"]["hotel_lead_scorer"]
        skill = capability_to_skill_definition("hotel_lead_scorer", cap_data)
        assert skill.risk == SkillRisk.LOW
        assert skill.requires_approval is False


# ── activate_capability ───────────────────────────────────────────────────────

class TestActivateCapability:
    def test_returns_none_for_missing_yaml(self, tmp_path):
        result = activate_capability("x", caps_path=tmp_path / "nope.yaml")
        assert result is None

    def test_returns_none_for_unknown_cap_id(self, caps_yaml):
        result = activate_capability("unknown_cap", caps_path=caps_yaml)
        assert result is None

    def test_dry_run_returns_skill_def(self, caps_yaml):
        skill = activate_capability("hotel_lead_scorer", caps_path=caps_yaml, dry_run=True)
        assert isinstance(skill, SkillDefinition)
        assert skill.skill_id == "hotel_lead_scorer"
        assert skill.status == "active"

    def test_dry_run_does_not_flip_yaml(self, caps_yaml):
        activate_capability("hotel_lead_scorer", caps_path=caps_yaml, dry_run=True)
        raw = yaml.safe_load(caps_yaml.read_text())
        assert raw["capabilities"]["hotel_lead_scorer"]["status"] == "planned"

    def test_real_run_flips_yaml_status(self, caps_yaml, skills_json):
        activate_capability(
            "hotel_lead_scorer",
            caps_path=caps_yaml,
            catalog_path=skills_json,
            dry_run=False,
        )
        raw = yaml.safe_load(caps_yaml.read_text())
        assert raw["capabilities"]["hotel_lead_scorer"]["status"] == "active"

    def test_real_run_writes_to_catalog(self, caps_yaml, skills_json):
        activate_capability(
            "hotel_lead_scorer",
            caps_path=caps_yaml,
            catalog_path=skills_json,
            dry_run=False,
        )
        data = json.loads(skills_json.read_text())
        ids = [s["skill_id"] for s in data["skills"]]
        assert "hotel_lead_scorer" in ids

    def test_real_run_catalog_skill_status_is_active(self, caps_yaml, skills_json):
        activate_capability(
            "hotel_lead_scorer",
            caps_path=caps_yaml,
            catalog_path=skills_json,
            dry_run=False,
        )
        data = json.loads(skills_json.read_text())
        skill = next(s for s in data["skills"] if s["skill_id"] == "hotel_lead_scorer")
        assert skill["status"] == "active"


# ── Builder integration ───────────────────────────────────────────────────────

class TestBuilderActivation:
    def test_build_done_sets_activated_skill_id(self, approved_cli_proposal):
        builder = CapabilityBuilder(dry_run=True)
        result = builder.build(approved_cli_proposal)
        assert result.activated_skill_id == "hotel_lead_scorer"

    def test_activated_skill_id_in_to_dict(self, approved_cli_proposal):
        builder = CapabilityBuilder(dry_run=True)
        result = builder.build(approved_cli_proposal)
        d = result.to_dict()
        assert d["activated_skill_id"] == "hotel_lead_scorer"

    def test_activated_skill_id_round_trip(self, approved_cli_proposal):
        builder = CapabilityBuilder(dry_run=True)
        result = builder.build(approved_cli_proposal)
        restored = type(result).from_dict(result.to_dict())
        assert restored.activated_skill_id == result.activated_skill_id

    def test_score_failed_has_no_activated_skill_id(
        self, approved_cli_proposal, monkeypatch
    ):
        from src.capability_forge_real.sandbox import SandboxResult, SandboxStatus
        import src.capability_forge_real.builder as builder_mod

        def blocked(self_inner, code, run_id=""):
            return SandboxResult(
                run_id=run_id,
                status=SandboxStatus.BLOCKED,
                blocked_patterns=["subprocess"],
            )

        monkeypatch.setattr(builder_mod.SandboxRunner, "dry_run_validate", blocked)
        builder = CapabilityBuilder(dry_run=True)
        result = builder.build(approved_cli_proposal)
        assert result.activated_skill_id is None
