"""Output Validation Layer — package integrity checks against Manifest Registry."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

from src.output_generator.manifest_registry import ManifestRegistry


REQUIRED_FIELDS = [
    "output_id", "work_order_id", "output_type",
    "file_path", "generator_id", "fingerprint", "registered_at",
]


@dataclass
class ValidationResult:
    valid: bool
    work_order_id: str
    checks: list[dict] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "work_order_id": self.work_order_id,
            "checks": self.checks,
            "issues": self.issues,
            "warnings": self.warnings,
        }


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def validate_package(
    work_order_id: str,
    registry: ManifestRegistry | None = None,
    output_root: Path | None = None,
) -> ValidationResult:
    """Validate package integrity for a work order.

    Checks: registry entries exist, schema completeness, file existence,
    fingerprint match, package manifest.
    """
    reg = registry or ManifestRegistry()
    root = output_root or Path("exports/generated_outputs")

    checks: list[dict] = []
    issues: list[str] = []
    warnings: list[str] = []

    entries = reg.list_by_work_order(work_order_id)

    # Check 1: registry has entries
    if not entries:
        issues.append(f"No registry entries for work_order_id={work_order_id}")
        checks.append({"name": "registry_entries", "status": "fail", "message": "No entries found"})
        return ValidationResult(
            valid=False, work_order_id=work_order_id,
            checks=checks, issues=issues, warnings=warnings,
        )
    checks.append({"name": "registry_entries", "status": "pass", "message": f"{len(entries)} entries found"})

    # Check 2: schema — all required fields present
    schema_ok = True
    for entry in entries:
        missing = [f for f in REQUIRED_FIELDS if f not in entry or entry[f] == "" and f != "fingerprint"]
        if missing:
            schema_ok = False
            issues.append(f"Entry {entry.get('output_id', '?')} missing fields: {', '.join(missing)}")
    if schema_ok:
        checks.append({"name": "schema", "status": "pass", "message": "All entries have required fields"})
    else:
        checks.append({"name": "schema", "status": "fail", "message": "Some entries missing required fields"})

    # Check 3: file existence
    missing_files = []
    for entry in entries:
        fp_str = entry.get("file_path", "")
        if not fp_str:
            missing_files.append("(missing file_path field)")
            issues.append(f"Entry {entry.get('output_id', '?')} has no file_path")
            continue
        fpath = Path(fp_str)
        if not fpath.exists():
            missing_files.append(str(fpath))
            issues.append(f"File missing: {fpath}")
    if missing_files:
        checks.append({"name": "file_existence", "status": "fail", "message": f"{len(missing_files)} files missing"})
    else:
        checks.append({"name": "file_existence", "status": "pass", "message": f"All {len(entries)} files present"})

    # Check 4: fingerprints
    fp_mismatches = 0
    for entry in entries:
        fp_str = entry.get("file_path", "")
        if not fp_str:
            continue
        fpath = Path(fp_str)
        if not fpath.exists():
            continue
        actual_fp = _hash_file(fpath)
        expected_fp = entry.get("fingerprint", "")
        if expected_fp and actual_fp != expected_fp:
            fp_mismatches += 1
            issues.append(f"Fingerprint mismatch for {entry['output_id']}: expected {expected_fp}, got {actual_fp}")
    if fp_mismatches:
        checks.append({"name": "fingerprints", "status": "fail", "message": f"{fp_mismatches} mismatches"})
    else:
        checks.append({"name": "fingerprints", "status": "pass", "message": "All fingerprints match"})

    # Check 5: package manifest (find package dir and check manifest)
    pkg_dirs = set()
    for entry in entries:
        fp_str = entry.get("file_path", "")
        if not fp_str:
            continue
        fpath = Path(fp_str)
        if fpath.exists():
            pkg_dirs.add(fpath.parent)

    manifest_found = False
    for pkg_dir in pkg_dirs:
        manifest_path = pkg_dir / "package_manifest.json"
        if manifest_path.exists():
            manifest_found = True
            try:
                data = json.loads(manifest_path.read_text(encoding="utf-8"))
                if data.get("work_order_id") != work_order_id:
                    warnings.append(f"Manifest work_order_id mismatch: {data.get('work_order_id')}")
                checks.append({"name": "package_manifest", "status": "pass", "message": str(manifest_path)})
            except json.JSONDecodeError:
                issues.append(f"Invalid JSON in {manifest_path}")
                checks.append({"name": "package_manifest", "status": "fail", "message": "Invalid JSON"})
            break

    if not manifest_found:
        warnings.append("No package_manifest.json found")
        checks.append({"name": "package_manifest", "status": "warn", "message": "Not found"})

    valid = len(issues) == 0
    return ValidationResult(
        valid=valid, work_order_id=work_order_id,
        checks=checks, issues=issues, warnings=warnings,
    )
