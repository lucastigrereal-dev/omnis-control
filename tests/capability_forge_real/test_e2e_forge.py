"""E2E tests for P22 Capability Forge Real — gap → proposal → build → register."""
from __future__ import annotations

import pytest
from pathlib import Path

from src.capability_forge_real import (
    CapabilityBuilder,
    BuildResult,
    BuildState,
    render_template,
    scan_code,
    generate_test_content,
    count_test_functions,
)
from src.capability_forge_lite.models import (
    CapabilityProposal,
    PROPOSAL_STATUS_APPROVED,
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


def _approved_proposal(name, impl_type):
    p = CapabilityProposal.from_gap(
        gap_id="gap_e2e",
        capability_name=name,
        sector="midia",
        desired_output=f"E2E test for {name}",
        implementation_type=impl_type,
    )
    p.status = PROPOSAL_STATUS_APPROVED
    return p


# ── Full Pipeline: Template → Code → Scan → Tests → Build ───────────────────

class TestFullPipeline:
    """Simula o ciclo completo de forge real para cada tipo."""

    def test_cli_wrapper_full_cycle(self, builder):
        proposal = _approved_proposal("e2e_cli_test", IMPL_TYPE_CLI_WRAPPER)

        # Step 1: Template rendering
        from src.capability_forge_real.scaffold import get_template
        tpl = get_template(IMPL_TYPE_CLI_WRAPPER)
        rendered = render_template(tpl, proposal)
        assert "e2e_cli_test" in rendered
        assert "E2eCliTest" in rendered

        # Step 2: Policy scan
        scan = scan_code(rendered)
        assert scan["passed"] is True

        # Step 3: Test generation
        tests = generate_test_content(proposal)
        assert count_test_functions(tests) >= 3

        # Step 4: Full build
        result = builder.build(proposal)
        assert result.state == BuildState.DONE.value
        assert result.is_success is True
        assert result.test_count >= 3

    def test_offline_package_full_cycle(self, builder):
        proposal = _approved_proposal("e2e_offline", IMPL_TYPE_OFFLINE_PACKAGE)

        from src.capability_forge_real.scaffold import get_template
        tpl = get_template(IMPL_TYPE_OFFLINE_PACKAGE)
        rendered = render_template(tpl, proposal)
        assert "e2e_offline" in rendered

        scan = scan_code(rendered)
        assert scan["passed"] is True

        result = builder.build(proposal)
        assert result.state == BuildState.DONE.value

    def test_manual_process_full_cycle(self, builder):
        proposal = _approved_proposal("e2e_manual", IMPL_TYPE_MANUAL_PROCESS)

        from src.capability_forge_real.scaffold import get_template
        tpl = get_template(IMPL_TYPE_MANUAL_PROCESS)
        rendered = render_template(tpl, proposal)
        assert "Processo Manual" in rendered

        result = builder.build(proposal)
        assert result.state == BuildState.DONE.value

    def test_external_future_full_cycle(self, builder):
        proposal = _approved_proposal("e2e_ext", IMPL_TYPE_EXTERNAL_FUTURE)

        result = builder.build(proposal)
        assert result.state == BuildState.DONE.value
        assert result.is_success is True

    def test_app_factory_future_full_cycle(self, builder):
        proposal = _approved_proposal("e2e_app", IMPL_TYPE_APP_FACTORY_FUTURE)

        result = builder.build(proposal)
        assert result.state == BuildState.DONE.value


# ── Build Result Integrity ───────────────────────────────────────────────────

class TestBuildResultIntegrity:
    def test_build_result_has_all_fields(self, builder):
        proposal = _approved_proposal("e2e_fields", IMPL_TYPE_CLI_WRAPPER)
        result = builder.build(proposal)
        data = result.to_dict()
        assert "build_id" in data
        assert "proposal_id" in data
        assert "state" in data
        assert "files_created" in data
        assert "test_count" in data
        assert "policy_scan" in data
        assert "dry_run" in data

    def test_dry_run_reflected_in_result(self, builder):
        proposal = _approved_proposal("e2e_dry", IMPL_TYPE_CLI_WRAPPER)
        result = builder.build(proposal)
        assert result.dry_run is True


# ── Round-trip: All 5 types end in DONE ─────────────────────────────────────

class TestAllTypesRoundTrip:
    @pytest.mark.parametrize("name,impl_type", [
        ("e2e_all_cli", IMPL_TYPE_CLI_WRAPPER),
        ("e2e_all_offline", IMPL_TYPE_OFFLINE_PACKAGE),
        ("e2e_all_manual", IMPL_TYPE_MANUAL_PROCESS),
        ("e2e_all_ext", IMPL_TYPE_EXTERNAL_FUTURE),
        ("e2e_all_app", IMPL_TYPE_APP_FACTORY_FUTURE),
    ])
    def test_all_types_done(self, builder, name, impl_type):
        proposal = _approved_proposal(name, impl_type)
        result = builder.build(proposal)
        assert result.state == BuildState.DONE.value, f"Failed for {impl_type}"
