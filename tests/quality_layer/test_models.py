"""Tests for quality_layer models."""
from src.quality_layer.models import QualityResult, QualityGrade


class TestQualityGrade:
    def test_score_90_plus_is_ready(self):
        r = QualityResult.from_score("pkg", 90, [], [], [])
        assert r.grade == QualityGrade.READY

    def test_score_70_to_89_needs_adjustment(self):
        r = QualityResult.from_score("pkg", 75, [], [], [])
        assert r.grade == QualityGrade.NEEDS_ADJUSTMENT

    def test_score_below_70_is_blocked(self):
        r = QualityResult.from_score("pkg", 50, [], [], [])
        assert r.grade == QualityGrade.BLOCKED

    def test_score_100_is_ready(self):
        r = QualityResult.from_score("pkg", 100, [], [], [])
        assert r.grade == QualityGrade.READY

    def test_score_0_is_blocked(self):
        r = QualityResult.from_score("pkg", 0, [], [], [])
        assert r.grade == QualityGrade.BLOCKED


class TestQualityResultToDict:
    def test_to_dict_has_all_keys(self):
        r = QualityResult.from_score("pkg", 80, ["a"], ["b"], ["w"])
        d = r.to_dict()
        assert "package_id" in d
        assert "score" in d
        assert "grade" in d
        assert "checks_passed" in d
        assert "checks_failed" in d
        assert "warnings" in d

    def test_grade_is_string(self):
        r = QualityResult.from_score("pkg", 95, [], [], [])
        d = r.to_dict()
        assert isinstance(d["grade"], str)
