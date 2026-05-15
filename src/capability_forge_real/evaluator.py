"""Evaluator Scorecard — quality scoring for generated capabilities."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ScoreGrade(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    F = "F"


@dataclass
class DimensionScore:
    name: str
    score: float = 0.0
    max_score: float = 10.0
    notes: list[str] = field(default_factory=list)

    @property
    def percentage(self) -> float:
        return (self.score / self.max_score) * 100 if self.max_score > 0 else 0.0


@dataclass
class EvaluatorScorecard:
    capability_name: str = ""
    dimensions: list[DimensionScore] = field(default_factory=list)
    total_score: float = 0.0
    max_total: float = 50.0
    grade: ScoreGrade = ScoreGrade.F

    @property
    def percentage(self) -> float:
        return (self.total_score / self.max_total) * 100 if self.max_total > 0 else 0.0

    @property
    def passed(self) -> bool:
        return self.grade in (ScoreGrade.A, ScoreGrade.B, ScoreGrade.C)

    def to_dict(self) -> dict[str, Any]:
        return {
            "capability_name": self.capability_name,
            "dimensions": [
                {"name": d.name, "score": d.score, "max": d.max_score, "notes": d.notes}
                for d in self.dimensions
            ],
            "total_score": self.total_score,
            "max_total": self.max_total,
            "percentage": self.percentage,
            "grade": self.grade.value,
            "passed": self.passed,
        }


class CapabilityEvaluator:
    """Evaluates generated capability code across 5 quality dimensions."""

    DIMENSION_WEIGHTS = {
        "code_quality": 10.0,
        "test_coverage": 10.0,
        "policy_compliance": 10.0,
        "spec_adherence": 10.0,
        "documentation": 10.0,
    }

    @staticmethod
    def evaluate(
        capability_name: str = "",
        code: str = "",
        test_code: str = "",
        spec: dict[str, Any] | None = None,
        policy_scan_clean: bool = True,
    ) -> EvaluatorScorecard:
        dimensions: list[DimensionScore] = []

        # Code quality
        dimensions.append(CapabilityEvaluator._score_code_quality(code))

        # Test coverage
        dimensions.append(CapabilityEvaluator._score_test_coverage(test_code))

        # Policy compliance
        dimensions.append(CapabilityEvaluator._score_policy_compliance(policy_scan_clean))

        # Spec adherence
        dimensions.append(CapabilityEvaluator._score_spec_adherence(spec))

        # Documentation
        dimensions.append(CapabilityEvaluator._score_documentation(code, test_code))

        total = sum(d.score for d in dimensions)
        max_total = sum(d.max_score for d in dimensions)
        percentage = (total / max_total) * 100 if max_total > 0 else 0

        grade = CapabilityEvaluator._compute_grade(percentage)

        return EvaluatorScorecard(
            capability_name=capability_name,
            dimensions=dimensions,
            total_score=total,
            max_total=max_total,
            grade=grade,
        )

    @staticmethod
    def _score_code_quality(code: str) -> DimensionScore:
        score = 10.0
        notes: list[str] = []

        if not code:
            return DimensionScore(name="code_quality", score=0.0, notes=["no code provided"])

        if "def " not in code and "class " not in code:
            score -= 2.0
            notes.append("missing function or class definition")

        if "import" not in code and "from " not in code:
            score -= 1.0
            notes.append("no imports — likely incomplete")

        if len(code) < 50:
            score -= 3.0
            notes.append("code too short (< 50 chars)")

        if "#" not in code and '"""' not in code:
            score -= 1.0
            notes.append("no comments or docstrings")

        return DimensionScore(name="code_quality", score=max(score, 0), notes=notes)

    @staticmethod
    def _score_test_coverage(test_code: str) -> DimensionScore:
        score = 10.0
        notes: list[str] = []

        if not test_code:
            return DimensionScore(name="test_coverage", score=0.0, notes=["no tests provided"])

        test_count = test_code.count("def test_")
        if test_count == 0:
            score -= 5.0
            notes.append("zero test functions found")
        elif test_count < 3:
            score -= 2.0
            notes.append(f"only {test_count} test(s) — recommend >= 3")

        if "import pytest" not in test_code and "from pytest" not in test_code:
            score -= 1.0
            notes.append("missing pytest import")

        if "assert" not in test_code:
            score -= 3.0
            notes.append("no assertions found")

        return DimensionScore(name="test_coverage", score=max(score, 0), notes=notes)

    @staticmethod
    def _score_policy_compliance(policy_scan_clean: bool) -> DimensionScore:
        if policy_scan_clean:
            return DimensionScore(name="policy_compliance", score=10.0, notes=["all policies passed"])
        return DimensionScore(name="policy_compliance", score=0.0, notes=["policy scan failed"])

    @staticmethod
    def _score_spec_adherence(spec: dict[str, Any] | None) -> DimensionScore:
        score = 10.0
        notes: list[str] = []

        if spec is None:
            return DimensionScore(name="spec_adherence", score=5.0, notes=["no spec provided — neutral score"])

        required = ["name", "description", "implementation_type"]
        missing = [k for k in required if k not in spec]
        if missing:
            score -= len(missing) * 3.0
            notes.append(f"missing spec keys: {', '.join(missing)}")

        return DimensionScore(name="spec_adherence", score=max(score, 0), notes=notes)

    @staticmethod
    def _score_documentation(code: str, test_code: str) -> DimensionScore:
        score = 10.0
        notes: list[str] = []

        has_docstring = '"""' in code or "'''" in code
        has_comments = "#" in code

        if not has_docstring:
            score -= 3.0
            notes.append("missing docstring")

        if not has_comments:
            score -= 2.0
            notes.append("no inline comments")

        if len(code) > 100 and not has_docstring:
            score -= 1.0
            notes.append("long code without docstring")

        return DimensionScore(name="documentation", score=max(score, 0), notes=notes)

    @staticmethod
    def _compute_grade(percentage: float) -> ScoreGrade:
        if percentage >= 90:
            return ScoreGrade.A
        if percentage >= 75:
            return ScoreGrade.B
        if percentage >= 60:
            return ScoreGrade.C
        if percentage >= 40:
            return ScoreGrade.D
        return ScoreGrade.F
