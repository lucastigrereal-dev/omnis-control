"""Tests for WorkOrder models."""
from __future__ import annotations

import pytest

from src.work_order.models import (
    VALID_STATUS_TRANSITIONS,
    OutputContract,
    OutputEntry,
    OutputType,
    WorkOrder,
    WorkOrderStatus,
    make_output_id,
    make_work_order_id,
)


class TestWorkOrderStatus:
    def test_all_statuses_present(self):
        """All 10 statuses are defined."""
        expected = {
            "DRAFT", "READY", "BLOCKED", "APPROVED", "IN_PROGRESS_FUTURE",
            "OUTPUT_PENDING", "OUTPUT_SUBMITTED", "VALIDATED", "REJECTED", "CLOSED",
        }
        assert set(WorkOrderStatus.__members__) == expected

    def test_status_values_are_lowercase(self):
        for status in WorkOrderStatus:
            assert status.value == status.name.lower()


class TestOutputType:
    def test_all_output_types_present(self):
        """All 10 output types are defined."""
        expected = {
            "MARKDOWN", "JSON", "CSV", "HTML_PREVIEW", "ZIP_PACKAGE",
            "IMAGE_ASSET", "VIDEO_PLAN", "DELIVERY_PACKAGE",
            "MISSION_REPORT", "UNKNOWN",
        }
        assert set(OutputType.__members__) == expected


class TestIDGeneration:
    def test_work_order_id_prefix(self):
        for _ in range(10):
            assert make_work_order_id().startswith("wo_")

    def test_output_id_prefix(self):
        for _ in range(10):
            assert make_output_id().startswith("out_")

    def test_work_order_ids_are_unique(self):
        ids = {make_work_order_id() for _ in range(50)}
        assert len(ids) == 50

    def test_output_ids_are_unique(self):
        ids = {make_output_id() for _ in range(50)}
        assert len(ids) == 50


class TestOutputContract:
    def test_create_contract(self):
        c = OutputContract(
            contract_id="c01",
            output_type=OutputType.MARKDOWN,
            description="Texto do post",
        )
        assert c.contract_id == "c01"
        assert c.output_type == OutputType.MARKDOWN
        assert c.required is True
        assert c.min_count == 1
        assert c.max_count == 1

    def test_optional_contract(self):
        c = OutputContract(
            contract_id="c02",
            output_type=OutputType.JSON,
            description="Metadata",
            required=False,
            min_count=0,
            max_count=2,
        )
        assert c.required is False
        assert c.min_count == 0
        assert c.max_count == 2

    def test_to_dict(self):
        c = OutputContract("c01", OutputType.MARKDOWN, "Texto")
        d = c.to_dict()
        assert d["contract_id"] == "c01"
        assert d["output_type"] == "markdown"
        assert d["required"] is True

    def test_from_dict(self):
        d = {"contract_id": "c01", "output_type": "json", "description": "Dados"}
        c = OutputContract.from_dict(d)
        assert c.contract_id == "c01"
        assert c.output_type == OutputType.JSON


class TestOutputEntry:
    def test_create_entry(self):
        e = OutputEntry(
            output_id="out_abc",
            output_type=OutputType.MARKDOWN,
            contract_id="c01",
        )
        assert e.status == "submitted"

    def test_to_dict(self):
        e = OutputEntry("out_abc", OutputType.JSON, "c01", file_path="data.json")
        d = e.to_dict()
        assert d["file_path"] == "data.json"

    def test_from_dict(self):
        d = {"output_id": "out_xyz", "output_type": "json", "contract_id": "c02"}
        e = OutputEntry.from_dict(d)
        assert e.output_id == "out_xyz"
        assert e.output_type == OutputType.JSON


class TestWorkOrder:
    def test_create_minimal(self):
        wo = WorkOrder(
            work_order_id=make_work_order_id(),
            graph_step_id="step_abc",
            graph_run_id="grun_xyz",
            role="copywriter",
            step_label="Criar legenda",
        )
        assert wo.status == WorkOrderStatus.DRAFT
        assert wo.created_at != ""
        assert wo.updated_at != ""

    def test_default_contracts_and_outputs_empty(self):
        wo = WorkOrder(
            work_order_id=make_work_order_id(),
            graph_step_id="step_abc",
            graph_run_id="grun_xyz",
            role="copywriter",
            step_label="Test",
        )
        assert wo.contracts == []
        assert wo.outputs == []


