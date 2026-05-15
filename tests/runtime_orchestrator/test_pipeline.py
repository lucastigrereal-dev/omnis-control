from src.runtime_orchestrator.pipeline import RuntimePipeline
from src.runtime_orchestrator.models import StepStatus


class TestRuntimePipeline:
    def test_execute_single_step(self):
        pipeline = RuntimePipeline(dry_run=True)
        pipeline.add_step("step1", lambda d: {"result": "ok"})
        result = pipeline.execute()
        assert result.is_success is True
        assert len(result.steps) == 1
        assert result.steps[0].status == StepStatus.COMPLETED
        assert result.steps[0].output_data == {"result": "ok"}

    def test_execute_multiple_steps(self):
        pipeline = RuntimePipeline(dry_run=True)
        pipeline.add_step("a", lambda d: {"from": "a"})
        pipeline.add_step("b", lambda d: {"from": "b"})
        result = pipeline.execute()
        assert len(result.steps) == 2
        assert result.steps[0].status == StepStatus.COMPLETED
        assert result.steps[1].status == StepStatus.COMPLETED

    def test_step_failure_stops_pipeline(self):
        pipeline = RuntimePipeline(dry_run=True)
        pipeline.add_step("good", lambda d: {"ok": True})
        pipeline.add_step("bad", lambda d: (_ for _ in ()).throw(Exception("boom")))
        pipeline.add_step("never_runs", lambda d: {"missed": True})
        result = pipeline.execute()
        assert result.status == StepStatus.FAILED
        assert len(result.steps) == 2
        assert result.steps[1].status == StepStatus.FAILED
        assert len(result.failed_steps) == 1

    def test_missing_handler_blocks(self):
        pipeline = RuntimePipeline(dry_run=True)
        step = pipeline.add_step("orphan", None)
        pipeline._handlers.pop("orphan", None)
        result = pipeline.execute()
        assert result.status == StepStatus.BLOCKED
        assert result.steps[0].status == StepStatus.BLOCKED

    def test_final_output_is_last_step(self):
        pipeline = RuntimePipeline(dry_run=True)
        pipeline.add_step("first", lambda d: {"a": 1})
        pipeline.add_step("last", lambda d: {"z": 99})
        result = pipeline.execute()
        assert result.final_output == {"z": 99}

    def test_dry_run_flag(self):
        pipeline = RuntimePipeline(dry_run=True)
        assert pipeline.dry_run is True
        pipeline.add_step("s", lambda d: {})
        result = pipeline.execute()
        assert result.dry_run is True
