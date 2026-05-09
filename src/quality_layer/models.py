"""Quality layer models."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class QualityGrade(str, Enum):
    READY = "ready_for_human_review"
    NEEDS_ADJUSTMENT = "needs_adjustment"
    BLOCKED = "blocked"


@dataclass
class QualityResult:
    package_id: str
    score: int  # 0-100
    grade: QualityGrade
    checks_passed: list = field(default_factory=list)
    checks_failed: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "package_id": self.package_id,
            "score": self.score,
            "grade": self.grade.value,
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
            "warnings": self.warnings,
        }

    @classmethod
    def from_score(cls, package_id: str, score: int, checks_passed: list, checks_failed: list, warnings: list) -> "QualityResult":
        if score >= 90:
            grade = QualityGrade.READY
        elif score >= 70:
            grade = QualityGrade.NEEDS_ADJUSTMENT
        else:
            grade = QualityGrade.BLOCKED
        return cls(
            package_id=package_id,
            score=score,
            grade=grade,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            warnings=warnings,
        )
