"""Onda 9 FIO 4 — SandboxRunner + CapabilityEvaluator rail in CapabilityBuilder.build()."""
from __future__ import annotations

import pytest

from src.capability_forge_real.builder import CapabilityBuilder
from src.capability_forge_real.models import (
    BuildResult,
    BuildState,
    TERMINAL_STATES,
    VALID_TRANSITIONS,
    CapabilityProposal,
    PROPOSAL_STATUS_APPROVED,
    IMPL_TYPE_CLI_WRAPPER,
    IMPL_TYPE_MANUAL_PROCESS,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def builder():
    return CapabilityBuilder(dry_run=True)


@pytest.fixture
def approved_cli_proposal():
    p = CapabilityProposal.from_gap(
        gap_id="gap_s9_001",
        capability_name="hotel_lead_scorer",
        sector="comercial",
        desired_output="Scores hotel leads by engagement potential",
        risk_level="low",
        implementation_type=IMPL_TYPE_CLI_WRAPPER,
    )
    p.status = PROPOSAL_STATUS_APPROVED
    return p


@pytest.fixture
def approved_manual_proposal():
    p = CapabilityProposal.from_gap(
        gap_id="gap_s9_002",
        capability_name="onboarding_checklist",
        sector="operacoes",
        desired_output="SOP checklist for hotel onboarding",
        implementation_type=IMPL_TYPE_MANUAL_PROCESS,
    )
    p.status = PROPOSAL_STATUS_APPROVED
    return p


# ── FSM: new states ───────────────────────────────────────────────────────────

class TestNewBuildStates:
    def test_sandbox_validating_state_exists(self):
        assert BuildState.SANDBOX_VALIDATING == "sandbox_validating"

    def test_score_failed_state_exists(self):
        assert BuildState.SCORE_FAILED == "score_failed"

    def test_score_failed_is_terminal(self):
        assert BuildState.SCORE_FAILED in TERMINAL_STATES

    def test_sandbox_validating_transitions(self):
        valid = VALID_TRANSITIONS[BuildState.SANDBOX_VALIDATING]
        assert BuildState.SCORE_FAILED in valid
        assert BuildState.REGISTERING in valid

    def test_validating_no_longer_leads_to_registering_directly(self):
        valid = VALID_TRANSITIONS[BuildState.VALIDATING]
        assert BuildState.REGISTERING not in valid
        assert BuildState.SANDBOX_VALIDATING in valid


# ── BuildResult: new fields ───────────────────────────────────────────────────

class TestBuildResultNewFields:
    def test_sandbox_result_defaults_none(self, approved_cli_proposal):
        result = BuildResult.new(approved_cli_proposal)
        assert result.sandbox_result is None

    def test_scorecard_defaults_none(self, approved_cli_proposal):
        result = BuildResult.new(approved_cli_proposal)
        assert result.scorecard is None

    def test_to_dict_includes_sandbox_result(self, approved_cli_proposal):
        result = BuildResult.new(approved_cli_proposal)
        d = result.to_dict()
        assert "sandbox_result" in d
        assert "scorecard" in d

    def test_from_dict_round_trip_new_fields(self, approved_cli_proposal):
        result = BuildResult.new(approved_cli_proposal)
        result.sandbox_result = {"status": "passed", "is_clean": True}
        result.scorecard = {"grade": "B", "passed": True}
        restored = BuildResult.from_dict(result.to_dict())
        assert restored.sandbox_result == result.sandbox_result
        assert restored.scorecard == result.scorecard


# ── Happy path ────────────────────────────────────────────────────────────────

class TestSandboxRailHappyPath:
    def test_cli_skill_reaches_done(self, builder, approved_cli_proposal):
        result = builder.build(approved_cli_proposal)
        assert result.state == BuildState.DONE.value

    def test_cli_skill_sandbox_result_populated(self, builder, approved_cli_proposal):
        result = builder.build(approved_cli_proposal)
        assert result.sandbox_result is not None
        assert result.sandbox_result["is_clean"] is True

    def test_cli_skill_scorecard_populated(self, builder, approved_cli_proposal):
        result = builder.build(approved_cli_proposal)
        assert result.scorecard is not None
        assert result.scorecard["passed"] is True

    def test_manual_process_skips_sandbox_rail(self, builder, approved_manual_proposal):
        result = builder.build(approved_manual_proposal)
        assert result.state == BuildState.DONE.value
        assert result.sandbox_result is None
        assert result.scorecard is None


# ── Rejection paths ───────────────────────────────────────────────────────────

class TestSandboxRailRejections:
    def test_sandbox_blocked_yields_score_failed(
        self, builder, approved_cli_proposal, monkeypatch
    ):
        """Code with forbidden patterns → sandbox blocks → SCORE_FAILED."""
        from src.capability_forge_real.sandbox import SandboxResult, SandboxStatus

        def blocked_validate(self_inner, code, run_id=""):
            return SandboxResult(
                run_id=run_id,
                status=SandboxStatus.BLOCKED,
                blocked_patterns=["subprocess"],
                error="Blocked patterns: subprocess",
            )

        import src.capability_forge_real.builder as builder_mod
        monkeypatch.setattr(
            builder_mod.SandboxRunner,
            "dry_run_validate",
            blocked_validate,
        )

        result = builder.build(approved_cli_proposal)
        assert result.state == BuildState.SCORE_FAILED.value

    def test_sandbox_blocked_stores_sandbox_result(
        self, builder, approved_cli_proposal, monkeypatch
    ):
        from src.capability_forge_real.sandbox import SandboxResult, SandboxStatus

        def blocked_validate(self_inner, code, run_id=""):
            return SandboxResult(
                run_id=run_id,
                status=SandboxStatus.BLOCKED,
                blocked_patterns=["subprocess"],
                error="Blocked patterns: subprocess",
            )

        import src.capability_forge_real.builder as builder_mod
        monkeypatch.setattr(builder_mod.SandboxRunner, "dry_run_validate", blocked_validate)

        result = builder.build(approved_cli_proposal)
        assert result.sandbox_result is not None
        assert result.sandbox_result["is_clean"] is False

    def test_low_score_yields_score_failed(
        self, builder, approved_cli_proposal, monkeypatch
    ):
        """Evaluator returns grade F → SCORE_FAILED."""
        from src.capability_forge_real.evaluator import (
            EvaluatorScorecard,
            ScoreGrade,
            DimensionScore,
        )

        def failing_evaluate(**kwargs):
            return EvaluatorScorecard(
                capability_name=kwargs.get("capability_name", ""),
                dimensions=[DimensionScore(name="code_quality", score=1.0)],
                total_score=5.0,
                max_total=50.0,
                grade=ScoreGrade.F,
            )

        import src.capability_forge_real.builder as builder_mod
        monkeypatch.setattr(
            builder_mod.CapabilityEvaluator,
            "evaluate",
            staticmethod(failing_evaluate),
        )

        result = builder.build(approved_cli_proposal)
        assert result.state == BuildState.SCORE_FAILED.value

    def test_low_score_stores_scorecard(
        self, builder, approved_cli_proposal, monkeypatch
    ):
        from src.capability_forge_real.evaluator import (
            EvaluatorScorecard,
            ScoreGrade,
            DimensionScore,
        )

        def failing_evaluate(**kwargs):
            return EvaluatorScorecard(
                capability_name=kwargs.get("capability_name", ""),
                dimensions=[DimensionScore(name="code_quality", score=1.0)],
                total_score=5.0,
                max_total=50.0,
                grade=ScoreGrade.F,
            )

        import src.capability_forge_real.builder as builder_mod
        monkeypatch.setattr(
            builder_mod.CapabilityEvaluator,
            "evaluate",
            staticmethod(failing_evaluate),
        )

        result = builder.build(approved_cli_proposal)
        assert result.scorecard is not None
        assert result.scorecard["passed"] is False
        assert result.scorecard["grade"] == "F"

    def test_score_failed_is_is_terminal(self, builder, approved_cli_proposal, monkeypatch):
        from src.capability_forge_real.sandbox import SandboxResult, SandboxStatus

        def blocked_validate(self_inner, code, run_id=""):
            return SandboxResult(
                run_id=run_id,
                status=SandboxStatus.BLOCKED,
                blocked_patterns=["subprocess"],
            )

        import src.capability_forge_real.builder as builder_mod
        monkeypatch.setattr(builder_mod.SandboxRunner, "dry_run_validate", blocked_validate)

        result = builder.build(approved_cli_proposal)
        assert result.is_terminal is True
        assert result.is_success is False
