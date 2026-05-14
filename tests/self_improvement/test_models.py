"""Tests for P28 models."""
import pytest

from src.self_improvement.models import (
    ExecutionFeedback, ImprovementProposal, ImpactMeasurement,
    Pattern, PrioritizedGap,
    SOURCE_MISSION, SOURCE_BUILD, SOURCE_ACTION, SOURCE_SYSTEM,
    CATEGORY_CAPABILITY_GAP, CATEGORY_PERFORMANCE, CATEGORY_RELIABILITY,
    CATEGORY_COST, CATEGORY_SECURITY,
    SEVERITY_LOW, SEVERITY_MEDIUM, SEVERITY_HIGH, SEVERITY_CRITICAL,
    IMPL_CODE_CHANGE, IMPL_CONFIG_CHANGE, IMPL_NEW_CAPABILITY, IMPL_PROCESS_CHANGE,
    PROPOSAL_DRAFT, PROPOSAL_PROPOSED, PROPOSAL_APPROVED, PROPOSAL_REJECTED,
    PROPOSAL_IMPLEMENTED, PROPOSAL_MEASURED, PROPOSAL_ROLLED_BACK,
    VERDICT_IMPROVED, VERDICT_DEGRADED, VERDICT_NEUTRAL, VERDICT_INSUFFICIENT_DATA,
)


class TestExecutionFeedback:
    def test_new_basic(self):
        fb = ExecutionFeedback.new(SOURCE_MISSION, "m1")
        assert fb.feedback_id.startswith("sif_")
        assert fb.source_type == SOURCE_MISSION
        assert fb.source_id == "m1"
        assert fb.status == "success"

    def test_new_with_errors(self):
        fb = ExecutionFeedback.new(SOURCE_BUILD, "b1", status="failure", errors=["build failed"])
        assert fb.is_failure is True
        assert fb.has_errors is True

    def test_from_mission_report(self):
        fb = ExecutionFeedback.from_mission_report({
            "mission_id": "m_test", "status": "success", "errors": [], "latency_ms": 200,
        })
        assert fb.source_type == SOURCE_MISSION
        assert fb.source_id == "m_test"

    def test_from_build_result(self):
        fb = ExecutionFeedback.from_build_result({
            "build_id": "apb_test", "is_complete": True, "errors": [],
        })
        assert fb.source_type == SOURCE_BUILD
        assert fb.status == "success"

    def test_from_build_result_failure(self):
        fb = ExecutionFeedback.from_build_result({
            "build_id": "apb_test", "is_complete": False, "errors": ["fail"],
        })
        assert fb.status == "failure"

    def test_from_action_result(self):
        fb = ExecutionFeedback.from_action_result({
            "result_id": "rwr_test", "status": "success", "error": "", "latency_ms": 150,
        })
        assert fb.source_type == SOURCE_ACTION
        assert fb.status == "success"

    def test_from_action_result_error(self):
        fb = ExecutionFeedback.from_action_result({
            "result_id": "rwr_test", "status": "timeout", "error": "timed out",
        })
        assert fb.status == "timeout"

    def test_to_dict_from_dict_roundtrip(self):
        fb1 = ExecutionFeedback.new(SOURCE_MISSION, "m1", status="failure",
                                    errors=["e1"], warnings=["w1"], latency_ms=300)
        fb2 = ExecutionFeedback.from_dict(fb1.to_dict())
        assert fb2.feedback_id == fb1.feedback_id
        assert fb2.status == fb1.status
        assert fb2.errors == fb1.errors

    def test_is_failure_detects_partial(self):
        fb = ExecutionFeedback.new(SOURCE_ACTION, "a1", status="partial_success")
        assert fb.is_failure is True


class TestImprovementProposal:
    def test_new_basic(self):
        p = ImprovementProposal.new("Add auth module")
        assert p.proposal_id.startswith("sip_")
        assert p.title == "Add auth module"
        assert p.status == PROPOSAL_DRAFT

    def test_new_full(self):
        p = ImprovementProposal.new(
            "Fix timeout", category=CATEGORY_RELIABILITY, severity=SEVERITY_HIGH,
            current_state="Timeout on step X", proposed_change="Increase timeout to 60s",
            expected_impact="Reduce timeout failures by 80%",
            implementation_type=IMPL_CONFIG_CHANGE, auto_implementable=True,
            evidence=["sif_abc"],
        )
        assert p.category == CATEGORY_RELIABILITY
        assert p.severity == SEVERITY_HIGH
        assert p.auto_implementable is True
        assert p.is_actionable is True

    def test_is_actionable_false_when_empty(self):
        p = ImprovementProposal.new("Vague title")
        assert p.is_actionable is False

    def test_to_dict_from_dict_roundtrip(self):
        p1 = ImprovementProposal.new("Test", category=CATEGORY_COST, severity=SEVERITY_LOW,
                                     proposed_change="Do X", implementation_type=IMPL_CONFIG_CHANGE)
        p2 = ImprovementProposal.from_dict(p1.to_dict())
        assert p2.proposal_id == p1.proposal_id
        assert p2.title == p1.title
        assert p2.category == p1.category

    def test_status_lifecycle(self):
        p = ImprovementProposal.new("Test")
        p.status = PROPOSAL_PROPOSED
        assert p.status == PROPOSAL_PROPOSED
        p.status = PROPOSAL_APPROVED
        assert p.status == PROPOSAL_APPROVED
        p.approved_by = "lucas"
        p.status = PROPOSAL_IMPLEMENTED
        assert p.status == PROPOSAL_IMPLEMENTED
        p.status = PROPOSAL_MEASURED
        assert p.status == PROPOSAL_MEASURED


