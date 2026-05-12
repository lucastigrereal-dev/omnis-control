"""Tests for package builder."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.output_generator.package_builder import build_package
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
        "role": "copywriter",
        "step_label": "Test Package",
        "status": WorkOrderStatus.APPROVED,
        "contracts": [
            OutputContract("c00", OutputType.MARKDOWN, "Post markdown", True),
        ],
        "metadata": {"expected_output": "Content", "request": "Create post"},
    }
    defaults.update(overrides)
    return WorkOrder(**defaults)


class TestBuildPackage:
    def test_build_package_creates_directory(self, tmp_path: Path):
        wo = _make_test_wo()
        pkg_dir, outputs, blockers = build_package(wo, tmp_path)
        assert pkg_dir.exists()
        assert pkg_dir.is_dir()

    def test_build_package_generates_markdown(self, tmp_path: Path):
        wo = _make_test_wo()
        pkg_dir, outputs, blockers = build_package(wo, tmp_path)
        assert len(outputs) >= 1
        md_outputs = [o for o in outputs if o.output_type == "markdown"]
        assert len(md_outputs) >= 1

    def test_build_package_writes_manifest(self, tmp_path: Path):
        wo = _make_test_wo()
        pkg_dir, outputs, blockers = build_package(wo, tmp_path)
        manifest_path = pkg_dir / "package_manifest.json"
        assert manifest_path.exists()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["work_order_id"] == wo.work_order_id

    def test_build_package_multi_contract(self, tmp_path: Path):
        wo = _make_test_wo(contracts=[
            OutputContract("c00", OutputType.MARKDOWN, "Markdown post", True),
            OutputContract("c01", OutputType.JSON, "JSON export", True),
        ])
        pkg_dir, outputs, blockers = build_package(wo, tmp_path)
        types = {o.output_type for o in outputs}
        assert "markdown" in types
        assert "json" in types

    def test_build_package_csv_contract(self, tmp_path: Path):
        wo = _make_test_wo(contracts=[
            OutputContract("c00", OutputType.CSV, "CSV calendar", True),
        ])
        pkg_dir, outputs, blockers = build_package(wo, tmp_path)
        assert len(outputs) >= 1
        csv_outputs = [o for o in outputs if o.output_type == "csv"]
        assert len(csv_outputs) >= 1

    def test_build_package_no_blockers_for_valid_contracts(self, tmp_path: Path):
        wo = _make_test_wo()
        pkg_dir, outputs, blockers = build_package(wo, tmp_path)
        assert len(blockers) == 0

    def test_build_package_manifest_counts_files(self, tmp_path: Path):
        wo = _make_test_wo(contracts=[
            OutputContract("c00", OutputType.MARKDOWN, "MD", True),
            OutputContract("c01", OutputType.JSON, "JSON", True),
            OutputContract("c02", OutputType.CSV, "CSV", True),
        ])
        pkg_dir, outputs, blockers = build_package(wo, tmp_path)
        manifest = json.loads((pkg_dir / "package_manifest.json").read_text(encoding="utf-8"))
        assert manifest["file_count"] == len(outputs)

    def test_build_package_all_outputs_exist_on_disk(self, tmp_path: Path):
        wo = _make_test_wo(contracts=[
            OutputContract("c00", OutputType.MARKDOWN, "MD", True),
            OutputContract("c01", OutputType.JSON, "JSON", True),
        ])
        pkg_dir, outputs, blockers = build_package(wo, tmp_path)
        for o in outputs:
            assert Path(o.file_path).exists()

    def test_package_ids_are_unique(self, tmp_path: Path):
        wo1 = _make_test_wo()
        wo2 = _make_test_wo()
        d1, _, _ = build_package(wo1, tmp_path / "a")
        d2, _, _ = build_package(wo2, tmp_path / "b")
        assert d1.name != d2.name
