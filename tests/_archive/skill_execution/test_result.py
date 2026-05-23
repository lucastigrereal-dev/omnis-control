from src.skill_execution.result import SkillExecutionResult, ExecutionStatus


class TestSkillExecutionResult:
    def test_default_result(self):
        r = SkillExecutionResult()
        assert r.result_id.startswith("srr_")
        assert r.status == ExecutionStatus.DRY_RUN_OK
        assert r.is_ok is True
        assert r.has_errors is False

    def test_blocked_result(self):
        r = SkillExecutionResult(status=ExecutionStatus.BLOCKED)
        assert r.is_ok is False

    def test_failed_with_errors(self):
        r = SkillExecutionResult(
            status=ExecutionStatus.FAILED,
            errors=["Something broke"],
        )
        assert r.has_errors is True

    def test_warnings_not_errors(self):
        r = SkillExecutionResult(
            status=ExecutionStatus.COMPLETED,
            warnings=["Deprecated parameter"],
        )
        assert r.has_errors is False
        assert r.is_ok is True

    def test_artifacts_collected(self):
        r = SkillExecutionResult(
            artifacts=[
                {"type": "file", "path": "output/caption.txt"},
                {"type": "json", "data": {"key": "val"}},
            ],
        )
        assert len(r.artifacts) == 2

    def test_logs_tracked(self):
        r = SkillExecutionResult(logs=["Step 1: parse", "Step 2: generate"])
        assert len(r.logs) == 2

    def test_next_action_set(self):
        r = SkillExecutionResult(next_action="Review generated content")
        assert r.next_action == "Review generated content"

    def test_roundtrip(self):
        r = SkillExecutionResult(
            request_id="ser_test",
            skill_id="seogram",
            status=ExecutionStatus.DRY_RUN_OK,
            summary="All good",
            warnings=["minor issue"],
            next_action="proceed",
            duration_ms=150,
        )
        data = r.to_dict()
        r2 = SkillExecutionResult.from_dict(data)
        assert r2.skill_id == "seogram"
        assert r2.status == ExecutionStatus.DRY_RUN_OK
        assert r2.warnings == ["minor issue"]
        assert r2.duration_ms == 150
