"""Tests for batch output generator (P10.9)."""
from __future__ import annotations

import json
from pathlib import Path

from src.output_generator.batch_runner import run_batch
from src.output_generator.manifest_registry import ManifestRegistry
from src.output_generator.writer_service import OutputWriterService


def _make_work_order(wo_root: Path, wo_id: str, status="ready", contracts=None):
    wo_dir = wo_root / wo_id
    wo_dir.mkdir(parents=True)
    wo_data = {
        "work_order_id": wo_id,
        "graph_step_id": "step_01",
        "graph_run_id": "run_01",
        "role": "content_producer",
        "step_label": "Test Step",
        "status": status,
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


class TestRunBatch:
    def test_no_work_orders_root(self, tmp_path: Path):
        result = run_batch(work_orders_root=tmp_path / "nonexistent")
        assert result["total_candidates"] == 0
        assert len(result["warnings"]) >= 1

    def test_empty_root(self, tmp_path: Path):
        wo_root = tmp_path / "work_orders"
        wo_root.mkdir()
        result = run_batch(work_orders_root=wo_root)
        assert result["total_candidates"] == 0
        assert result["processed"] == 0

    def test_dry_run_processes_wo(self, tmp_path: Path):
        wo_root = tmp_path / "work_orders"
        out_root = tmp_path / "outputs"
        _make_work_order(wo_root, "wo_01")
        _make_work_order(wo_root, "wo_02")

        result = run_batch(work_orders_root=wo_root, outputs_root=out_root, dry_run=True)
        assert result["total_candidates"] == 2
        assert result["processed"] == 2
        assert result["dry_run"] is True
        assert result["registered"] == 0  # dry-run doesn't register

    def test_dry_run_does_not_write_files(self, tmp_path: Path):
        wo_root = tmp_path / "work_orders"
        out_root = tmp_path / "outputs"
        _make_work_order(wo_root, "wo_01")

        result = run_batch(work_orders_root=wo_root, outputs_root=out_root, dry_run=True)
        # Check no outputs were written
        md_files = list(out_root.glob("**/*.md")) if out_root.exists() else []
        assert len(md_files) == 0

    def test_live_mode_generates_outputs(self, tmp_path: Path):
        wo_root = tmp_path / "work_orders"
        out_root = tmp_path / "outputs"
        _make_work_order(wo_root, "wo_01")

        result = run_batch(work_orders_root=wo_root, outputs_root=out_root, dry_run=False)
        assert result["processed"] >= 1
        assert result["registered"] >= 1
        assert result["dry_run"] is False

    def test_status_filter(self, tmp_path: Path):
        wo_root = tmp_path / "work_orders"
        out_root = tmp_path / "outputs"
        _make_work_order(wo_root, "wo_01", status="approved")
        _make_work_order(wo_root, "wo_02", status="draft")
        _make_work_order(wo_root, "wo_03", status="approved")

        result = run_batch(work_orders_root=wo_root, outputs_root=out_root, status_filter="approved", dry_run=True)
        assert result["total_candidates"] == 2
        assert result["status_filter"] == "approved"

    def test_limit(self, tmp_path: Path):
        wo_root = tmp_path / "work_orders"
        out_root = tmp_path / "outputs"
        for i in range(10):
            _make_work_order(wo_root, f"wo_{i:02d}")

        result = run_batch(work_orders_root=wo_root, outputs_root=out_root, dry_run=True, limit=3)
        assert result["total_candidates"] == 3

    def test_result_structure(self, tmp_path: Path):
        wo_root = tmp_path / "work_orders"
        out_root = tmp_path / "outputs"
        _make_work_order(wo_root, "wo_01")

        result = run_batch(work_orders_root=wo_root, outputs_root=out_root, dry_run=True)
        required = ["total_candidates", "processed", "skipped", "failed", "registered", "dry_run", "results"]
        for key in required:
            assert key in result

    def test_results_contain_validation(self, tmp_path: Path):
        wo_root = tmp_path / "work_orders"
        out_root = tmp_path / "outputs"
        _make_work_order(wo_root, "wo_01")

        result = run_batch(work_orders_root=wo_root, outputs_root=out_root, dry_run=True)
        assert len(result["results"]) >= 1
        assert "valid" in result["results"][0]
        assert "work_order_id" in result["results"][0]

    def test_skips_non_directories(self, tmp_path: Path):
        wo_root = tmp_path / "work_orders"
        out_root = tmp_path / "outputs"
        wo_root.mkdir(parents=True)
        # Create a random file, not a WO directory
        (wo_root / "some_file.txt").write_text("not a work order")
        _make_work_order(wo_root, "wo_01")

        result = run_batch(work_orders_root=wo_root, outputs_root=out_root, dry_run=True)
        assert result["total_candidates"] == 1
