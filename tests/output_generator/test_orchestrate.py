"""Tests for P10.8 — Work Order → Output Package orchestrator."""
from __future__ import annotations

import json
from pathlib import Path

from src.output_generator.manifest_registry import ManifestRegistry
from src.output_generator.writer_service import OutputWriterService


def _make_work_order(wo_root: Path, wo_id: str, contracts=None):
    wo_dir = wo_root / wo_id
    wo_dir.mkdir(parents=True)
    wo_data = {
        "work_order_id": wo_id,
        "graph_step_id": "step_01",
        "graph_run_id": "run_01",
        "role": "content_producer",
        "step_label": "Test Step",
        "status": "ready",
        "contracts": contracts or [
            {"contract_id": "c01", "output_type": "markdown", "description": "md file", "required": True, "min_count": 1, "max_count": 1},
        ],
        "outputs": [],
        "approval_id": None,
        "created_at": "2026-05-12T00:00:00Z",
        "updated_at": "2026-05-12T00:00:00Z",
        "metadata": {},
    }
    (wo_dir / "work_order.json").write_text(json.dumps(wo_data), encoding="utf-8")
    return wo_dir


class TestOrchestrate:
    def test_orchestrate_generates_and_registers(self, tmp_path: Path):
        wo_root = tmp_path / "work_orders"
        out_root = tmp_path / "outputs"
        reg_path = tmp_path / "registry.jsonl"

        _make_work_order(wo_root, "wo_01", contracts=[
            {"contract_id": "c01", "output_type": "markdown", "description": "md file", "required": True, "min_count": 1, "max_count": 1},
        ])

        service = OutputWriterService(
            work_orders_root=wo_root,
            outputs_root=out_root,
            manifest_registry=ManifestRegistry(reg_path),
        )
        result = service.orchestrate("wo_01")

        assert result["work_order_id"] == "wo_01"
        assert result["package_dir"].startswith(str(out_root))
        assert result["registered"] >= 1
        assert result["valid"] is True
        assert len(result["outputs"]) >= 1

    def test_orchestrate_registry_persists(self, tmp_path: Path):
        wo_root = tmp_path / "work_orders"
        out_root = tmp_path / "outputs"
        reg_path = tmp_path / "registry.jsonl"

        _make_work_order(wo_root, "wo_01", contracts=[
            {"contract_id": "c01", "output_type": "markdown", "description": "md file", "required": True, "min_count": 1, "max_count": 1},
        ])

        service = OutputWriterService(
            work_orders_root=wo_root,
            outputs_root=out_root,
            manifest_registry=ManifestRegistry(reg_path),
        )
        service.orchestrate("wo_01")

        # Verify registry has entries
        reg = ManifestRegistry(reg_path)
        assert reg.count() >= 1
        entries = reg.list_by_work_order("wo_01")
        assert len(entries) >= 1

    def test_orchestrate_runs_validation(self, tmp_path: Path):
        wo_root = tmp_path / "work_orders"
        out_root = tmp_path / "outputs"
        reg_path = tmp_path / "registry.jsonl"

        _make_work_order(wo_root, "wo_01", contracts=[
            {"contract_id": "c01", "output_type": "markdown", "description": "md file", "required": True, "min_count": 1, "max_count": 1},
        ])

        service = OutputWriterService(
            work_orders_root=wo_root,
            outputs_root=out_root,
            manifest_registry=ManifestRegistry(reg_path),
        )
        result = service.orchestrate("wo_01")

        assert "validation_checks" in result
        assert len(result["validation_checks"]) >= 3
        check_names = [c["name"] for c in result["validation_checks"]]
        assert "registry_entries" in check_names
        assert "file_existence" in check_names

    def test_package_auto_registers(self, tmp_path: Path):
        wo_root = tmp_path / "work_orders"
        out_root = tmp_path / "outputs"
        reg_path = tmp_path / "registry.jsonl"

        _make_work_order(wo_root, "wo_01", contracts=[
            {"contract_id": "c01", "output_type": "markdown", "description": "md file", "required": True, "min_count": 1, "max_count": 1},
        ])

        service = OutputWriterService(
            work_orders_root=wo_root,
            outputs_root=out_root,
            manifest_registry=ManifestRegistry(reg_path),
        )
        pkg_dir, outputs, blockers = service.package("wo_01")

        assert len(outputs) >= 1
        assert len(blockers) == 0
        # Check registry was updated
        reg = ManifestRegistry(reg_path)
        assert reg.count() >= 1

    def test_orchestrate_multi_contract(self, tmp_path: Path):
        wo_root = tmp_path / "work_orders"
        out_root = tmp_path / "outputs"
        reg_path = tmp_path / "registry.jsonl"

        _make_work_order(wo_root, "wo_01", contracts=[
            {"contract_id": "c01", "output_type": "markdown", "description": "md file", "required": True, "min_count": 1, "max_count": 1},
            {"contract_id": "c02", "output_type": "json", "description": "json file", "required": True, "min_count": 1, "max_count": 1},
        ])

        service = OutputWriterService(
            work_orders_root=wo_root,
            outputs_root=out_root,
            manifest_registry=ManifestRegistry(reg_path),
        )
        result = service.orchestrate("wo_01")

        types = {o["output_type"] for o in result["outputs"]}
        assert "markdown" in types
        assert "json" in types
        assert result["registered"] >= 2

    def test_work_order_not_found(self, tmp_path: Path):
        service = OutputWriterService(
            work_orders_root=tmp_path / "work_orders",
            outputs_root=tmp_path / "outputs",
        )
        with __import__("pytest").raises(FileNotFoundError):
            service.package("wo_ghost")

    def test_orchestrate_result_structure(self, tmp_path: Path):
        wo_root = tmp_path / "work_orders"
        out_root = tmp_path / "outputs"
        reg_path = tmp_path / "registry.jsonl"

        _make_work_order(wo_root, "wo_01")

        service = OutputWriterService(
            work_orders_root=wo_root,
            outputs_root=out_root,
            manifest_registry=ManifestRegistry(reg_path),
        )
        result = service.orchestrate("wo_01")

        required_keys = [
            "work_order_id", "package_dir", "outputs", "blockers",
            "registered", "valid", "validation_checks",
            "validation_issues", "validation_warnings",
        ]
        for key in required_keys:
            assert key in result, f"Missing key: {key}"

    def test_work_order_no_contracts_generates_markdown(self, tmp_path: Path):
        wo_root = tmp_path / "work_orders"
        out_root = tmp_path / "outputs"
        reg_path = tmp_path / "registry.jsonl"

        _make_work_order(wo_root, "wo_01", contracts=[])

        service = OutputWriterService(
            work_orders_root=wo_root,
            outputs_root=out_root,
            manifest_registry=ManifestRegistry(reg_path),
        )
        result = service.orchestrate("wo_01")

        assert len(result["outputs"]) >= 1
        # Default fallback to markdown
        assert result["outputs"][0]["output_type"] == "markdown"
