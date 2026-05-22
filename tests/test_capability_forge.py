"""Tests for Capability Forge MVP (proposal-only)."""
import pytest
from pathlib import Path
from src.capability_forge_real.models import (
    CreationContext, CreationState, SkillSpec, RegistryEntry
)
from src.capability_forge_real.lifecycle import transition, InvalidCreationTransitionError
from src.capability_forge_real.policy import PolicyEngine, PolicyReport
from src.capability_forge_real.registrymanager import RegistryManager
from src.capability_forge_real.orchestrator import CapabilityForge


class TestModels:
    def test_creation_context_defaults(self):
        ctx = CreationContext(gap_description="test", sector="marketing")
        assert ctx.state == CreationState.DISCOVERY
        assert ctx.errors == []

    def test_skill_spec_defaults(self):
        spec = SkillSpec(name="test", sector="sales", description="a skill")
        assert spec.risk_level == "low"

    def test_registry_entry_defaults(self):
        entry = RegistryEntry(id="1", name="test")
        assert entry.version == "0.1.0"
        assert entry.status == "generated"


class TestLifecycle:
    def test_valid_transition(self):
        ctx = CreationContext(gap_description="test", sector="test")
        assert ctx.state == CreationState.DISCOVERY
        ctx = transition(ctx, "gap_confirmed")
        assert ctx.state == CreationState.GAP_CONFIRMED

    def test_invalid_transition_raises(self):
        ctx = CreationContext(gap_description="test", sector="test")
        ctx.state = CreationState.APPROVED
        with pytest.raises(InvalidCreationTransitionError):
            transition(ctx, "build")


class TestPolicyEngine:
    def test_check_safe_file(self, tmp_path):
        safe = tmp_path / "safe.py"
        safe.write_text("x = 1\ny = x + 1\nprint(y)")
        engine = PolicyEngine()
        report = engine.check_file(safe)
        assert report.passed is True

    def test_check_forbidden_import(self, tmp_path):
        bad = tmp_path / "bad.py"
        bad.write_text("import subprocess\nsubprocess.run(['ls'])")
        engine = PolicyEngine()
        report = engine.check_file(bad)
        assert report.passed is False

    def test_check_missing_file(self, tmp_path):
        engine = PolicyEngine()
        report = engine.check_file(tmp_path / "nonexistent.py")
        assert report.passed is False


class TestRegistryManager:
    def test_add_and_get(self, tmp_path):
        reg = RegistryManager(registry_path=tmp_path / "registry.jsonl")
        entry = RegistryEntry(id="1", name="test-skill", description="test")
        reg.add(entry)
        result = reg.get("test-skill")
        assert result is not None
        assert result["name"] == "test-skill"

    def test_add_duplicate_raises(self, tmp_path):
        reg = RegistryManager(registry_path=tmp_path / "registry.jsonl")
        entry = RegistryEntry(id="1", name="test-skill")
        reg.add(entry)
        with pytest.raises(ValueError):
            reg.add(entry)

    def test_search(self, tmp_path):
        reg = RegistryManager(registry_path=tmp_path / "registry.jsonl")
        reg.add(RegistryEntry(id="1", name="skill-one", tags=["tag1"]))
        reg.add(RegistryEntry(id="2", name="skill-two", tags=["tag2"]))
        results = reg.search("one")
        assert len(results) == 1


class TestOrchestrator:
    @pytest.mark.asyncio
    async def test_propose_skill(self):
        forge = CapabilityForge()
        result = await forge.propose_skill(
            gap_description="Preciso de uma skill para gerar relatorios semanais",
            sector="operations",
            requested_name="weekly-report",
        )
        assert result["state"] in ("SPEC_READY", "DUPLICATE_FOUND")
        if result["state"] == "SPEC_READY":
            assert "report_path" in result

    @pytest.mark.asyncio
    async def test_build_skill_not_implemented(self):
        forge = CapabilityForge()
        with pytest.raises(NotImplementedError):
            await forge.build_skill({"name": "test"}, "sales")
