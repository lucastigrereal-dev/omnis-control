from src.runtime_orchestrator.models import (
    PipelineStep,
    PipelineResult,
    StepStatus,
    _now_iso,
    _new_id,
)


class RuntimePipeline:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self._steps: list[PipelineStep] = []
        self._handlers: dict[str, callable] = {}

    def add_step(self, name: str, handler: callable) -> "RuntimePipeline":
        step = PipelineStep(name=name)
        self._steps.append(step)
        self._handlers[name] = handler
        return self

    def execute(self) -> PipelineResult:
        result = PipelineResult(dry_run=self.dry_run)
        steps_executed: list[PipelineStep] = []

        accumulated = {}
        for i, step in enumerate(self._steps):
            step.status = StepStatus.RUNNING
            step.started_at = _now_iso()
            handler = self._handlers.get(step.name)
            if handler is None:
                step.status = StepStatus.BLOCKED
                step.error = f"No handler for step: {step.name}"
                steps_executed.append(step)
                result.errors.append(step.error)
                result.status = StepStatus.BLOCKED
                break
            merged_input = {**accumulated, **step.input_data}
            try:
                output = handler(merged_input)
                step.output_data = output if isinstance(output, dict) else {"result": str(output)}
                step.status = StepStatus.COMPLETED
                accumulated.update(merged_input)
                accumulated.update(step.output_data)
            except Exception as e:
                step.status = StepStatus.FAILED
                step.error = str(e)
                result.errors.append(f"{step.name}: {e}")
            step.finished_at = _now_iso()
            steps_executed.append(step)

            if step.status == StepStatus.FAILED:
                result.status = StepStatus.FAILED
                break

            if i < len(self._steps) - 1:
                self._steps[i + 1].input_data = {**self._steps[i + 1].input_data, **accumulated}

        result.steps = steps_executed
        if result.status == StepStatus.PENDING:
            result.status = StepStatus.COMPLETED
        if steps_executed:
            result.final_output = steps_executed[-1].output_data
        return result
