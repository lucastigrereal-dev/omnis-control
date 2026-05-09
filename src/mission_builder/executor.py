"""Mission Executor — orchestrates plan + package export.

NUNCA publica. NUNCA chama Meta. NUNCA aciona OAuth.
run() sempre opera em dry-run nesta fase.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from src.mission_builder.models import MissionPlan, MissionPackageManifest
from src.mission_builder.planner import build_plan
from src.mission_builder.package_exporter import export_package


def run(
    request_text: str,
    account_handle: Optional[str] = None,
    objective: str = "engajamento",
    dry_run: bool = True,
    config_path: Optional[Path] = None,
    packages_root: Optional[Path] = None,
    allow_unknown: bool = False,
) -> tuple[MissionPlan, Optional[MissionPackageManifest]]:
    """Build plan and (if dry_run=True) export package.

    Returns (plan, manifest) where manifest is None if not exporting.
    """
    plan = build_plan(
        request_text=request_text,
        account_handle=account_handle,
        objective=objective,
        config_path=config_path,
        allow_unknown=allow_unknown,
    )
    plan.dry_run = dry_run

    if not dry_run:
        return plan, None

    kwargs = {}
    if packages_root is not None:
        kwargs["packages_root"] = packages_root
    manifest = export_package(plan, **kwargs)
    return plan, manifest
