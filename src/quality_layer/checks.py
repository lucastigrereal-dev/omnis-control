"""Quality checks for offline packages and renders."""
import json
import re
from pathlib import Path
from typing import Optional


_SECRET_PATTERNS = ["access_token", "META_APP_SECRET", "client_secret", "app_secret"]

# weight: critical=20, high=10, medium=5
CHECKS = {
    "manifest_exists":          ("critical", "Manifest.json presente"),
    "manifest_valid_json":      ("critical", "Manifest.json valido (JSON)"),
    "manifest_has_package_id":  ("high",     "Manifest tem package_id"),
    "manifest_has_status":      ("high",     "Manifest tem status"),
    "caption_exists":           ("high",     "caption.md presente"),
    "caption_not_empty":        ("high",     "caption.md nao vazio"),
    "checklist_exists":         ("medium",   "publishing_checklist.md presente"),
    "no_secret_patterns":       ("critical", "Nenhum secret nos arquivos"),
    "package_status_consistent":("medium",   "Status do pacote consistente"),
    "render_html_exists":       ("medium",   "preview.html renderizado"),
    "asset_present_or_warned":  ("medium",   "Asset referenciado ou aviso presente"),
}

WEIGHTS = {"critical": 20, "high": 10, "medium": 5}

# Maximum possible score
MAX_SCORE = sum(WEIGHTS[level] for level, _ in CHECKS.values())


def run_checks(
    package_dir: Path,
    render_dir: Optional[Path] = None,
) -> tuple[list[str], list[str], list[str]]:
    """Returns (passed, failed, warnings)."""
    passed = []
    failed = []
    warnings = []

    def ok(key):
        passed.append(CHECKS[key][1])

    def fail(key):
        failed.append(CHECKS[key][1])

    def warn(msg):
        warnings.append(msg)

    # manifest_exists
    manifest_path = package_dir / "manifest.json"
    if manifest_path.exists():
        ok("manifest_exists")
    else:
        fail("manifest_exists")

    # manifest_valid_json + fields
    manifest = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            ok("manifest_valid_json")
        except Exception:
            fail("manifest_valid_json")
    else:
        fail("manifest_valid_json")

    if manifest.get("package_id"):
        ok("manifest_has_package_id")
    else:
        fail("manifest_has_package_id")

    if manifest.get("status"):
        ok("manifest_has_status")
    else:
        fail("manifest_has_status")

    # caption_exists + not_empty
    caption_path = package_dir / "caption.md"
    if caption_path.exists():
        ok("caption_exists")
        text = caption_path.read_text(encoding="utf-8").strip()
        if text:
            ok("caption_not_empty")
        else:
            fail("caption_not_empty")
    else:
        fail("caption_exists")
        fail("caption_not_empty")

    # checklist
    checklist_path = package_dir / "publishing_checklist.md"
    if checklist_path.exists():
        ok("checklist_exists")
    else:
        fail("checklist_exists")

    # no_secret_patterns — scan all text files
    secrets_found = []
    for f in package_dir.iterdir():
        if f.suffix in (".md", ".json", ".txt", ".csv"):
            try:
                content = f.read_text(encoding="utf-8")
                for pattern in _SECRET_PATTERNS:
                    if pattern in content:
                        secrets_found.append(f"{pattern} in {f.name}")
            except Exception:
                pass
    if secrets_found:
        fail("no_secret_patterns")
        for s in secrets_found:
            warn(f"Secret encontrado: {s}")
    else:
        ok("no_secret_patterns")

    # package_status_consistent
    status = manifest.get("status", "")
    if status in ("ready", "partial", "blocked", "exported", "draft"):
        ok("package_status_consistent")
    else:
        fail("package_status_consistent")

    # render_html_exists
    if render_dir and (render_dir / "preview.html").exists():
        ok("render_html_exists")
    else:
        fail("render_html_exists")
        warn("HTML preview nao encontrado — execute: offline render package <id>")

    # asset_present_or_warned
    if manifest.get("asset_id") or manifest.get("has_asset"):
        ok("asset_present_or_warned")
    else:
        fail("asset_present_or_warned")
        warn("Nenhum asset atribuido — execute: assets add-mock <nome> --queue-id <id>")

    return passed, failed, warnings


def compute_score(passed_names: list[str]) -> int:
    """Compute score 0-100 from list of passed check descriptions."""
    check_by_desc = {desc: (level, key) for key, (level, desc) in CHECKS.items()}
    earned = 0
    for desc in passed_names:
        if desc in check_by_desc:
            level, _ = check_by_desc[desc]
            earned += WEIGHTS[level]
    if MAX_SCORE == 0:
        return 0
    return min(100, round(earned * 100 / MAX_SCORE))
