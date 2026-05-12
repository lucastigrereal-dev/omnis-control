"""Tests for P15 Computer Ops service."""
from __future__ import annotations

import pytest

from src.computer_ops.models import (
    AuditTarget,
    DiskFinding,
    CleanupCandidate,
    TARGET_DISK,
    TARGET_PROJECT,
    TARGET_DOCKER,
    SEVERITY_LOW,
    SEVERITY_HIGH,
    SEVERITY_CRITICAL,
    ACTION_QUARANTINE,
    ACTION_ARCHIVE,
    ACTION_DELETE,
    ACTION_KEEP,
    ACTION_REVIEW,
    STATUS_CLASSIFIED,
    STATUS_QUARANTINED,
)
from src.computer_ops.service import (
    ComputerOpsPlanner,
    AuditPlan,
    ClassificationResult,
    SafeCleanupPlan,
    build_readonly_audit_plan,
    classify_cleanup_candidate,
    generate_safe_cleanup_plan,
)
from src.computer_ops.errors import (
    EmptyTargetListError,
    InvalidTargetTypeError,
    CleanupPlanError,
    DestructiveActionBlockedError,
)


class TestComputerOpsPlanner:
    def test_build_plan_with_targets(self, sample_targets):
        planner = ComputerOpsPlanner()
        plan = planner.build_plan(sample_targets)
        assert isinstance(plan, AuditPlan)
        assert plan.plan_id == "audit_3_targets"
        assert len(plan.targets) == 3
        assert plan.estimated_steps == 9  # 3 * 3
        assert plan.dry_run is True
        assert "read_only_scan" in plan.safety_rules
        assert "no_modifications" in plan.safety_rules

    def test_build_plan_filters_disabled_targets(self):
        t1 = AuditTarget.new(TARGET_DISK, "/a", "A", enabled=True)
        t2 = AuditTarget.new(TARGET_PROJECT, "/b", "B", enabled=False)
        t3 = AuditTarget.new(TARGET_DOCKER, "/c", "C", enabled=True)

        planner = ComputerOpsPlanner()
        plan = planner.build_plan([t1, t2, t3])
        assert len(plan.targets) == 2
        target_ids = {t.target_id for t in plan.targets}
        assert t1.target_id in target_ids
        assert t3.target_id in target_ids
        assert t2.target_id not in target_ids

    def test_build_plan_raises_on_empty(self):
        planner = ComputerOpsPlanner()
        with pytest.raises(EmptyTargetListError):
            planner.build_plan([])

    def test_build_plan_raises_on_invalid_type(self):
        t = AuditTarget(target_id="x", target_type="invalid_type", path="/", label="Bad")
        planner = ComputerOpsPlanner()
        with pytest.raises(InvalidTargetTypeError):
            planner.build_plan([t])

    def test_build_report(self):
        planner = ComputerOpsPlanner()
        report = planner.build_report("Titulo", "Desc")
        assert report.title == "Titulo"
        assert report.description == "Desc"
        assert len(report.safety_rules_applied) == 4

    def test_plan_is_empty_property(self):
        plan = AuditPlan(plan_id="empty")
        assert plan.is_empty is True


class TestBuildReadOnlyAuditPlan:
    def test_convenience_function(self, sample_targets):
        plan = build_readonly_audit_plan(sample_targets)
        assert isinstance(plan, AuditPlan)
        assert plan.dry_run is True
        assert len(plan.targets) == 3


