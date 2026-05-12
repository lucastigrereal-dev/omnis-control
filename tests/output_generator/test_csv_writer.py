"""Tests for CSV output writer."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from src.output_generator.csv_writer import write_csv_output
from src.output_generator.models import GeneratedOutputStatus
from src.work_order.models import (
    OutputContract,
    OutputType,
    WorkOrder,
    WorkOrderStatus,
    make_work_order_id,
)


def _make_test_wo(**overrides) -> WorkOrder:
    defaults = {
        "work_order_id": make_work_order_id(),
        "graph_step_id": "step_01",
        "graph_run_id": "run_test",
        "role": "scheduler",
        "step_label": "Calendar Export",
        "status": WorkOrderStatus.APPROVED,
        "contracts": [
            OutputContract("c00", OutputType.CSV, "Export calendar as CSV", True),
        ],
        "metadata": {
            "expected_output": "CSV calendar export",
            "request": "Generate content calendar",
        },
    }
    defaults.update(overrides)
    return WorkOrder(**defaults)


class TestWriteCsvOutput:
    def test_generates_csv_file(self, tmp_path: Path):
        wo = _make_test_wo()
        result = write_csv_output(wo, tmp_path)

        assert result.status == GeneratedOutputStatus.GENERATED
        csv_file = Path(result.file_path)
        assert csv_file.exists()
        content = csv_file.read_text(encoding="utf-8")
        reader = csv.reader(content.splitlines())
        rows = list(reader)
        assert len(rows) >= 2  # header + data

    def test_csv_has_header(self, tmp_path: Path):
        wo = _make_test_wo()
        result = write_csv_output(wo, tmp_path)
        content = Path(result.file_path).read_text(encoding="utf-8")
        reader = csv.reader(content.splitlines())
        header = next(reader)
        assert "contract_id" in header or "date" in header

    def test_csv_contains_contract_data(self, tmp_path: Path):
        wo = _make_test_wo()
        result = write_csv_output(wo, tmp_path)
        content = Path(result.file_path).read_text(encoding="utf-8")
        assert wo.contracts[0].contract_id in content

    def test_csv_creates_manifest(self, tmp_path: Path):
        wo = _make_test_wo()
        result = write_csv_output(wo, tmp_path)
        manifest_path = Path(result.file_path).parent / "output_manifest.json"
        assert manifest_path.exists()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["output_type"] == "csv"

    def test_calendar_table_type(self, tmp_path: Path):
        wo = _make_test_wo()
        result = write_csv_output(wo, tmp_path, table_type="calendar")
        content = Path(result.file_path).read_text(encoding="utf-8")
        reader = csv.reader(content.splitlines())
        header = next(reader)
        assert "date" in header

    def test_queue_table_type(self, tmp_path: Path):
        wo = _make_test_wo()
        result = write_csv_output(wo, tmp_path, table_type="queue")
        content = Path(result.file_path).read_text(encoding="utf-8")
        reader = csv.reader(content.splitlines())
        header = next(reader)
        assert "priority" in header

    def test_fingerprint_is_generated(self, tmp_path: Path):
        wo = _make_test_wo()
        result = write_csv_output(wo, tmp_path)
        assert len(result.fingerprint) == 16

    def test_different_fingerprints_for_different_table_types(self, tmp_path: Path):
        wo = _make_test_wo()
        r1 = write_csv_output(wo, tmp_path / "a", table_type="list")
        r2 = write_csv_output(wo, tmp_path / "b", table_type="calendar")
        assert r1.fingerprint != r2.fingerprint

    def test_no_csv_contract_warns(self, tmp_path: Path):
        wo = _make_test_wo(contracts=[
            OutputContract("c00", OutputType.MARKDOWN, "Markdown output", True),
        ])
        result = write_csv_output(wo, tmp_path)
        assert result.status == GeneratedOutputStatus.GENERATED
        assert any("csv contract" in w.lower() for w in result.warnings)

    def test_can_customize_generator_id(self, tmp_path: Path):
        wo = _make_test_wo()
        result = write_csv_output(wo, tmp_path, generator_id="custom_csv")
        assert result.generator_id == "custom_csv"

    def test_does_not_call_network(self, tmp_path: Path):
        wo = _make_test_wo()
        result = write_csv_output(wo, tmp_path)
        assert result.status == GeneratedOutputStatus.GENERATED
        import inspect
        from src.output_generator import csv_writer as cw
        source = inspect.getsource(cw)
        assert "requests." not in source
        assert "urllib." not in source
        assert "httpx" not in source
