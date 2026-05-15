from src.runtime_orchestrator.pipeline import RuntimePipeline
from src.runtime_orchestrator.models import PipelineResult, StepStatus


class OrchestratorService:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run

    def build_pipeline(self) -> RuntimePipeline:
        pipeline = RuntimePipeline(dry_run=self.dry_run)
        pipeline.add_step("parse_order", self._parse_order)
        pipeline.add_step("validate_contract", self._validate_contract)
        pipeline.add_step("evaluate_risk", self._evaluate_risk)
        pipeline.add_step("check_approval", self._check_approval)
        pipeline.add_step("select_skill", self._select_skill)
        pipeline.add_step("execute_dryrun", self._execute_dryrun)
        pipeline.add_step("log_decision", self._log_decision)
        pipeline.add_step("sink_event", self._sink_event)
        pipeline.add_step("write_report", self._write_report)
        return pipeline

    def run(self, order_data: dict) -> PipelineResult:
        pipeline = self.build_pipeline()
        initial = pipeline._steps[0] if pipeline._steps else None
        if initial:
            initial.input_data = order_data
        return pipeline.execute()

    def _parse_order(self, data: dict) -> dict:
        return {"order_id": data.get("order_id", "unknown"), "parsed": True}

    def _validate_contract(self, data: dict) -> dict:
        return {"contract_valid": True, "order_id": data.get("order_id")}

    def _evaluate_risk(self, data: dict) -> dict:
        risk = data.get("risk", "LOW")
        if risk in ("HIGH", "CRITICAL"):
            return {"risk": risk, "blocked": False, "requires_approval": True}
        return {"risk": risk, "blocked": False, "requires_approval": risk == "MEDIUM"}

    def _check_approval(self, data: dict) -> dict:
        if data.get("requires_approval"):
            return {"approval": "PENDING", "message": "Awaiting human approval"}
        return {"approval": "AUTO_APPROVED"}

    def _select_skill(self, data: dict) -> dict:
        return {"selected_skill": "manual-review", "confidence": 0.5}

    def _execute_dryrun(self, data: dict) -> dict:
        return {"dry_run": True, "status": "DRY_RUN_OK", "skill": data.get("selected_skill")}

    def _log_decision(self, data: dict) -> dict:
        return {"logged": True, "event_type": "pipeline_execution"}

    def _sink_event(self, data: dict) -> dict:
        return {"sunk": True, "sink": "file"}

    def _write_report(self, data: dict) -> dict:
        return {"report_written": True, "format": "markdown"}
