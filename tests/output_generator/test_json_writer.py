"""Tests for JSON and Spec output writers."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.output_generator.json_writer import write_json_output, write_spec_output
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
        "role": "analyst",
        "step_label": "Data Export Task",
        "status": WorkOrderStatus.APPROVED,
        "contracts": [
            OutputContract("c00", OutputType.JSON, "Export data as JSON", True),
        ],
        "metadata": {
            "expected_output": "Structured JSON export of task results",
            "request": "Export analytics data",
        },
    }
    defaults.update(overrides)
    return WorkOrder(**defaults)


def _make_spec_wo(**overrides) -> WorkOrder:
    defaults = {
        "work_order_id": make_work_order_id(),
        "graph_step_id": "step_s1",
        "graph_run_id": "run_spec",
        "role": "architect",
        "step_label": "API Spec",
        "status": WorkOrderStatus.APPROVED,
        "contracts": [
            OutputContract("c00", OutputType.UNKNOWN, "Technical specification", True),
        ],
        "metadata": {
            "expected_output": "REST API technical specification",
            "spec_type": "technical_spec",
        },
    }
    defaults.update(overrides)
    # Fix contract output_type since OutputType doesn't have TECHNICAL_SPEC
    return WorkOrder(**defaults)


def _make_spec_wo_technical(**overrides) -> WorkOrder:
    defaults = {
        "work_order_id": make_work_order_id(),
        "graph_step_id": "step_s1",
        "graph_run_id": "run_spec",
        "role": "architect",
        "step_label": "API Design Spec",
        "status": WorkOrderStatus.APPROVED,
        "contracts": [
            OutputContract("c00", OutputType.JSON, "API specification document", True),
        ],
        "metadata": {
            "expected_output": "REST API technical specification",
            "spec_type": "technical_spec",
        },
    }
    defaults.update(overrides)
    return WorkOrder(**defaults)


class TestWriteJsonOutput:
    def test_generates_json_file(self, tmp_path: Path):
        wo = _make_test_wo()
        result = write_json_output(wo, tmp_path)

        assert result.status == GeneratedOutputStatus.GENERATED
        json_file = Path(result.file_path)
        assert json_file.exists()
        content = json.loads(json_file.read_text(encoding="utf-8"))
        assert content["work_order"]["work_order_id"] == wo.work_order_id

    def test_json_contains_contracts(self, tmp_path: Path):
        wo = _make_test_wo()
        result = write_json_output(wo, tmp_path)
        content = json.loads(Path(result.file_path).read_text(encoding="utf-8"))
        assert len(content["contracts"]) == 1
        assert content["contracts"][0]["output_type"] == "json"

    def test_json_contains_metadata(self, tmp_path: Path):
        wo = _make_test_wo()
        result = write_json_output(wo, tmp_path)
        content = json.loads(Path(result.file_path).read_text(encoding="utf-8"))
        assert content["metadata"]["expected_output"] == "Structured JSON export of task results"

    def test_json_creates_manifest(self, tmp_path: Path):
        wo = _make_test_wo()
        result = write_json_output(wo, tmp_path)
        manifest_path = Path(result.file_path).parent / "output_manifest.json"
        assert manifest_path.exists()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["output_type"] == "json"
        assert manifest["generator_id"] == "json_basic_writer"

    def test_json_fingerprint_is_stable(self, tmp_path: Path):
        wo = _make_test_wo()
        result = write_json_output(wo, tmp_path)
        assert len(result.fingerprint) == 16

    def test_json_different_fingerprints_for_different_content(self, tmp_path: Path):
        wo1 = _make_test_wo(step_label="A")
        wo2 = _make_test_wo(step_label="B")
        r1 = write_json_output(wo1, tmp_path / "a")
        r2 = write_json_output(wo2, tmp_path / "b")
        assert r1.fingerprint != r2.fingerprint

    def test_json_no_contract_warns(self, tmp_path: Path):
        wo = _make_test_wo(contracts=[
            OutputContract("c00", OutputType.MARKDOWN, "Markdown output", True),
        ])
        result = write_json_output(wo, tmp_path)
        assert result.status == GeneratedOutputStatus.GENERATED
        assert any("json contract" in w.lower() for w in result.warnings)

    def test_json_does_not_call_network(self, tmp_path: Path):
        wo = _make_test_wo()
        result = write_json_output(wo, tmp_path)
        assert result.status == GeneratedOutputStatus.GENERATED
        import inspect
        from src.output_generator import json_writer as jw
        source = inspect.getsource(jw)
        assert "requests." not in source
        assert "urllib." not in source
        assert "httpx" not in source


class TestWriteSpecOutput:
    def test_generates_spec_file(self, tmp_path: Path):
        wo = _make_spec_wo_technical()
        result = write_spec_output(wo, tmp_path)

        assert result.status == GeneratedOutputStatus.GENERATED
        spec_file = Path(result.file_path)
        assert spec_file.exists()
        content = json.loads(spec_file.read_text(encoding="utf-8"))
        assert content["spec"]["spec_id"] == wo.work_order_id

    def test_spec_contains_requirements(self, tmp_path: Path):
        wo = _make_spec_wo_technical()
        result = write_spec_output(wo, tmp_path)
        content = json.loads(Path(result.file_path).read_text(encoding="utf-8"))
        assert len(content["requirements"]) >= 1
        assert "description" in content["requirements"][0]

    def test_spec_contains_sections(self, tmp_path: Path):
        wo = _make_spec_wo_technical()
        result = write_spec_output(wo, tmp_path)
        content = json.loads(Path(result.file_path).read_text(encoding="utf-8"))
        assert "sections" in content
        assert "overview" in content["sections"]
        assert "acceptance_criteria" in content["sections"]

    def test_spec_creates_manifest(self, tmp_path: Path):
        wo = _make_spec_wo_technical()
        result = write_spec_output(wo, tmp_path)
        manifest_path = Path(result.file_path).parent / "output_manifest.json"
        assert manifest_path.exists()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["generator_id"] == "spec_basic_writer"

    def test_spec_no_contract_generates_anyway(self, tmp_path: Path):
        wo = _make_spec_wo_technical(contracts=[
            OutputContract("c00", OutputType.MARKDOWN, "Markdown output", True),
        ])
        result = write_spec_output(wo, tmp_path)
        assert result.status == GeneratedOutputStatus.GENERATED
        assert any("spec contract" in w.lower() for w in result.warnings)

    def test_spec_can_customize_generator_id(self, tmp_path: Path):
        wo = _make_spec_wo_technical()
        result = write_spec_output(wo, tmp_path, generator_id="custom_spec")
        assert result.generator_id == "custom_spec"
