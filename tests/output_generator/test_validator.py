"""Tests for output validation layer (P10.6)."""
from __future__ import annotations

import json
from pathlib import Path

from src.output_generator.manifest_registry import ManifestRegistry
from src.output_generator.validator import ValidationResult, validate_package


class TestValidationResult:
    def test_to_dict(self):
        vr = ValidationResult(valid=True, work_order_id="wo_01", checks=[{"name": "x", "status": "pass", "message": "ok"}])
        d = vr.to_dict()
        assert d["valid"] is True
        assert d["work_order_id"] == "wo_01"
        assert d["checks"] == [{"name": "x", "status": "pass", "message": "ok"}]

    def test_defaults(self):
        vr = ValidationResult(valid=False, work_order_id="wo_X")
        assert vr.checks == []
        assert vr.issues == []
        assert vr.warnings == []


class TestValidatePackage:
    def test_no_registry_entries(self, tmp_path: Path):
        reg = ManifestRegistry(tmp_path / "reg.jsonl")
        result = validate_package("wo_ghost", registry=reg)
        assert result.valid is False
        assert any("No registry entries" in i for i in result.issues)
        assert result.checks[0]["status"] == "fail"

    def test_all_checks_pass(self, tmp_path: Path):
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

        result = validate_package("wo_01", registry=reg, output_root=root)
        assert result.valid is True
        statuses = [c["status"] for c in result.checks]
        assert "pass" in statuses

    def test_schema_missing_fields(self, tmp_path: Path):
        root = tmp_path / "outputs"
        root.mkdir(parents=True)

        reg_path = tmp_path / "reg.jsonl"
        reg = ManifestRegistry(reg_path)
        # Manually write an entry with missing fields
        bad_entry = {"output_id": "out_bad", "work_order_id": "wo_01"}
        with open(reg_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(bad_entry) + "\n")

        result = validate_package("wo_01", registry=reg, output_root=root)
        assert result.valid is False
        assert any("schema" in c["name"] and c["status"] == "fail" for c in result.checks)

    def test_file_missing(self, tmp_path: Path):
        reg = ManifestRegistry(tmp_path / "reg.jsonl")
        reg.register("out_01", "wo_01", "markdown", str(tmp_path / "nonexistent.md"), "md_gen", "abc")

        result = validate_package("wo_01", registry=reg, output_root=tmp_path / "out")
        assert result.valid is False
        assert any("File missing" in i for i in result.issues)
        file_check = [c for c in result.checks if c["name"] == "file_existence"]
        assert len(file_check) == 1
        assert file_check[0]["status"] == "fail"

    def test_fingerprint_mismatch(self, tmp_path: Path):
        root = tmp_path / "outputs"
        pkg = root / "pkg_01"
        pkg.mkdir(parents=True)
        md_file = pkg / "output.md"
        md_file.write_text("# real content")

        reg = ManifestRegistry(tmp_path / "reg.jsonl")
        reg.register("out_01", "wo_01", "markdown", str(md_file), "md_gen", "deadbeef00000000")

        result = validate_package("wo_01", registry=reg, output_root=root)
        assert result.valid is False
        assert any("Fingerprint mismatch" in i for i in result.issues)

    def test_fingerprints_match(self, tmp_path: Path):
        root = tmp_path / "outputs"
        pkg = root / "pkg_01"
        pkg.mkdir(parents=True)
        md_file = pkg / "output.md"
        md_file.write_text("# exact content")
        fp = __import__("hashlib").sha256(md_file.read_bytes()).hexdigest()[:16]

        reg = ManifestRegistry(tmp_path / "reg.jsonl")
        reg.register("out_01", "wo_01", "markdown", str(md_file), "md_gen", fp)

        result = validate_package("wo_01", registry=reg, output_root=root)
        fp_check = [c for c in result.checks if c["name"] == "fingerprints"]
        assert fp_check[0]["status"] == "pass"
        assert "All fingerprints match" in fp_check[0]["message"]

    def test_empty_fingerprint_in_registry_passes(self, tmp_path: Path):
        """Empty fingerprint in registry is skipped (not compared)."""
        root = tmp_path / "outputs"
        pkg = root / "pkg_01"
        pkg.mkdir(parents=True)
        md_file = pkg / "output.md"
        md_file.write_text("# content")

        reg = ManifestRegistry(tmp_path / "reg.jsonl")
        reg.register("out_01", "wo_01", "markdown", str(md_file), "md_gen", "")

        result = validate_package("wo_01", registry=reg, output_root=root)
        fp_check = [c for c in result.checks if c["name"] == "fingerprints"]
        assert fp_check[0]["status"] == "pass"

    def test_package_manifest_missing_warns(self, tmp_path: Path):
        root = tmp_path / "outputs"
        pkg = root / "pkg_01"
        pkg.mkdir(parents=True)
        md_file = pkg / "output.md"
        md_file.write_text("# content")
        fp = __import__("hashlib").sha256(md_file.read_bytes()).hexdigest()[:16]

        reg = ManifestRegistry(tmp_path / "reg.jsonl")
        reg.register("out_01", "wo_01", "markdown", str(md_file), "md_gen", fp)

        result = validate_package("wo_01", registry=reg, output_root=root)
        # Manifest is missing but files + fingerprints are ok → still valid
        assert result.valid is True
        manifest_check = [c for c in result.checks if c["name"] == "package_manifest"]
        assert manifest_check[0]["status"] == "warn"

    def test_multiple_entries(self, tmp_path: Path):
        root = tmp_path / "outputs"
        pkg = root / "pkg_01"
        pkg.mkdir(parents=True)

        md_file = pkg / "output.md"
        md_file.write_text("# md")
        md_fp = __import__("hashlib").sha256(md_file.read_bytes()).hexdigest()[:16]

        csv_file = pkg / "output.csv"
        csv_file.write_text("col1,col2\na,b")
        csv_fp = __import__("hashlib").sha256(csv_file.read_bytes()).hexdigest()[:16]

        manifest = {
            "package_id": "pkg_01",
            "work_order_id": "wo_01",
            "created_at": "2026-05-12T00:00:00Z",
            "outputs": [],
            "blockers": [],
            "file_count": 2,
        }
        (pkg / "package_manifest.json").write_text(json.dumps(manifest))

        reg = ManifestRegistry(tmp_path / "reg.jsonl")
        reg.register("out_01", "wo_01", "markdown", str(md_file), "md_gen", md_fp)
        reg.register("out_02", "wo_01", "csv", str(csv_file), "csv_gen", csv_fp)

        result = validate_package("wo_01", registry=reg, output_root=root)
        assert result.valid is True
        assert all(c["status"] == "pass" for c in result.checks if c["name"] != "package_manifest")