class TestClassifyCleanupCandidate:
    def test_classify_safe_candidate(self, sample_cleanup_candidate):
        result = classify_cleanup_candidate(sample_cleanup_candidate)
        assert isinstance(result, ClassificationResult)
        assert result.is_safe is True
        assert result.requires_review is False  # < 1GB, has days_since_accessed
        assert result.blocked_actions == []

    def test_classify_blocks_delete_without_quarantine(self):
        c = CleanupCandidate(
            candidate_id="c_x",
            source_finding_id="disk_x",
            path="/tmp/x",
            size_bytes=100,
            recommended_action=ACTION_DELETE,
            days_since_accessed=10,
        )
        result = classify_cleanup_candidate(c)
        assert result.is_safe is False
        assert ACTION_DELETE in result.blocked_actions
        assert len(result.warnings) > 0
        # Deve ter sido corrigido para QUARANTINE
        assert c.recommended_action == ACTION_QUARANTINE

    def test_classify_large_candidate_requires_review(self):
        c = CleanupCandidate.new(
            "disk_x", "/tmp/big", 2_000_000_000,  # 2 GB
            ACTION_QUARANTINE, days_since_accessed=30,
        )
        result = classify_cleanup_candidate(c)
        assert result.requires_review is True
        assert any("1GB" in w for w in result.warnings)

    def test_classify_no_access_data_requires_review(self):
        c = CleanupCandidate.new(
            "disk_x", "/tmp/unknown", 100_000, ACTION_QUARANTINE,
        )
        result = classify_cleanup_candidate(c)
        assert result.requires_review is True
        assert any("ultimo acesso" in w for w in result.warnings)

    def test_classify_already_quarantined_delete_still_blocked(self):
        c = CleanupCandidate.new("disk_x", "/tmp/x", 100, ACTION_QUARANTINE)
        c.mark_quarantined("/q/x")
        # Forcar delete apos quarentena — mas a funcao bloqueia
        c.recommended_action = ACTION_DELETE
        result = classify_cleanup_candidate(c)
        assert result.is_safe is False
        assert ACTION_DELETE in result.blocked_actions

    def test_classify_result_updates_candidate_status(self, sample_cleanup_candidate):
        result = classify_cleanup_candidate(sample_cleanup_candidate)
        assert result.candidate.status == STATUS_CLASSIFIED
        assert result.candidate.is_safe_to_clean is True


class TestGenerateSafeCleanupPlan:
    def test_generate_plan_basic(self, sample_cleanup_candidate):
        plan = generate_safe_cleanup_plan([sample_cleanup_candidate])
        assert isinstance(plan, SafeCleanupPlan)
        assert plan.candidate_count == 1
        assert plan.total_size_bytes == sample_cleanup_candidate.size_bytes
        assert plan.requires_approval is True
        assert len(plan.phases) == 2
        assert plan.phases[0]["phase"] == "quarantine"
        assert plan.phases[0]["dry_run"] is True
        assert plan.phases[1]["phase"] == "review"

    def test_generate_plan_multiple_candidates(self):
        c1 = CleanupCandidate.new("f1", "/a", 100, ACTION_QUARANTINE, days_since_accessed=30)
        c2 = CleanupCandidate.new("f2", "/b", 200, ACTION_ARCHIVE, days_since_accessed=60)
        plan = generate_safe_cleanup_plan([c1, c2])
        assert plan.candidate_count == 2
        assert plan.total_size_bytes == 300

    def test_generate_plan_skips_already_classified(self):
        c = CleanupCandidate.new("f1", "/a", 100, ACTION_QUARANTINE, days_since_accessed=30)
        c.mark_classified(True, False)
        plan = generate_safe_cleanup_plan([c])
        assert plan.candidate_count == 1
        assert any("ja classificado" in n for n in plan.notes)

    def test_generate_plan_raises_on_empty(self):
        with pytest.raises(CleanupPlanError, match="Lista de candidatos vazia"):
            generate_safe_cleanup_plan([])

    def test_generate_plan_no_destructive_actions_in_phases(self, sample_cleanup_candidate):
        plan = generate_safe_cleanup_plan([sample_cleanup_candidate])
        for phase in plan.phases:
            assert "delete" not in phase.get("action", "").lower()
            assert "remove" not in phase.get("action", "").lower()

    def test_generate_plan_handles_large_candidate(self):
        c = CleanupCandidate.new("f1", "/big", 3_000_000_000, ACTION_QUARANTINE, days_since_accessed=10)
        plan = generate_safe_cleanup_plan([c])
        assert plan.requires_approval is True
        assert any("1GB" in n for n in plan.notes)

    def test_generate_plan_quarantine_phase_is_dry_run(self):
        c = CleanupCandidate.new("f1", "/tmp/x", 100, ACTION_QUARANTINE, days_since_accessed=5)
        plan = generate_safe_cleanup_plan([c])
        quarantine = plan.phases[0]
        assert quarantine["dry_run"] is True
        assert "NENHUM ARQUIVO SERA MOVIDO" in quarantine["note"]
