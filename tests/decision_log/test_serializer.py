import json
import pytest
from src.decision_log.models import LogEventType
from src.decision_log.serializer import LogSerializer
from src.decision_log.events import EventFactory


class TestLogSerializer:
    def test_to_json_from_json_round_trip(self):
        evt = EventFactory.decision_created(
            decision_id="dec_abc",
            summary="Test decision",
            project="omnis",
        )
        json_str = LogSerializer.to_json(evt)
        restored = LogSerializer.from_json(json_str)
        assert restored.to_dict()["decision_id"] == "dec_abc"
        assert restored.event.summary == "Test decision"

    def test_save_and_load(self, tmp_path):
        fp = str(tmp_path / "event.json")
        evt = EventFactory.execution_completed(
            item_id="eqi_xyz",
            tests_run=5,
            tests_passed=5,
        )
        LogSerializer.save(evt, fp)
        restored = LogSerializer.load(fp)
        assert restored.to_dict()["item_id"] == "eqi_xyz"
        assert restored.to_dict()["tests_run"] == 5

    def test_save_all_and_load_all(self, tmp_path):
        dirpath = str(tmp_path / "events")
        events = [
            EventFactory.decision_created(decision_id="d1"),
            EventFactory.work_order_parsed(order_id="wo1"),
            EventFactory.contract_validated(contract_id="c1"),
        ]
        LogSerializer.save_all(events, dirpath)
        loaded = LogSerializer.load_all(dirpath)
        assert len(loaded) == 3
        ids = {e.event.event_id for e in loaded}
        assert len(ids) == 3

    def test_load_all_empty_directory(self, tmp_path):
        dirpath = str(tmp_path / "empty")
        loaded = LogSerializer.load_all(dirpath)
        assert loaded == []

    def test_from_json_all_event_types(self):
        for factory_method, expected_type in [
            (EventFactory.decision_created, "DecisionCreated"),
            (EventFactory.work_order_parsed, "WorkOrderParsed"),
            (EventFactory.contract_validated, "ContractValidated"),
            (EventFactory.risk_blocked, "RiskBlocked"),
            (EventFactory.dry_run_completed, "DryRunCompleted"),
            (EventFactory.approval_required, "ApprovalRequired"),
            (EventFactory.execution_completed, "ExecutionCompleted"),
            (EventFactory.execution_failed, "ExecutionFailed"),
        ]:
            if factory_method == EventFactory.risk_blocked:
                evt = factory_method(risk_level="LOW", reason="test")
            elif factory_method == EventFactory.approval_required:
                evt = factory_method(item_id="x", risk_level="LOW")
            else:
                evt = factory_method()
            j = LogSerializer.to_json(evt)
            restored = LogSerializer.from_json(j)
            assert restored.event.event_type.value == expected_type

    def test_event_factory_creates_typed_events(self):
        evt = EventFactory.create(
            event_type=LogEventType.RISK_BLOCKED,
            risk_level="CRITICAL",
            reason="boundary violation",
            summary="Blocked by guard",
            project="omnis",
        )
        d = evt.to_dict()
        assert d["risk_level"] == "CRITICAL"
        assert d["reason"] == "boundary violation"
        assert d["summary"] == "Blocked by guard"

    def test_execution_failed_event_factory(self):
        evt = EventFactory.execution_failed(
            item_id="eqi_fail",
            error="division by zero",
            summary="Execution crashed",
        )
        d = evt.to_dict()
        assert d["item_id"] == "eqi_fail"
        assert d["error"] == "division by zero"

    def test_approval_required_event_factory(self):
        evt = EventFactory.approval_required(
            item_id="eqi_001",
            risk_level="HIGH",
            project="omnis",
        )
        d = evt.to_dict()
        assert d["item_id"] == "eqi_001"
        assert d["risk_level"] == "HIGH"
