"""Tests for P22 Capability Forge Real models."""
from __future__ import annotations

import pytest

from src.capability_forge_real.models import (
    BuildResult,
    BuildState,
    SkillTemplateConfig,
    TERMINAL_STATES,
    _new_id,
    _now_iso,
)
from src.capability_forge_real.errors import (
    ForgeRealError,
    BuildError,
    ScaffoldError,
    PolicyScanError,
    TestGenerationError,
    RegistrationError,
    RollbackError,
)
from src.capability_forge_real.models import (
    CapabilityProposal,
    IMPL_TYPE_CLI_WRAPPER,
    IMPL_TYPE_MANUAL_PROCESS,
    IMPL_TYPE_OFFLINE_PACKAGE,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_proposal():
    return CapabilityProposal.from_gap(
        gap_id="gap_001",
        capability_name="test_skill",
        sector="midia",
        desired_output="A test skill output",
        risk_level="medium",
        implementation_type=IMPL_TYPE_CLI_WRAPPER,
    )


# ── ID and timestamp helpers ─────────────────────────────────────────────────

class TestHelpers:
    def test_new_id_has_prefix(self):
        result = _new_id("bld")
        assert result.startswith("bld_")
        assert len(result) == 12

    def test_new_ids_are_unique(self):
        ids = {_new_id("bld") for _ in range(100)}
        assert len(ids) == 100

    def test_now_iso_format(self):
        result = _now_iso()
        assert "T" in result
        assert result.endswith("Z")


# ── BuildState enum ──────────────────────────────────────────────────────────

class TestBuildState:
    def test_all_states_exist(self):
        assert BuildState.PROPOSAL_APPROVED.value == "proposal_approved"
        assert BuildState.SCAFFOLDING.value == "scaffolding"
        assert BuildState.POLICY_SCANNING.value == "policy_scanning"
        assert BuildState.TEST_GENERATING.value == "test_generating"
        assert BuildState.VALIDATING.value == "validating"
        assert BuildState.REGISTERING.value == "registering"
        assert BuildState.DONE.value == "done"
        assert BuildState.POLICY_FAILED.value == "policy_failed"
        assert BuildState.TEST_FAILED.value == "test_failed"

    def test_nine_states(self):
        assert len(BuildState) == 9

    def test_terminal_states_correct(self):
        assert BuildState.DONE in TERMINAL_STATES
        assert BuildState.POLICY_FAILED in TERMINAL_STATES
        assert BuildState.TEST_FAILED in TERMINAL_STATES
        assert BuildState.SCAFFOLDING not in TERMINAL_STATES


# ── BuildResult ──────────────────────────────────────────────────────────────

class TestBuildResult:
    def test_new_creates_result(self, sample_proposal):
        result = BuildResult.new(sample_proposal)
        assert result.build_id.startswith("bld_")
        assert result.dry_run is True

    def test_new_respects_dry_run(self, sample_proposal):
        result = BuildResult.new(sample_proposal, dry_run=False)
        assert result.dry_run is False

    def test_initial_state_proposal_approved(self, sample_proposal):
        result = BuildResult.new(sample_proposal)
        assert result.state == BuildState.PROPOSAL_APPROVED.value

    def test_is_terminal_false_initially(self, sample_proposal):
        result = BuildResult.new(sample_proposal)
        assert result.is_terminal is False

    def test_is_success_false_initially(self, sample_proposal):
        result = BuildResult.new(sample_proposal)
        assert result.is_success is False

    def test_transition_valid(self, sample_proposal):
        result = BuildResult.new(sample_proposal)
        result.transition(BuildState.SCAFFOLDING)
        assert result.state == BuildState.SCAFFOLDING.value

    def test_transition_invalid_raises(self, sample_proposal):
        result = BuildResult.new(sample_proposal)
        with pytest.raises(ValueError, match="Transicao invalida"):
            result.transition(BuildState.DONE)

    def test_full_happy_path(self, sample_proposal):
        result = BuildResult.new(sample_proposal)
        result.transition(BuildState.SCAFFOLDING)
        result.transition(BuildState.POLICY_SCANNING)
        result.transition(BuildState.TEST_GENERATING)
        result.transition(BuildState.VALIDATING)
        result.transition(BuildState.REGISTERING)
        result.transition(BuildState.DONE)
        assert result.is_terminal is True
        assert result.is_success is True

    def test_policy_failure_path(self, sample_proposal):
        result = BuildResult.new(sample_proposal)
        result.transition(BuildState.SCAFFOLDING)
        result.transition(BuildState.POLICY_SCANNING)
        result.transition(BuildState.POLICY_FAILED)
        assert result.is_terminal is True
        assert result.is_success is False

    def test_test_failure_path(self, sample_proposal):
        result = BuildResult.new(sample_proposal)
        result.transition(BuildState.SCAFFOLDING)
        result.transition(BuildState.POLICY_SCANNING)
        result.transition(BuildState.TEST_GENERATING)
        result.transition(BuildState.VALIDATING)
        result.transition(BuildState.TEST_FAILED)
        assert result.is_terminal is True
        assert result.is_success is False

    def test_cannot_transition_from_terminal(self, sample_proposal):
        result = BuildResult.new(sample_proposal)
        result.state = BuildState.DONE.value
        with pytest.raises(ValueError, match="Transicao invalida"):
            result.transition(BuildState.SCAFFOLDING)

    def test_to_dict_roundtrip(self, sample_proposal):
        result = BuildResult.new(sample_proposal)
        result.files_created = ["src/skills/test_skill/run.py"]
        result.test_count = 3
        data = result.to_dict()
        restored = BuildResult.from_dict(data)
        assert restored.build_id == result.build_id
        assert restored.files_created == result.files_created
        assert restored.test_count == 3

    def test_policy_scan_default(self, sample_proposal):
        result = BuildResult.new(sample_proposal)
        assert result.policy_scan["passed"] is True
        assert result.policy_scan["violations"] == []


# ── SkillTemplateConfig ─────────────────────────────────────────────────────

class TestSkillTemplateConfig:
    def test_new_creates_config(self):
        cfg = SkillTemplateConfig.new(
            implementation_type=IMPL_TYPE_CLI_WRAPPER,
            target_dir="skills/test_skill",
        )
        assert cfg.template_id.startswith("tpl_")
        assert cfg.implementation_type == IMPL_TYPE_CLI_WRAPPER

    def test_defaults(self):
        cfg = SkillTemplateConfig.new(
            implementation_type=IMPL_TYPE_MANUAL_PROCESS,
            target_dir="processes/test",
        )
        assert cfg.filename == "run.py"
        assert cfg.test_filename == "test_run.py"
        assert cfg.min_tests == 3
        assert cfg.class_prefix == ""

    def test_custom_values(self):
        cfg = SkillTemplateConfig.new(
            implementation_type=IMPL_TYPE_OFFLINE_PACKAGE,
            target_dir="offline_factory/test_pkg",
            filename="main.py",
            class_prefix="TestPkg",
            test_dir="offline_factory/test_pkg",
            min_tests=5,
        )
        assert cfg.filename == "main.py"
        assert cfg.class_prefix == "TestPkg"
        assert cfg.min_tests == 5

    def test_to_dict_roundtrip(self):
        cfg = SkillTemplateConfig.new(
            implementation_type=IMPL_TYPE_CLI_WRAPPER,
            target_dir="skills/demo",
            class_prefix="Demo",
        )
        data = cfg.to_dict()
        restored = SkillTemplateConfig.from_dict(data)
        assert restored.template_id == cfg.template_id
        assert restored.target_dir == cfg.target_dir
        assert restored.class_prefix == cfg.class_prefix


# ── Errors ───────────────────────────────────────────────────────────────────

class TestErrors:
    def test_forge_real_error_base(self):
        with pytest.raises(ForgeRealError):
            raise ForgeRealError("base")

    def test_build_error(self):
        with pytest.raises(BuildError):
            raise BuildError("build failed")

    def test_scaffold_error_chain(self):
        with pytest.raises(ScaffoldError):
            raise ScaffoldError("scaffold failed")
        assert issubclass(ScaffoldError, BuildError)

    def test_policy_scan_error_chain(self):
        assert issubclass(PolicyScanError, BuildError)

    def test_test_gen_error_chain(self):
        assert issubclass(TestGenerationError, BuildError)

    def test_all_extend_forge_real_error(self):
        assert issubclass(BuildError, ForgeRealError)
        assert issubclass(RegistrationError, ForgeRealError)
        assert issubclass(RollbackError, ForgeRealError)
