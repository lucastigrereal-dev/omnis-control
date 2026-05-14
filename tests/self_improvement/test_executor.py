"""Tests for P28 ImprovementExecutor."""
import pytest

from src.self_improvement.executor import ImprovementExecutor
from src.self_improvement.models import (
    ImprovementProposal, ImpactMeasurement,
    IMPL_CODE_CHANGE, IMPL_CONFIG_CHANGE, IMPL_NEW_CAPABILITY, IMPL_PROCESS_CHANGE,
    PROPOSAL_DRAFT, PROPOSAL_APPROVED, PROPOSAL_IMPLEMENTED,
    CATEGORY_PERFORMANCE, CATEGORY_RELIABILITY, CATEGORY_SECURITY,
    VERDICT_INSUFFICIENT_DATA,
)
from src.self_improvement.errors import ExecutionError


class TestImprovementExecutor:
    @pytest.fixture
    def executor(self):
        return ImprovementExecutor(dry_run=True)

    @pytest.fixture
    def real_executor(self):
        return ImprovementExecutor(dry_run=False)

    @pytest.fixture
    def approved_proposal(self):
        return ImprovementProposal.new(
            "Test proposal", category=CATEGORY_PERFORMANCE,
            proposed_change="Increase timeout to 60s",
            implementation_type=IMPL_CONFIG_CHANGE,
            auto_implementable=True,
        )

    def test_dry_run_returns_empty_measurement(self, executor, approved_proposal):
        approved_proposal.status = PROPOSAL_APPROVED
        m = executor.execute(approved_proposal)
        assert m.verdict == VERDICT_INSUFFICIENT_DATA

    def test_execute_not_approved_raises(self, executor, approved_proposal):
        approved_proposal.status = PROPOSAL_DRAFT
        with pytest.raises(ExecutionError):
            executor.execute(approved_proposal)

    def test_code_change_implementation(self, real_executor):
        p = ImprovementProposal.new("Fix bug", category=CATEGORY_RELIABILITY,
                                    proposed_change="Add try/except",
                                    implementation_type=IMPL_CODE_CHANGE)
        p.status = PROPOSAL_APPROVED
        m = real_executor.execute(p)
        assert m.metric == "code_change_applied"

    def test_config_change_implementation(self, real_executor):
        p = ImprovementProposal.new("Tune timeout", category=CATEGORY_PERFORMANCE,
                                    proposed_change="Increase timeout",
                                    implementation_type=IMPL_CONFIG_CHANGE)
        p.status = PROPOSAL_APPROVED
        m = real_executor.execute(p)
        assert m.metric == "config_change_applied"

    def test_new_capability_implementation(self, real_executor):
        p = ImprovementProposal.new("Add auth", category=CATEGORY_PERFORMANCE,
                                    proposed_change="Build auth module",
                                    implementation_type=IMPL_NEW_CAPABILITY)
        p.status = PROPOSAL_APPROVED
        m = real_executor.execute(p)
        assert m.metric == "new_capability_scaffolded"

    def test_process_change_implementation(self, real_executor):
        p = ImprovementProposal.new("Security review", category=CATEGORY_SECURITY,
                                    proposed_change="Add review step",
                                    implementation_type=IMPL_PROCESS_CHANGE)
        p.status = PROPOSAL_APPROVED
        m = real_executor.execute(p)
        assert m.metric == "process_change_documented"

    def test_rollback_removes_measurement(self, executor, approved_proposal):
        approved_proposal.status = PROPOSAL_APPROVED
        executor.execute(approved_proposal)
        assert executor.implemented_count == 1
        assert executor.rollback(approved_proposal.proposal_id) is True
        assert executor.rolled_back_count == 1

    def test_get_measurements(self, executor, approved_proposal):
        approved_proposal.status = PROPOSAL_APPROVED
        executor.execute(approved_proposal)
        assert len(executor.get_measurements()) == 1

    def test_implements_sets_proposal_status(self, real_executor):
        p = ImprovementProposal.new("Test", category=CATEGORY_PERFORMANCE,
                                    proposed_change="Do X",
                                    implementation_type=IMPL_CONFIG_CHANGE)
        p.status = PROPOSAL_APPROVED
        real_executor.execute(p)
        assert p.status == PROPOSAL_IMPLEMENTED

    def test_rollback_unknown_id(self, executor):
        assert executor.rollback("nonexistent") is True

    def test_dry_run_does_not_change_status(self, executor, approved_proposal):
        approved_proposal.status = PROPOSAL_APPROVED
        executor.execute(approved_proposal)
        # In dry_run mode, status should NOT change to IMPLEMENTED
        assert approved_proposal.status == PROPOSAL_APPROVED
