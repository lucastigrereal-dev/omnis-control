"""Skill Test Harness — structured testing framework for skill validation."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class SkillTestStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class SkillTestCase:
    name: str
    description: str = ""
    input_payload: dict[str, Any] = field(default_factory=dict)
    expected_status: str = "DRY_RUN_OK"
    expected_artifacts: list[str] = field(default_factory=list)
    should_pass: bool = True
    tags: list[str] = field(default_factory=list)


@dataclass
class SkillTestResult:
    case_name: str
    status: SkillTestStatus = SkillTestStatus.PASSED
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0


@dataclass
class SkillTestSuite:
    skill_name: str
    cases: list[SkillTestCase] = field(default_factory=list)
    results: list[SkillTestResult] = field(default_factory=list)

    def add_case(self, case: SkillTestCase) -> None:
        self.cases.append(case)

    def summary(self) -> dict[str, Any]:
        passed = sum(1 for r in self.results if r.status == SkillTestStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == SkillTestStatus.FAILED)
        return {
            "skill_name": self.skill_name,
            "total": len(self.results),
            "passed": passed,
            "failed": failed,
            "errors": sum(1 for r in self.results if r.status == SkillTestStatus.ERROR),
            "skipped": sum(1 for r in self.results if r.status == SkillTestStatus.SKIPPED),
            "all_passed": failed == 0 and len(self.results) > 0,
        }


class SkillTestHarness:
    """Structured test harness for validating skills before execution."""

    @staticmethod
    def run_test(case: SkillTestCase, executor: Callable | None = None) -> SkillTestResult:
        if executor is None:
            result = SkillTestHarness._dry_run_validation(case)
        else:
            try:
                output = executor(case.input_payload)
                result = SkillTestHarness._validate_output(case, output)
            except Exception as exc:
                return SkillTestResult(
                    case_name=case.name,
                    status=SkillTestStatus.ERROR,
                    message=str(exc),
                )
        return result

    @staticmethod
    def run_suite(
        suite: SkillTestSuite,
        executor: Callable | None = None,
    ) -> SkillTestSuite:
        for case in suite.cases:
            result = SkillTestHarness.run_test(case, executor)
            suite.results.append(result)
        return suite

    @staticmethod
    def _dry_run_validation(case: SkillTestCase) -> SkillTestResult:
        """Validate a test case without executing — checks input/output contract."""
        issues: list[str] = []

        if not case.name:
            issues.append("empty test case name")

        if case.should_pass and not case.expected_artifacts:
            issues.append("no expected artifacts defined for passing test")

        if issues:
            return SkillTestResult(
                case_name=case.name or "unnamed",
                status=SkillTestStatus.FAILED,
                message="; ".join(issues),
            )

        return SkillTestResult(
            case_name=case.name,
            status=SkillTestStatus.PASSED,
            message="dry-run validation OK",
            details={"expected_status": case.expected_status, "artifacts_count": len(case.expected_artifacts)},
        )

    @staticmethod
    def _validate_output(case: SkillTestCase, output: Any) -> SkillTestResult:
        status = SkillTestStatus.PASSED
        message = "execution OK"

        if isinstance(output, dict):
            actual_status = output.get("status", "")
            if case.should_pass and actual_status != case.expected_status:
                status = SkillTestStatus.FAILED
                message = f"expected status {case.expected_status}, got {actual_status}"
        elif case.should_pass:
            status = SkillTestStatus.FAILED
            message = f"unexpected output type: {type(output).__name__}"

        return SkillTestResult(case_name=case.name, status=status, message=message)

    @staticmethod
    def create_smoke_suite(skill_name: str) -> SkillTestSuite:
        """Generate a default smoke-test suite for any skill."""
        suite = SkillTestSuite(skill_name=skill_name)
        suite.add_case(SkillTestCase(
            name=f"{skill_name}_dry_run_smoke",
            description="Default smoke test — dry-run only",
            expected_status="DRY_RUN_OK",
            expected_artifacts=["result.json"],
            should_pass=True,
        ))
        suite.add_case(SkillTestCase(
            name=f"{skill_name}_invalid_input",
            description="Should reject empty payload gracefully",
            input_payload={"invalid": True},
            expected_status="BLOCKED",
            should_pass=False,
        ))
        return suite
