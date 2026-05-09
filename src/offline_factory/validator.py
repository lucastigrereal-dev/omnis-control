"""Package integrity validator — FASE 4.

Reads manifest, checks files on disk, computes a 0-100 score.
NEVER calls external APIs. NEVER reads secrets.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_SECRET_PATTERNS = re.compile(
    r"(access_token|META_APP_SECRET|client_secret|INSTAGRAM_APP_SECRET"
    r"|bearer\s+[A-Za-z0-9._-]{20,}|eyJ[A-Za-z0-9._-]{20,})",
    re.IGNORECASE,
)


@dataclass
class ValidationResult:
    package_id: str
    score: int  # 0-100
    checks_passed: list[str] = field(default_factory=list)
    checks_failed: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.checks_failed) == 0

    def to_dict(self) -> dict:
        return {
            "package_id": self.package_id,
            "score": self.score,
            "is_valid": self.is_valid,
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
            "warnings": self.warnings,
        }


def validate_package(package_dir: Path) -> ValidationResult:
    """Validate a package directory. Returns ValidationResult with score 0-100."""
    pkg_id = package_dir.name
    result = ValidationResult(package_id=pkg_id, score=0)

    checks: list[tuple[str, bool, str]] = []  # (name, passed, weight_desc)

    # 1. manifest exists
    manifest_path = package_dir / "manifest.json"
    checks.append(("manifest_exists", manifest_path.is_file(), "critical"))

    manifest_data: dict = {}
    if manifest_path.is_file():
        try:
            manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
            checks.append(("manifest_valid_json", True, "critical"))
        except (json.JSONDecodeError, OSError):
            checks.append(("manifest_valid_json", False, "critical"))
    else:
        checks.append(("manifest_valid_json", False, "critical"))

    # 2. Required manifest fields
    required_fields = ["package_id", "package_type", "status", "account_handle"]
    for f in required_fields:
        checks.append((f"manifest_has_{f}", bool(manifest_data.get(f)), "high"))

    # 3. Files listed in manifest actually exist on disk
    listed_files = manifest_data.get("files", [])
    missing_files = []
    for entry in listed_files:
        fname = entry.get("name") if isinstance(entry, dict) else str(entry)
        if fname and fname != "manifest.json":
            fpath = package_dir / fname
            if not fpath.is_file():
                missing_files.append(fname)

    checks.append(("all_listed_files_exist", len(missing_files) == 0, "critical"))
    if missing_files:
        result.warnings.append(f"Arquivos ausentes do disco: {', '.join(missing_files)}")

    # 4. Essential files
    for essential in ("caption.md", "README.md", "publishing_checklist.md"):
        checks.append((f"{essential.replace('.', '_')}_exists", (package_dir / essential).is_file(), "medium"))

    # 5. No Meta secrets in any text file
    secret_found_in: list[str] = []
    for fpath in package_dir.iterdir():
        if fpath.suffix in (".md", ".json", ".txt", ".csv") and fpath.is_file():
            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
                if _SECRET_PATTERNS.search(content):
                    secret_found_in.append(fpath.name)
            except OSError:
                pass
    checks.append(("no_meta_secrets", len(secret_found_in) == 0, "critical"))
    if secret_found_in:
        result.warnings.append(f"Possivel secret encontrado em: {', '.join(secret_found_in)}")

    # 6. Status consistency (partial/ready should not have empty caption)
    status = manifest_data.get("status", "")
    caption_path = package_dir / "caption.md"
    if status in ("partial", "ready") and caption_path.is_file():
        content = caption_path.read_text(encoding="utf-8", errors="ignore").strip()
        caption_ok = bool(content) and content != "(Legenda pendente)"
        checks.append(("caption_not_empty", caption_ok, "medium"))
    else:
        checks.append(("caption_not_empty", caption_path.is_file(), "medium"))

    # Compute score
    weights = {"critical": 20, "high": 10, "medium": 5}
    total_weight = sum(weights.get(w, 5) for _, _, w in checks)
    earned = sum(weights.get(w, 5) for _, passed, w in checks if passed)
    score = int((earned / total_weight) * 100) if total_weight else 0

    result.score = score
    result.checks_passed = [name for name, passed, _ in checks if passed]
    result.checks_failed = [name for name, passed, _ in checks if not passed]

    return result


def validate_by_id(package_id: str, export_root: Path) -> Optional[ValidationResult]:
    """Find a package by ID (prefix match) and validate it."""
    if not export_root.exists():
        return None
    matches = [
        d for d in export_root.iterdir()
        if d.is_dir() and d.name.startswith(package_id)
    ]
    if not matches:
        return None
    return validate_package(matches[0])
