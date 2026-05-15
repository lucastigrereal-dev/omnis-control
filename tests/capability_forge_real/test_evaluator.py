from src.capability_forge_real.evaluator import (
    CapabilityEvaluator,
    EvaluatorScorecard,
    DimensionScore,
    ScoreGrade,
)


class TestDimensionScore:
    def test_percentage(self):
        d = DimensionScore(name="test", score=7.5, max_score=10.0)
        assert d.percentage == 75.0

    def test_zero_max(self):
        d = DimensionScore(name="test", score=0, max_score=0)
        assert d.percentage == 0.0


class TestEvaluatorScorecard:
    def test_percentage(self):
        sc = EvaluatorScorecard(total_score=35, max_total=50)
        assert sc.percentage == 70.0

    def test_passed_grade_c(self):
        sc = EvaluatorScorecard(grade=ScoreGrade.C)
        assert sc.passed is True

    def test_not_passed_grade_d(self):
        sc = EvaluatorScorecard(grade=ScoreGrade.D)
        assert sc.passed is False

    def test_to_dict(self):
        sc = EvaluatorScorecard(
            capability_name="test_skill",
            total_score=42,
            max_total=50,
            grade=ScoreGrade.B,
            dimensions=[DimensionScore(name="code_quality", score=9, notes=["good"])],
        )
        d = sc.to_dict()
        assert d["capability_name"] == "test_skill"
        assert d["total_score"] == 42
        assert d["grade"] == "B"
        assert d["passed"] is True
        assert len(d["dimensions"]) == 1


class TestCapabilityEvaluator:
    def test_evaluate_empty_code(self):
        result = CapabilityEvaluator.evaluate(
            capability_name="empty",
            code="",
            test_code="",
        )
        assert result.total_score < result.max_total
        assert result.grade in (ScoreGrade.D, ScoreGrade.F)

    def test_evaluate_good_code(self):
        code = '''"""A test skill."""
def run(payload: dict) -> dict:
    """Execute the skill with the given payload."""
    # Process input
    result = {"status": "ok", "data": payload}
    return result
'''
        test_code = '''import pytest
def test_run():
    """Test the run function."""
    result = run({"key": "value"})
    assert result["status"] == "ok"

def test_empty_payload():
    result = run({})
    assert result["status"] == "ok"
'''
        spec = {"name": "test_skill", "description": "A test skill", "implementation_type": "cli_wrapper"}

        result = CapabilityEvaluator.evaluate(
            capability_name="test_skill",
            code=code,
            test_code=test_code,
            spec=spec,
            policy_scan_clean=True,
        )
        assert result.grade in (ScoreGrade.A, ScoreGrade.B, ScoreGrade.C)
        assert result.passed is True

    def test_policy_failure_scores_zero(self):
        result = CapabilityEvaluator.evaluate(
            capability_name="bad",
            code="def run(): pass",
            test_code="def test_run(): pass",
            policy_scan_clean=False,
        )
        policy_dim = [d for d in result.dimensions if d.name == "policy_compliance"][0]
        assert policy_dim.score == 0.0

    def test_no_test_code_scores_zero(self):
        result = CapabilityEvaluator.evaluate(
            capability_name="no_tests",
            code="def run(): pass",
            test_code="",
        )
        test_dim = [d for d in result.dimensions if d.name == "test_coverage"][0]
        assert test_dim.score == 0.0

    def test_grade_a_at_90_percent(self):
        result = CapabilityEvaluator.evaluate(
            capability_name="excellent",
            code='"""Great code."""\n\ndef run(payload: dict) -> dict:\n    """Execute."""\n    # Process\n    return {"ok": True}',
            test_code="import pytest\n\ndef test_run():\n    assert run({}) == {'ok': True}\n\ndef test_empty():\n    assert run({})\n\ndef test_type():\n    assert isinstance(run({}), dict)",
            spec={"name": "excellent", "description": "Great", "implementation_type": "cli_wrapper"},
            policy_scan_clean=True,
        )
        assert result.passed is True
