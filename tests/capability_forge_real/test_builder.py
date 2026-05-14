"""Tests for P22 Capability Builder."""
from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.capability_forge_real.builder import CapabilityBuilder
from src.capability_forge_real.models import BuildResult, BuildState
from src.capability_forge_real.errors import BuildError, ScaffoldError
from src.capability_forge_lite.models import (
    CapabilityProposal,
    PROPOSAL_STATUS_APPROVED,
    PROPOSAL_STATUS_DRAFT,
    IMPL_TYPE_CLI_WRAPPER,
    IMPL_TYPE_OFFLINE_PACKAGE,
    IMPL_TYPE_MANUAL_PROCESS,
    IMPL_TYPE_EXTERNAL_FUTURE,
    IMPL_TYPE_APP_FACTORY_FUTURE,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def builder():
    return CapabilityBuilder(dry_run=True)


@pytest.fixture
def approved_cli_proposal():
    p = CapabilityProposal.from_gap(
        gap_id="gap_001",
        capability_name="test_cli_skill",
        sector="midia",
        desired_output="A test skill",
        risk_level="medium",
        implementation_type=IMPL_TYPE_CLI_WRAPPER,
    )
    p.status = PROPOSAL_STATUS_APPROVED
    return p


@pytest.fixture
def approved_offline_proposal():
    p = CapabilityProposal.from_gap(
        gap_id="gap_002",
        capability_name="test_offline_pkg",
        sector="produto",
        desired_output="An offline package",
        implementation_type=IMPL_TYPE_OFFLINE_PACKAGE,
    )
    p.status = PROPOSAL_STATUS_APPROVED
    return p


@pytest.fixture
def approved_manual_proposal():
    p = CapabilityProposal.from_gap(
        gap_id="gap_003",
        capability_name="manual_process_test",
        sector="operacoes",
        desired_output="Manual SOP",
        implementation_type=IMPL_TYPE_MANUAL_PROCESS,
    )
    p.status = PROPOSAL_STATUS_APPROVED
    return p


# ── Initialization ──────────────────────────────────────────────────────────

class TestCapabilityBuilderInit:
    def test_default_dry_run_true(self):
        builder = CapabilityBuilder()
        assert builder.dry_run is True

    def test_explicit_dry_run_false(self):
        builder = CapabilityBuilder(dry_run=False)
        assert builder.dry_run is False


# ── Build: Validation ───────────────────────────────────────────────────────

class TestBuildValidation:
    def test_unapproved_proposal_raises(self, builder):
        p = CapabilityProposal.from_gap(
            gap_id="gap_001",
            capability_name="test",
            sector="midia",
            desired_output="output",
            implementation_type=IMPL_TYPE_CLI_WRAPPER,
        )
        with pytest.raises(BuildError, match="nao esta aprovada"):
            builder.build(p)

    def test_approved_proposal_proceeds(self, builder, approved_cli_proposal):
        result = builder.build(approved_cli_proposal)
        assert isinstance(result, BuildResult)


# ── Build: CLI Wrapper ──────────────────────────────────────────────────────

class TestBuildCliWrapper:
    def test_build_cli_completes(self, builder, approved_cli_proposal):
        result = builder.build(approved_cli_proposal)
        assert result.state == BuildState.DONE.value
        assert result.is_success is True

    def test_build_cli_dry_run_no_files_on_disk(self, builder, approved_cli_proposal):
        result = builder.build(approved_cli_proposal)
        for f in result.files_created:
            assert not Path(f).exists()

    def test_build_cli_has_files_created(self, builder, approved_cli_proposal):
        result = builder.build(approved_cli_proposal)
        assert len(result.files_created) >= 1

    def test_build_cli_has_test_count(self, builder, approved_cli_proposal):
        result = builder.build(approved_cli_proposal)
        assert result.test_count >= 3

    def test_build_cli_policy_scan_passed(self, builder, approved_cli_proposal):
        result = builder.build(approved_cli_proposal)
        assert result.policy_scan["passed"] is True


# ── Build: Offline Package ──────────────────────────────────────────────────

class TestBuildOfflinePackage:
    def test_build_offline_completes(self, builder, approved_offline_proposal):
        result = builder.build(approved_offline_proposal)
        assert result.state == BuildState.DONE.value

    def test_build_offline_has_files(self, builder, approved_offline_proposal):
        result = builder.build(approved_offline_proposal)
        assert len(result.files_created) >= 1

    def test_build_offline_policy_scan(self, builder, approved_offline_proposal):
        result = builder.build(approved_offline_proposal)
        assert result.policy_scan["passed"] is True


# ── Build: Manual Process ───────────────────────────────────────────────────

class TestBuildManualProcess:
    def test_build_manual_completes(self, builder, approved_manual_proposal):
        result = builder.build(approved_manual_proposal)
        assert result.state == BuildState.DONE.value

    def test_build_manual_no_test_count(self, builder, approved_manual_proposal):
        result = builder.build(approved_manual_proposal)
        assert result.test_count == 0

    def test_build_manual_no_policy_scan_needed(self, builder, approved_manual_proposal):
        result = builder.build(approved_manual_proposal)
        assert result.policy_scan["passed"] is True


# ── Scaffold ────────────────────────────────────────────────────────────────

class TestScaffold:
    def test_scaffold_cli_returns_paths(self, builder, approved_cli_proposal):
        files = builder.scaffold(approved_cli_proposal)
        assert len(files) >= 1
        assert isinstance(files[0], Path)

    def test_scaffold_cli_path_in_skills(self, builder, approved_cli_proposal):
        files = builder.scaffold(approved_cli_proposal)
        assert "skills" in str(files[0])

    def test_scaffold_manual_returns_path(self, builder, approved_manual_proposal):
        files = builder.scaffold(approved_manual_proposal)
        assert len(files) >= 1

    def test_scaffold_dry_run_doesnt_create_files(self, builder, approved_cli_proposal):
        files = builder.scaffold(approved_cli_proposal)
        for f in files:
            assert not f.exists()


# ── Build: All 5 types ──────────────────────────────────────────────────────

class TestBuildAllTypes:
    @pytest.mark.parametrize("impl_type", [
        IMPL_TYPE_CLI_WRAPPER,
        IMPL_TYPE_OFFLINE_PACKAGE,
        IMPL_TYPE_MANUAL_PROCESS,
        IMPL_TYPE_EXTERNAL_FUTURE,
        IMPL_TYPE_APP_FACTORY_FUTURE,
    ])
    def test_build_each_type_succeeds(self, builder, impl_type):
        p = CapabilityProposal.from_gap(
            gap_id="gap_test",
            capability_name=f"test_{impl_type[:6]}",
            sector="midia",
            desired_output="Test output",
            implementation_type=impl_type,
        )
        p.status = PROPOSAL_STATUS_APPROVED
        result = builder.build(p)
        assert result.state == BuildState.DONE.value


# ── Policy Failure Simulation ───────────────────────────────────────────────

class TestPolicyFailure:
    def test_build_stops_on_policy_failure(self, builder, approved_cli_proposal, monkeypatch):
        """Simula policy scan falhando."""
        def mock_scan(code):
            return {"passed": False, "violations": [{"line": 1, "pattern": "eval", "description": "eval() proibido"}]}

        monkeypatch.setattr(
            "src.capability_forge_real.builder.scan_code", mock_scan
        )
        result = builder.build(approved_cli_proposal)
        assert result.state == BuildState.POLICY_FAILED.value
        assert result.is_terminal is True
