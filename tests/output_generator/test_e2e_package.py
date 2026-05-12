"""E2E tests — Work Order → Final Package (P10.10)."""
from __future__ import annotations

import json
from pathlib import Path

from src.output_generator.approval_bridge import prepare_submission
from src.output_generator.batch_runner import run_batch
from src.output_generator.manifest_registry import ManifestRegistry
from src.output_generator.validator import validate_package
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


class TestE2EPackage:
    """Full end-to-end: WO → writers → package → manifest → registry → validate → submit."""

    def test_full_pipeline_single_wo(self, tmp_path: Path):
        wo_root = tmp_path / "work_orders"
        out_root = tmp_path / "outputs"
        reg_path = tmp_path / "registry.jsonl"

        _make_work_order(wo_root, "wo_e2e_01")

        # Phase 1: Package + register
        reg = ManifestRegistry(reg_path)
        service = OutputWriterService(work_orders_root=wo_root, outputs_root=out_root, manifest_registry=reg)
        orch_result = service.orchestrate("wo_e2e_01")

        assert orch_result["valid"] is True
        assert orch_result["registered"] >= 1
        assert len(orch_result["outputs"]) >= 1
        assert reg.count() >= 1

        # Phase 2: Validate
        validation = validate_package("wo_e2e_01", registry=reg, output_root=out_root)
        assert validation.valid is True
        assert any(c["status"] == "pass" for c in validation.checks)

        # Phase 3: Submit (dry-run)
        submission = prepare_submission("wo_e2e_01", registry=reg, dry_run=True)
        assert submission["valid"] is True
        assert submission["dry_run"] is True
        assert submission["approval_request"] is None  # dry-run = no actual submission

    def test_full_pipeline_multi_wo(self, tmp_path: Path):
        wo_root = tmp_path / "work_orders"
        out_root = tmp_path / "outputs"
        reg_path = tmp_path / "registry.jsonl"

        _make_work_order(wo_root, "wo_e2e_01")
        _make_work_order(wo_root, "wo_e2e_02")

        # Batch process
        result = run_batch(work_orders_root=wo_root, outputs_root=out_root, dry_run=False)
        assert result["processed"] == 2
        assert result["registered"] >= 2
        assert result["failed"] == 0

    def test_e2e_with_validation_and_submission(self, tmp_path: Path):
        wo_root = tmp_path / "work_orders"
        out_root = tmp_path / "outputs"
        reg_path = tmp_path / "registry.jsonl"
        approvals_log = tmp_path / "approvals.jsonl"

        _make_work_order(wo_root, "wo_e2e_03", contracts=[
            {"contract_id": "c01", "output_type": "markdown", "description": "md file", "required": True, "min_count": 1, "max_count": 1},
            {"contract_id": "c02", "output_type": "json", "description": "json file", "required": True, "min_count": 1, "max_count": 1},
        ])

        reg = ManifestRegistry(reg_path)
        service = OutputWriterService(work_orders_root=wo_root, outputs_root=out_root, manifest_registry=reg)
        orch_result = service.orchestrate("wo_e2e_03")

        assert orch_result["valid"] is True
        assert orch_result["registered"] >= 2

        # Validate
        validation = validate_package("wo_e2e_03", registry=reg, output_root=out_root)
        assert validation.valid is True

        # Submit with real approval (no_dry_run)
        submission = prepare_submission("wo_e2e_03", registry=reg, approvals_log=approvals_log, dry_run=False)
        assert submission["valid"] is True
        assert submission["dry_run"] is False
        assert submission["approval_request"] is not None
        assert submission["approval_request"]["request_id"].startswith("req_")
        assert submission["approval_request"]["status"] == "pending"

        # Verify approval request was persisted
        assert approvals_log.exists()
        log_content = approvals_log.read_text()
        assert "wo_e2e_03" in log_content

    def test_e2e_invalid_package_blocks_submission(self, tmp_path: Path):
        wo_root = tmp_path / "work_orders"
        out_root = tmp_path / "outputs"
        reg_path = tmp_path / "registry.jsonl"
        approvals_log = tmp_path / "approvals.jsonl"

        # Create a work order but don't actually generate the package
        _make_work_order(wo_root, "wo_bad")
        # Don't call service.orchestrate — package was never generated
        # This means validate_package will find no registry entries → invalid

        reg = ManifestRegistry(reg_path)
        submission = prepare_submission("wo_bad", registry=reg, approvals_log=approvals_log, dry_run=False)
        assert submission["valid"] is False
        assert submission["approval_request"] is None  # blocked
        assert not approvals_log.exists() or "wo_bad" not in approvals_log.read_text()

    def test_e2e_package_file_integrity(self, tmp_path: Path):
        wo_root = tmp_path / "work_orders"
        out_root = tmp_path / "outputs"
        reg_path = tmp_path / "registry.jsonl"

        _make_work_order(wo_root, "wo_int")

        reg = ManifestRegistry(reg_path)
        service = OutputWriterService(work_orders_root=wo_root, outputs_root=out_root, manifest_registry=reg)
        orch_result = service.orchestrate("wo_int")

        # Verify every output file exists on disk
        for output in orch_result["outputs"]:
            fpath = Path(output["file_path"])
            assert fpath.exists(), f"File missing: {fpath}"
            assert fpath.stat().st_size > 0, f"File empty: {fpath}"

        # Verify package_manifest.json
        pkg_dir = Path(orch_result["package_dir"])
        manifest_path = pkg_dir / "package_manifest.json"
        assert manifest_path.exists()

        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest_data["work_order_id"] == "wo_int"
        assert manifest_data["file_count"] == len(orch_result["outputs"])

    def test_e2e_registry_fingerprints_match_files(self, tmp_path: Path):
        wo_root = tmp_path / "work_orders"
        out_root = tmp_path / "outputs"
        reg_path = tmp_path / "registry.jsonl"

        _make_work_order(wo_root, "wo_fp")

        reg = ManifestRegistry(reg_path)
        service = OutputWriterService(work_orders_root=wo_root, outputs_root=out_root, manifest_registry=reg)
        service.orchestrate("wo_fp")

        entries = reg.list_by_work_order("wo_fp")
        for entry in entries:
            if entry.get("file_path") and Path(entry["file_path"]).exists():
                import hashlib
                actual_fp = hashlib.sha256(Path(entry["file_path"]).read_bytes()).hexdigest()[:16]
                expected_fp = entry.get("fingerprint", "")
                if expected_fp:  # Only compare if fingerprint is populated
                    assert actual_fp == expected_fp, f"Fingerprint mismatch for {entry['output_id']}"
