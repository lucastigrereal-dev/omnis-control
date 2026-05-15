from src.observability.stage_events import StageEvent, StageStatus


class TestStageStatus:
    def test_all_statuses(self):
        assert StageStatus.PLANNED.value == "planned"
        assert StageStatus.STARTED.value == "started"
        assert StageStatus.IN_PROGRESS.value == "in_progress"
        assert StageStatus.COMPLETED.value == "completed"
        assert StageStatus.FAILED.value == "failed"
        assert StageStatus.SKIPPED.value == "skipped"
        assert StageStatus.BLOCKED.value == "blocked"

    def test_from_string(self):
        assert StageStatus("planned") == StageStatus.PLANNED
        assert StageStatus("failed") == StageStatus.FAILED


class TestStageEvent:
    def test_defaults(self):
        evt = StageEvent()
        assert evt.stage_id
        assert evt.status == StageStatus.PLANNED
        assert evt.trace_id == ""
        assert evt.span_id == ""
        assert evt.artifacts_produced == []
        assert evt.warnings == []
        assert evt.metadata == {}
        assert evt.timestamp

    def test_for_stage_minimal(self):
        evt = StageEvent.for_stage("build_package")
        assert evt.stage_name == "build_package"
        assert evt.trace_id
        assert evt.span_id
        assert evt.stage_id

    def test_for_stage_full(self):
        evt = StageEvent.for_stage(
            "deploy",
            phase="release",
            mission_id="m1",
            run_id="r1",
        )
        assert evt.stage_name == "deploy"
        assert evt.phase == "release"
        assert evt.mission_id == "m1"
        assert evt.run_id == "r1"

    def test_to_dict(self):
        evt = StageEvent(
            stage_name="test",
            phase="qa",
            status=StageStatus.COMPLETED,
            mission_id="m42",
            run_id="r7",
            duration_ms=150.5,
            artifacts_produced=["a.json"],
            warnings=["slow"],
            error="",
                   )
        d = evt.to_dict()
        assert d["stage_name"] == "test"
        assert d["phase"] == "qa"
        assert d["status"] == "completed"
        assert d["mission_id"] == "m42"
        assert d["run_id"] == "r7"
        assert d["duration_ms"] == 150.5
        assert d["artifacts_produced"] == ["a.json"]
        assert d["warnings"] == ["slow"]

    def test_to_dict_stage_id_present(self):
        evt = StageEvent.for_stage("x")
        d = evt.to_dict()
        assert d["stage_id"] == evt.stage_id
        assert d["trace_id"] == evt.trace_id
        assert d["span_id"] == evt.span_id

    def test_unique_ids(self):
        a = StageEvent.for_stage("a")
        b = StageEvent.for_stage("b")
        assert a.stage_id != b.stage_id
        assert a.trace_id != b.trace_id

    def test_error_field(self):
        evt = StageEvent(
            stage_name="boom",
            status=StageStatus.FAILED,
            error="connection refused",
        )
        assert evt.error == "connection refused"
        d = evt.to_dict()
        assert d["error"] == "connection refused"
