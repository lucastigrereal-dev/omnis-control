import json
import pytest
from src.decision_log.models import (
    LogEvent,
    LogEventType,
    BaseEvent,
    DecisionCreatedEvent,
    WorkOrderParsedEvent,
    ContractValidatedEvent,
    RiskBlockedEvent,
    DryRunCompletedEvent,
    ApprovalRequiredEvent,
    ExecutionCompletedEvent,
    ExecutionFailedEvent,
)


class TestLogEvent:
    def test_defaults(self):
        event = LogEvent()
        assert event.event_id.startswith("evt_")
        assert event.event_type == LogEventType.DECISION_CREATED
        assert event.source == "omnis"

    def test_to_dict_round_trip(self):
        event = LogEvent(
            summary="Test event",
            project="omnis-test",
            correlation_id="corr_abc123",
            evidence={"key": "value"},
            next_action="verify",
        )
        data = event.to_dict()
        restored = LogEvent.from_dict(data)
        assert restored.event_id == event.event_id
        assert restored.summary == "Test event"
        assert restored.project == "omnis-test"
        assert restored.evidence == {"key": "value"}
        assert restored.next_action == "verify"


class TestBaseEvent:
    def test_to_dict_includes_event_fields(self):
        event = BaseEvent()
        d = event.to_dict()
        assert "event_id" in d
        assert "event_type" in d
        assert d["event_type"] == "DecisionCreated"

    def test_to_json_produces_valid_json(self):
        event = BaseEvent()
        j = event.to_json()
        data = json.loads(j)
        assert data["event_type"] == "DecisionCreated"


class TestEventSubclasses:
    def test_decision_created_event(self):
        evt = DecisionCreatedEvent(decision_id="dec_123")
        d = evt.to_dict()
        assert d["decision_id"] == "dec_123"

    def test_work_order_parsed_event(self):
        evt = WorkOrderParsedEvent(order_id="wo_456")
        d = evt.to_dict()
        assert d["order_id"] == "wo_456"

    def test_contract_validated_event(self):
        evt = ContractValidatedEvent(contract_id="exc_789")
        d = evt.to_dict()
        assert d["contract_id"] == "exc_789"

    def test_risk_blocked_event(self):
        evt = RiskBlockedEvent(risk_level="CRITICAL", reason="destructive write")
        d = evt.to_dict()
        assert d["risk_level"] == "CRITICAL"
        assert d["reason"] == "destructive write"

    def test_dry_run_completed_event(self):
        evt = DryRunCompletedEvent(request_id="skc_001")
        d = evt.to_dict()
        assert d["request_id"] == "skc_001"

    def test_approval_required_event(self):
        evt = ApprovalRequiredEvent(item_id="eqi_abc", risk_level="HIGH")
        d = evt.to_dict()
        assert d["item_id"] == "eqi_abc"
        assert d["risk_level"] == "HIGH"

    def test_execution_completed_event(self):
        evt = ExecutionCompletedEvent(item_id="eqi_xyz", tests_run=10, tests_passed=9)
        d = evt.to_dict()
        assert d["item_id"] == "eqi_xyz"
        assert d["tests_run"] == 10
        assert d["tests_passed"] == 9

    def test_execution_failed_event(self):
        evt = ExecutionFailedEvent(item_id="eqi_err", error="timeout")
        d = evt.to_dict()
        assert d["item_id"] == "eqi_err"
        assert d["error"] == "timeout"

    def test_all_events_extend_base_event(self):
        subclasses = [
            DecisionCreatedEvent,
            WorkOrderParsedEvent,
            ContractValidatedEvent,
            RiskBlockedEvent,
            DryRunCompletedEvent,
            ApprovalRequiredEvent,
            ExecutionCompletedEvent,
            ExecutionFailedEvent,
        ]
        for cls in subclasses:
            instance = cls()
            assert isinstance(instance, BaseEvent)
            assert hasattr(instance, "to_json")
