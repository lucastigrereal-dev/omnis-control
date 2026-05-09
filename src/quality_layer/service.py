"""Quality layer service — scores offline packages."""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.quality_layer.checks import run_checks, compute_score
from src.quality_layer.errors import PackageNotFoundError
from src.quality_layer.models import QualityResult

EXPORT_ROOT = Path("exports/offline_factory")
RENDER_ROOT = Path("exports/rendered")
SCORES_LOG = Path("data/quality_scores.jsonl")


def _append_score(result: QualityResult, log_path: Path = SCORES_LOG) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = result.to_dict()
    record["scored_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_scores(log_path: Path = SCORES_LOG) -> list[dict]:
    if not log_path.exists():
        return []
    rows = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def _find_dir(prefix: str, root: Path) -> Optional[Path]:
    if not root.exists():
        return None
    for d in root.iterdir():
        if d.is_dir() and d.name.startswith(prefix):
            return d
    return None


def score_package(
    package_id: str,
    export_root: Path = EXPORT_ROOT,
    render_root: Path = RENDER_ROOT,
) -> QualityResult:
    pkg_dir = _find_dir(package_id, export_root)
    if not pkg_dir:
        raise PackageNotFoundError(f"Package '{package_id}' not found in {export_root}")

    render_dir = _find_dir(pkg_dir.name, render_root)
    passed, failed, warnings = run_checks(pkg_dir, render_dir=render_dir)
    score = compute_score(passed)

    result = QualityResult.from_score(
        package_id=pkg_dir.name,
        score=score,
        checks_passed=passed,
        checks_failed=failed,
        warnings=warnings,
    )
    _append_score(result, SCORES_LOG)  # SCORES_LOG resolved at call time — patchable
    return result
