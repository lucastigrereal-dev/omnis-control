"""Tests for output generator approval bridge (P10.7)."""
from __future__ import annotations

import json
from pathlib import Path

from src.output_generator.approval_bridge import prepare_submission
from src.output_generator.manifest_registry import ManifestRegistry


class TestPrepareSubmission:
    def test_dry_run_valid_package_returns_no_approval(self, tmp_path: Path):
        root = tmp_path / "outputs"
        pkg = root / "pkg_01"
        pkg.mkdir(parents=True)
        md_file = pkg / "output.md"
        md_file.write_text("# hello")
        fp = __import__("hashlib").sha256(md_file.read_bytes()).hexdigest()[:16]

        manifest = {
            "package_id": "pkg_01",
            "work_order_id": "wo_01",
            "created_at": "2026-05-12T00:00:00Z",
            "outputs": [],
            "blockers": [],
            "file_count": 1,
        }
        (pkg / "package_manifest.json").write_text(json.dumps(manifest))

        reg = ManifestRegistry(tmp_path / "reg.jsonl")
        reg.register("out_01", "wo_01", "markdown", str(md_file), "md_gen", fp)

        result = prepare_submission("wo_01", registry=reg, dry_run=True)
        assert result["valid"] is True
        assert result["dry_run"] is True
        assert result["approval_request"] is None
        assert result["file_count"] == 1

    def test_dry_run_invalid_package(self, tmp_path: Path):
        reg = ManifestRegistry(tmp_path / "reg.jsonl")
        result = prepare_submission("wo_ghost", registry=reg, dry_run=True)
        assert result["valid"] is False
        assert result["dry_run"] is True
        assert result["approval_request"] is None

    def test_file_list_and_types(self, tmp_path: Path):
        root = tmp_path / "outputs"
        pkg = root / "pkg_01"
        pkg.mkdir(parents=True)
        md_file = pkg / "output.md"
        md_file.write_text("# md")
        md_fp = __import__("hashlib").sha256(md_file.read_bytes()).hexdigest()[:16]

        reg = ManifestRegistry(tmp_path / "reg.jsonl")
        reg.register("out_01", "wo_01", "markdown", str(md_file), "md_gen", md_fp)
        reg.register("out_02", "wo_01", "csv", str(md_file), "csv_gen", md_fp)

        result = prepare_submission("wo_01", registry=reg, dry_run=True)
        assert result["file_count"] == 2
        assert set(result["output_types"]) == {"markdown", "csv"}
        assert len(result["files"]) == 2

    def test_includes_validation_checks(self, tmp_path: Path):
        root = tmp_path / "outputs"
        pkg = root / "pkg_01"
        pkg.mkdir(parents=True)
        md_file = pkg / "output.md"
        md_file.write_text("# content")
        fp = __import__("hashlib").sha256(md_file.read_bytes()).hexdigest()[:16]

        reg = ManifestRegistry(tmp_path / "reg.jsonl")
        reg.register("out_01", "wo_01", "markdown", str(md_file), "md_gen", fp)

        result = prepare_submission("wo_01", registry=reg, dry_run=True)
        assert len(result["checks"]) >= 3
        check_names = [c["name"] for c in result["checks"]]
        assert "registry_entries" in check_names
        assert "file_existence" in check_names
        assert "fingerprints" in check_names

    def test_invalid_package_no_approval_submission(self, tmp_path: Path):
        """Even with no_dry_run, invalid package should NOT submit to approval."""
        reg = ManifestRegistry(tmp_path / "reg.jsonl")
        # No entries → invalid
        result = prepare_submission("wo_ghost", registry=reg, dry_run=False)
        assert result["valid"] is False
        assert result["approval_request"] is None
        assert result["dry_run"] is False

    def test_no_dry_run_submits_approval(self, tmp_path: Path):
        root = tmp_path / "outputs"
        pkg = root / "pkg_01"
        pkg.mkdir(parents=True)
        md_file = pkg / "output.md"
        md_file.write_text("# real")
        fp = __import__("hashlib").sha256(md_file.read_bytes()).hexdigest()[:16]

        reg = ManifestRegistry(tmp_path / "reg.jsonl")
        reg.register("out_01", "wo_01", "markdown", str(md_file), "md_gen", fp)

        approvals_log = tmp_path / "approvals.jsonl"
        result = prepare_submission("wo_01", registry=reg, dry_run=False, approvals_log=approvals_log)
        assert result["valid"] is True
        assert result["dry_run"] is False
        assert result["approval_request"] is not None
        assert result["approval_request"]["request_id"].startswith("req_")
        assert result["approval_request"]["status"] == "pending"
        # Verify it was written to the log
        assert approvals_log.exists()

    def test_issues_and_warnings_propagated(self, tmp_path: Path):
        root = tmp_path / "outputs"
        root.mkdir(parents=True)

        reg = ManifestRegistry(tmp_path / "reg.jsonl")
        reg.register("out_01", "wo_01", "markdown", str(tmp_path / "missing.md"), "md_gen", "abc")

        result = prepare_submission("wo_01", registry=reg, dry_run=True)
        assert result["valid"] is False
        assert len(result["issues"]) > 0