class TestStatusTransitions:
    def make_wo(self, status: WorkOrderStatus) -> WorkOrder:
        return WorkOrder(
            work_order_id=make_work_order_id(),
            graph_step_id="step_abc",
            graph_run_id="grun_xyz",
            role="copywriter",
            step_label="Test",
            status=status,
        )

    def test_draft_to_ready(self):
        wo = self.make_wo(WorkOrderStatus.DRAFT)
        assert wo.can_transition_to(WorkOrderStatus.READY) is True
        wo = wo.transition_to(WorkOrderStatus.READY)
        assert wo.status == WorkOrderStatus.READY

    def test_draft_to_closed(self):
        wo = self.make_wo(WorkOrderStatus.DRAFT)
        assert wo.can_transition_to(WorkOrderStatus.CLOSED) is True

    def test_draft_cannot_go_to_validated(self):
        wo = self.make_wo(WorkOrderStatus.DRAFT)
        assert wo.can_transition_to(WorkOrderStatus.VALIDATED) is False

    def test_blocked_to_approved(self):
        wo = self.make_wo(WorkOrderStatus.BLOCKED)
        wo = wo.transition_to(WorkOrderStatus.APPROVED)
        assert wo.status == WorkOrderStatus.APPROVED

    def test_blocked_to_rejected(self):
        wo = self.make_wo(WorkOrderStatus.BLOCKED)
        wo = wo.transition_to(WorkOrderStatus.REJECTED)
        assert wo.status == WorkOrderStatus.REJECTED

    def test_rejected_back_to_output_pending(self):
        wo = self.make_wo(WorkOrderStatus.REJECTED)
        wo = wo.transition_to(WorkOrderStatus.OUTPUT_PENDING)
        assert wo.status == WorkOrderStatus.OUTPUT_PENDING

    def test_closed_is_terminal(self):
        wo = self.make_wo(WorkOrderStatus.CLOSED)
        for status in WorkOrderStatus:
            assert wo.can_transition_to(status) is False

    def test_invalid_transition_raises(self):
        wo = self.make_wo(WorkOrderStatus.DRAFT)
        with pytest.raises(ValueError, match="Cannot transition"):
            wo.transition_to(WorkOrderStatus.VALIDATED)

    def test_all_transitions_are_defined(self):
        """Every non-terminal status has at least one valid transition."""
        for status in WorkOrderStatus:
            assert status in VALID_STATUS_TRANSITIONS, f"Missing transitions for {status}"


class TestWorkOrderOutputs:
    def make_wo(self) -> WorkOrder:
        c = OutputContract("c01", OutputType.MARKDOWN, "Texto", required=True)
        return WorkOrder(
            work_order_id=make_work_order_id(),
            graph_step_id="step_abc",
            graph_run_id="grun_xyz",
            role="copywriter",
            step_label="Test",
            status=WorkOrderStatus.OUTPUT_PENDING,
            contracts=[c],
        )

    def test_add_output_updates_timestamp(self):
        wo = self.make_wo()
        old_ts = wo.updated_at
        e = OutputEntry("out_abc", OutputType.MARKDOWN, "c01")
        wo = wo.add_output(e)
        assert wo.updated_at >= old_ts

    def test_add_output_transitions_to_submitted_when_all_contracts_met(self):
        wo = self.make_wo()
        e = OutputEntry("out_abc", OutputType.MARKDOWN, "c01")
        wo = wo.add_output(e)
        assert wo.status == WorkOrderStatus.OUTPUT_SUBMITTED


class TestToDictRoundTrip:
    def test_full_roundtrip(self):
        wo = WorkOrder(
            work_order_id=make_work_order_id(),
            graph_step_id="step_abc",
            graph_run_id="grun_xyz",
            role="copywriter",
            step_label="Criar post",
            status=WorkOrderStatus.OUTPUT_PENDING,
            contracts=[
                OutputContract("c01", OutputType.MARKDOWN, "Texto"),
                OutputContract("c02", OutputType.JSON, "Meta", required=False, min_count=0),
            ],
            outputs=[
                OutputEntry("out_a", OutputType.MARKDOWN, "c01", file_path="post.md"),
            ],
            approval_id="appr_123",
            metadata={"priority": "high"},
        )
        d = wo.to_dict()
        wo2 = WorkOrder.from_dict(d)
        assert wo2.work_order_id == wo.work_order_id
        assert wo2.status == wo.status
        assert len(wo2.contracts) == 2
        assert len(wo2.outputs) == 1
        assert wo2.approval_id == "appr_123"
        assert wo2.metadata["priority"] == "high"