class TestImpactMeasurement:
    def test_new_basic(self):
        m = ImpactMeasurement.new("sip_test")
        assert m.measurement_id.startswith("sim_")
        assert m.verdict == VERDICT_INSUFFICIENT_DATA

    def test_new_with_values(self):
        m = ImpactMeasurement.new("sip_test", metric="mission_success_rate",
                                  value_before=0.7, value_after=0.85,
                                  verdict=VERDICT_IMPROVED, sample_size=50)
        assert m.delta == pytest.approx(0.15)
        assert m.is_improvement is True

    def test_is_degradation(self):
        m = ImpactMeasurement.new("sip_test", value_before=0.8, value_after=0.5,
                                  verdict=VERDICT_DEGRADED)
        assert m.delta == pytest.approx(-0.3)
        assert m.is_degradation is True

    def test_to_dict_from_dict_roundtrip(self):
        m1 = ImpactMeasurement.new("sip_test", metric="avg_latency",
                                   value_before=500, value_after=300,
                                   verdict=VERDICT_IMPROVED, sample_size=30)
        m2 = ImpactMeasurement.from_dict(m1.to_dict())
        assert m2.proposal_id == m1.proposal_id
        assert m2.delta == m1.delta


class TestPattern:
    def test_new_basic(self):
        p = Pattern.new("timeout_pattern", category="performance")
        assert p.pattern_id.startswith("sipn_")
        assert p.name == "timeout_pattern"
        assert p.occurrences == 1

    def test_new_with_feedback_ids(self):
        p = Pattern.new("error_pattern", category="reliability",
                        description="Recurring error in step X",
                        occurrences=5, related_feedback_ids=["sif_a", "sif_b"],
                        confidence=0.8)
        assert p.occurrences == 5
        assert len(p.related_feedback_ids) == 2
        assert p.confidence == 0.8

    def test_to_dict_from_dict_roundtrip(self):
        p1 = Pattern.new("test", category="cost", description="desc",
                         occurrences=3, confidence=0.7)
        p2 = Pattern.from_dict(p1.to_dict())
        assert p2.name == p1.name
        assert p2.occurrences == p1.occurrences

    def test_from_dict_minimal(self):
        p = Pattern.from_dict({"pattern_id": "sipn_x", "name": "test"})
        assert p.pattern_id == "sipn_x"
        assert p.name == "test"
        assert p.occurrences == 0


class TestPrioritizedGap:
    def test_new_basic(self):
        pattern = Pattern.new("gap_pattern", category="security")
        gap = PrioritizedGap.new(pattern, score=8.5, impact_estimate="High impact", urgency=SEVERITY_HIGH)
        assert gap.gap_id.startswith("sig_")
        assert gap.score == 8.5
        assert gap.urgency == SEVERITY_HIGH

    def test_to_dict_from_dict_roundtrip(self):
        pattern = Pattern.new("test_pattern", category="performance",
                              occurrences=3, confidence=0.9)
        gap1 = PrioritizedGap.new(pattern, score=7.0, urgency=SEVERITY_CRITICAL)
        gap1.rank = 1
        gap2 = PrioritizedGap.from_dict(gap1.to_dict())
        assert gap2.gap_id == gap1.gap_id
        assert gap2.score == gap1.score
        assert gap2.pattern.name == pattern.name

    def test_from_dict_with_dict_pattern(self):
        d = {
            "gap_id": "sig_test",
            "pattern": {"pattern_id": "sipn_test", "name": "p", "occurrences": 2, "confidence": 0.5},
            "score": 5.0, "urgency": SEVERITY_MEDIUM, "rank": 3,
        }
        gap = PrioritizedGap.from_dict(d)
        assert gap.gap_id == "sig_test"
        assert gap.pattern.name == "p"
        assert gap.rank == 3
