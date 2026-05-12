"""Tests for OutputWriterService."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.output_generator.models import GeneratedOutputStatus
from src.output_generator.writer_service import OutputWriterService
from src.work_order.models import (
    OutputContract,
    OutputType,
    WorkOrder,
    WorkOrderStatus,
    make_work_order_id,
)


def _persist_wo(wo: WorkOrder, root: Path):
    wo_dir = root / wo.work_order_id
    wo_dir.mkdir(parents=True, exist_ok=True)
    manifest = wo_dir / "work_order.json"
    manifest.write_text(json.dumps(wo.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")


def _make_wo(**overrides) -> WorkOrder:
    defaults = {
        "work_order_id": make_work_order_id(),
        "graph_step_id": "step_01",
        "graph_run_id": "run_test",
        "role": "copywriter",
        "step_label": "Service Test Post",
        "status": WorkOrderStatus.APPROVED,
        "contracts": [
            OutputContract("c00", OutputType.MARKDOWN, "Texto do post", True),
        ],
        "metadata": {"expected_output": "Post", "request": "Test"},
    }
    defaults.update(overrides)
    return WorkOrder(**defaults)


class TestOutputWriterService:
    def test_write_generates_output(self, tmp_path: Path):
        wo = _make_wo()
        wo_root = tmp_path / "work_orders"
        out_root = tmp_path / "generated_outputs"
        _persist_wo(wo, wo_root)

        svc = OutputWriterService(work_orders_root=wo_root, outputs_root=out_root)
        result = svc.write(wo.work_order_id)

        assert result.status == GeneratedOutputStatus.GENERATED
        assert result.work_order_id == wo.work_order_id
        assert Path(result.file_path).exists()

    def test_write_creates_manifest(self, tmp_path: Path):
        wo = _make_wo()
        wo_root = tmp_path / "work_orders"
        out_root = tmp_path / "generated_outputs"
        _persist_wo(wo, wo_root)

        svc = OutputWriterService(work_orders_root=wo_root, outputs_root=out_root)
        result = svc.write(wo.work_order_id)

        manifest_path = Path(result.file_path).parent / "output_manifest.json"
        assert manifest_path.exists()

    def test_missing_work_order_raises(self, tmp_path: Path):
        svc = OutputWriterService(
            work_orders_root=tmp_path / "work_orders",
            outputs_root=tmp_path / "generated_outputs",
        )
        with pytest.raises(FileNotFoundError):
            svc.write("nonexistent_wo")

    def test_no_markdown_contract_blocks(self, tmp_path: Path):
        wo = _make_wo(contracts=[
            OutputContract("c00", OutputType.JSON, "JSON output", True),
        ])
        wo_root = tmp_path / "work_orders"
        out_root = tmp_path / "generated_outputs"
        _persist_wo(wo, wo_root)

        svc = OutputWriterService(work_orders_root=wo_root, outputs_root=out_root)
        result = svc.write(wo.work_order_id)

        assert result.status == GeneratedOutputStatus.UNSUPPORTED
        assert len(result.blockers) > 0
