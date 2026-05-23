import pytest
from src.omnis_control.pipeline import OmnisPipeline


LOW_RISK_WORK_ORDER = """---
title: Fix bug in login flow
aba: aba-0
type: bugfix
status: READY
risk: LOW
project: omnis-control
allowed_paths: src/auth/, tests/auth/
forbidden_paths: .kratos/
requires_approval: false
dry_run: true
---

Investigate and fix the login redirect issue.
"""

HIGH_RISK_WORK_ORDER = """---
title: Deploy to production
aba: aba-0
type: deploy
status: DRAFT
risk: HIGH
project: omnis-control
allowed_paths: src/
forbidden_paths: .kratos/,.env
requires_approval: true
dry_run: false
---

Deploy the latest changes to production environment.
"""

INVALID_WORK_ORDER = """---
title:
aba: aba-0
type:
status: READY
risk: LOW
project:
allowed_paths:
---

Empty fields.
"""


class TestOmnisPipeline:
    @pytest.fixture
    def pipeline(self):
        return OmnisPipeline(dry_run=True)

    def test_happy_path_low_risk_work_order(self, pipeline):
        result = pipeline.execute(LOW_RISK_WORK_ORDER, project="omnis-test")
        assert result.success is True
        assert result.work_order_id.startswith("wo_")
        assert result.contract_id.startswith("exc_")
        assert result.decision_id.startswith("ctd_")
        assert result.skill_selection_id.startswith("sks_")
        assert result.queue_item_id.startswith("eqi_")
        assert result.queue_result_status == "DONE"
        assert len(result.events) >= 4

    def test_high_risk_without_approval_is_blocked_by_validator(self, pipeline):
        result = pipeline.execute(HIGH_RISK_WORK_ORDER, project="omnis-test")
        assert result.success is False
        has_block = any("validation" in e.lower() or "blocked" in e.lower() for e in result.errors)
        assert has_block or len(result.errors) > 0

    def test_invalid_work_order_returns_errors(self, pipeline):
        result = pipeline.execute(INVALID_WORK_ORDER, project="omnis-test")
        assert result.success is False
        assert len(result.errors) > 0

    def test_pipeline_generates_event_log(self, pipeline):
        result = pipeline.execute(LOW_RISK_WORK_ORDER, project="omnis-test")
        assert result.success is True
        event_types = [e.event_type.value for e in result.events]
        assert "WorkOrderParsed" in event_types
        assert "ContractValidated" in event_types
        assert "DryRunCompleted" in event_types
        assert "ExecutionCompleted" in event_types

    def test_pipeline_result_to_dict(self, pipeline):
        result = pipeline.execute(LOW_RISK_WORK_ORDER, project="omnis-test")
        d = result.to_dict()
        assert d["success"] is True
        assert d["work_order_id"].startswith("wo_")
        assert d["contract_id"].startswith("exc_")

    def test_get_event_log(self, pipeline):
        pipeline.execute(LOW_RISK_WORK_ORDER, project="omnis-test")
        events = pipeline.get_event_log()
        assert len(events) > 0
        assert all(hasattr(e, "event_type") for e in events)

    def test_multiple_executions_independent(self, pipeline):
        r1 = pipeline.execute(LOW_RISK_WORK_ORDER, project="omnis-a")
        r2 = pipeline.execute(LOW_RISK_WORK_ORDER, project="omnis-b")
        assert r1.success is True
        assert r2.success is True
        assert r1.work_order_id != r2.work_order_id

    def test_approval_required_work_order(self, pipeline):
        wo = """---
title: Sensitive data migration
aba: aba-0
type: migration
status: READY
risk: MEDIUM
project: omnis-control
allowed_paths: src/data/
forbidden_paths: .kratos/
requires_approval: true
dry_run: true
---

Migrate sensitive user data to new schema.
"""
        result = pipeline.execute(wo, project="omnis-test")
        assert result.success is False
        assert "requires approval" in result.errors[0].lower()
