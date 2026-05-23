from src.runtime_orchestrator.service import OrchestratorService
from src.runtime_orchestrator.models import StepStatus


class TestOrchestratorService:
    def test_build_pipeline_has_nine_steps(self):
        svc = OrchestratorService(dry_run=True)
        pipeline = svc.build_pipeline()
        assert len(pipeline._steps) == 9

    def test_run_low_risk_order(self):
        svc = OrchestratorService(dry_run=True)
        result = svc.run({"order_id": "wro_test", "risk": "LOW"})
        assert result.is_success is True
        assert len(result.steps) == 9
        assert all(s.status == StepStatus.COMPLETED for s in result.steps)

    def test_run_high_risk_order(self):
        svc = OrchestratorService(dry_run=True)
        result = svc.run({"order_id": "wro_high", "risk": "HIGH"})
        assert result.is_success is True
        approval_step = [s for s in result.steps if s.name == "check_approval"][0]
        assert approval_step.output_data["approval"] == "PENDING"

    def test_run_medium_risk_order(self):
        svc = OrchestratorService(dry_run=True)
        result = svc.run({"order_id": "wro_med", "risk": "MEDIUM"})
        assert result.is_success is True
        risk_step = [s for s in result.steps if s.name == "evaluate_risk"][0]
        assert risk_step.output_data["requires_approval"] is True

    def test_service_dry_run_default(self):
        svc = OrchestratorService()
        assert svc.dry_run is True

    def test_result_is_dry_run(self):
        svc = OrchestratorService(dry_run=True)
        result = svc.run({"order_id": "wro_x", "risk": "LOW"})
        assert result.dry_run is True
