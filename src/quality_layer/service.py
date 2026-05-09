"""Quality layer service — scores offline packages."""
from pathlib import Path
from typing import Optional

from src.quality_layer.checks import run_checks, compute_score
from src.quality_layer.errors import PackageNotFoundError
from src.quality_layer.models import QualityResult

EXPORT_ROOT = Path("exports/offline_factory")
RENDER_ROOT = Path("exports/rendered")


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

    return QualityResult.from_score(
        package_id=pkg_dir.name,
        score=score,
        checks_passed=passed,
        checks_failed=failed,
        warnings=warnings,
    )
