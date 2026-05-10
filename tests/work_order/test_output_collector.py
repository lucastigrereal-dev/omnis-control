"""Tests for P9.2 — Output Collector."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from src.work_order.models import (
    OutputContract,
    OutputEntry,
    OutputType,
    WorkOrder,
    WorkOrderStatus,
    make_work_order_id,
)
from src.work_order.output_collector import (
    DEFAULT_EXPORTS_ROOT,
    collect_output,
    collect_outputs_batch,
    list_collected_outputs,
    reject_output,
    validate_output,
)
from src.work_order.output_registry import OutputRegistry, OutputRegistryEntry


def make_wo(**overrides) -> WorkOrder:
    kwargs = dict(
        work_order_id=make_work_order_id(),
        graph_step_id="step_abc",
        graph_run_id="grun_xyz",
        role="copywriter",
        step_label="Criar legenda",
        status=WorkOrderStatus.OUTPUT_PENDING,
        contracts=[
            OutputContract("c01", OutputType.MARKDOWN, "Legenda", min_count=1),
            OutputContract("c02", OutputType.JSON, "Meta", required=False, min_count=0),
        ],
    )
    kwargs.update(overrides)
    return WorkOrder(**kwargs)


@pytest.fixture
def tmp_exports():
    d = tempfile.mkdtemp(prefix="p9_test_")
    yield Path(d)
    import shutil
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def tmp_registry_path():
    d = tempfile.mkdtemp(prefix="p9_reg_")
    p = Path(d) / "registry.json"
    yield p
    import shutil
    shutil.rmtree(d, ignore_errors=True)


class TestCollectOutput:
    def test_collect_markdown(self, tmp_exports):
        wo = make_wo()
        entry, path = collect_output(
            wo, OutputType.MARKDOWN, "# Meu Post\n\nConteudo aqui.",
            "c01", exports_root=tmp_exports,
        )
        assert entry.output_type == OutputType.MARKDOWN
        assert entry.status == "submitted"
        assert entry.contract_id == "c01"
        assert Path(path).exists()
        assert Path(path).read_text(encoding="utf-8").startswith("# Meu Post")

    def test_collect_updates_work_order(self, tmp_exports):
        wo = make_wo()
        entry, path = collect_output(
            wo, OutputType.MARKDOWN, "texto", "c01", exports_root=tmp_exports,
        )
        assert len(wo.outputs) == 1
        assert wo.outputs[0].output_id == entry.output_id

    def test_collect_persists_manifest(self, tmp_exports):
        wo = make_wo()
        collect_output(wo, OutputType.MARKDOWN, "texto", "c01", exports_root=tmp_exports)
        manifest = tmp_exports / wo.work_order_id / "work_order.json"
        assert manifest.exists()
        data = json.loads(manifest.read_text(encoding="utf-8"))
        assert data["status"] in ("output_pending", "output_submitted")

    def test_collect_dict_content(self, tmp_exports):
        wo = make_wo()
        content = {"title": "Post", "hashtags": ["viagem", "natal"]}
        entry, path = collect_output(
            wo, OutputType.JSON, content, "c02", exports_root=tmp_exports,
        )
        saved = json.loads(Path(path).read_text(encoding="utf-8"))
        assert saved["title"] == "Post"
        assert len(saved["hashtags"]) == 2

    def test_collect_bytes_content(self, tmp_exports):
        wo = make_wo()
        entry, path = collect_output(
            wo, OutputType.MARKDOWN, b"bytes content", "c01", exports_root=tmp_exports,
        )
        assert Path(path).read_text(encoding="utf-8") == "bytes content"

    def test_collect_with_registry(self, tmp_exports, tmp_registry_path):
        wo = make_wo()
        registry = OutputRegistry(entries=[], _file_path=tmp_registry_path)
        entry, path = collect_output(
            wo, OutputType.MARKDOWN, "text", "c01",
            exports_root=tmp_exports, registry=registry,
        )
        assert len(registry.entries) == 1
        assert registry.entries[0].output_id == entry.output_id

    def test_collect_transitions_to_submitted_when_all_done(self, tmp_exports):
        wo = make_wo(contracts=[
            OutputContract("c01", OutputType.MARKDOWN, "A", min_count=1),
        ])
        collect_output(wo, OutputType.MARKDOWN, "text", "c01", exports_root=tmp_exports)
        assert wo.status == WorkOrderStatus.OUTPUT_SUBMITTED


class TestCollectOutputsBatch:
    def test_collect_multiple(self, tmp_exports):
        wo = make_wo()
        results = collect_outputs_batch(wo, [
            (OutputType.MARKDOWN, "# Post", "c01"),
            (OutputType.JSON, {"key": "val"}, "c02"),
        ], exports_root=tmp_exports)
        assert len(results) == 2
        assert len(wo.outputs) == 2

    def test_collect_batch_with_registry(self, tmp_exports, tmp_registry_path):
        wo = make_wo()
        registry = OutputRegistry(entries=[], _file_path=tmp_registry_path)
        collect_outputs_batch(wo, [
            (OutputType.MARKDOWN, "# A", "c01"),
            (OutputType.JSON, {"k": "v"}, "c02"),
        ], exports_root=tmp_exports, registry=registry)
        assert len(registry.entries) == 2


class TestValidateOutput:
    def test_validate_existing_output(self, tmp_exports):
        wo = make_wo()
        entry, _ = collect_output(
            wo, OutputType.MARKDOWN, "text", "c01", exports_root=tmp_exports,
        )
        result = validate_output(wo, entry.output_id, exports_root=tmp_exports)
        assert result is not None
        assert result.status == "validated"
        assert result.validated_at is not None

    def test_validate_nonexistent_output(self, tmp_exports):
        wo = make_wo()
        result = validate_output(wo, "nonexistent", exports_root=tmp_exports)
        assert result is None

    def test_validate_with_registry(self, tmp_exports, tmp_registry_path):
        wo = make_wo()
        registry = OutputRegistry(entries=[], _file_path=tmp_registry_path)
        entry, _ = collect_output(
            wo, OutputType.MARKDOWN, "text", "c01",
            exports_root=tmp_exports, registry=registry,
        )
        validate_output(wo, entry.output_id, exports_root=tmp_exports, registry=registry)

        reg = OutputRegistry.load(tmp_registry_path)
        assert reg.entries[0].status == "validated"

    def test_validate_updates_manifest(self, tmp_exports):
        wo = make_wo()
        entry, _ = collect_output(
            wo, OutputType.MARKDOWN, "text", "c01", exports_root=tmp_exports,
        )
        validate_output(wo, entry.output_id, exports_root=tmp_exports)

        manifest = tmp_exports / wo.work_order_id / "work_order.json"
        data = json.loads(manifest.read_text(encoding="utf-8"))
        assert data["outputs"][0]["status"] == "validated"


class TestRejectOutput:
    def test_reject_existing_output(self, tmp_exports):
        wo = make_wo()
        entry, _ = collect_output(
            wo, OutputType.MARKDOWN, "text", "c01", exports_root=tmp_exports,
        )
        result = reject_output(wo, entry.output_id, exports_root=tmp_exports, notes="Bad format")
        assert result is not None
        assert result.status == "rejected"
        assert result.notes == "Bad format"

    def test_reject_nonexistent_output(self, tmp_exports):
        wo = make_wo()
        result = reject_output(wo, "nonexistent", exports_root=tmp_exports)
        assert result is None


class TestListCollectedOutputs:
    def test_list_returns_saved_outputs(self, tmp_exports):
        wo = make_wo()
        collect_output(wo, OutputType.MARKDOWN, "text", "c01", exports_root=tmp_exports)
        outputs = list_collected_outputs(wo.work_order_id, tmp_exports)
        assert len(outputs) == 1
        assert outputs[0].output_type == OutputType.MARKDOWN

    def test_list_nonexistent_work_order(self, tmp_exports):
        outputs = list_collected_outputs("wo_nonexistent", tmp_exports)
        assert outputs == []


class TestOutputRegistry:
    def test_load_and_save(self, tmp_registry_path):
        reg = OutputRegistry(entries=[], _file_path=tmp_registry_path)
        reg.add(OutputRegistryEntry(
            output_id="out_abc", work_order_id="wo_123",
            output_type=OutputType.MARKDOWN, contract_id="c01",
            status="submitted", disk_path="wo_123/output.md",
            submitted_at="2026-05-09T00:00:00Z",
        ))

        reg2 = OutputRegistry.load(tmp_registry_path)
        assert len(reg2.entries) == 1
        assert reg2.entries[0].output_id == "out_abc"

    def test_load_nonexistent_file(self, tmp_registry_path):
        reg = OutputRegistry.load(tmp_registry_path)
        assert reg.entries == []

    def test_find_by_work_order(self, tmp_registry_path):
        reg = OutputRegistry(entries=[], _file_path=tmp_registry_path)
        reg.add(OutputRegistryEntry("out_a", "wo_1", OutputType.MARKDOWN, "c01", "submitted", "", ""))
        reg.add(OutputRegistryEntry("out_b", "wo_2", OutputType.JSON, "c01", "submitted", "", ""))

        found = reg.find_by_work_order("wo_1")
        assert len(found) == 1
        assert found[0].output_id == "out_a"

    def test_find_by_type(self, tmp_registry_path):
        reg = OutputRegistry(entries=[], _file_path=tmp_registry_path)
        reg.add(OutputRegistryEntry("out_a", "wo_1", OutputType.MARKDOWN, "c01", "submitted", "", ""))
        reg.add(OutputRegistryEntry("out_b", "wo_1", OutputType.JSON, "c02", "submitted", "", ""))

        found = reg.find_by_type(OutputType.JSON)
        assert len(found) == 1

    def test_find_by_status(self, tmp_registry_path):
        reg = OutputRegistry(entries=[], _file_path=tmp_registry_path)
        reg.add(OutputRegistryEntry("out_a", "wo_1", OutputType.MARKDOWN, "c01", "submitted", "", ""))
        reg.add(OutputRegistryEntry("out_b", "wo_1", OutputType.JSON, "c02", "validated", "", ""))

        found = reg.find_by_status("validated")
        assert len(found) == 1

    def test_count_by_work_order(self, tmp_registry_path):
        reg = OutputRegistry(entries=[], _file_path=tmp_registry_path)
        reg.add(OutputRegistryEntry("out_a", "wo_1", OutputType.MARKDOWN, "c01", "submitted", "", ""))
        reg.add(OutputRegistryEntry("out_b", "wo_1", OutputType.JSON, "c02", "submitted", "", ""))
        reg.add(OutputRegistryEntry("out_c", "wo_2", OutputType.MARKDOWN, "c01", "submitted", "", ""))

        assert reg.count_by_work_order("wo_1") == 2
        assert reg.count_by_work_order("wo_2") == 1
