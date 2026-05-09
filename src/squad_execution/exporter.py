"""Squad Execution Exporter — writes dry-run plan files to a run directory."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from src.squad_execution.models import SquadExecutionPlan, FORBIDDEN_MANIFEST_PREFIXES

BASE = Path(__file__).resolve().parent.parent.parent
DEFAULT_RUNS_ROOT = BASE / "exports" / "squad_runs"


def export_squad_run(
    plan: SquadExecutionPlan,
    runs_root: Optional[Path] = None,
    squad_plan=None,
    task_plan=None,
) -> Path:
    """Write dry-run plan files into a run directory. Returns the run_dir Path."""
    root = Path(runs_root) if runs_root is not None else DEFAULT_RUNS_ROOT
    run_dir = root / plan.squad_run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # 1. Manifest
    _write(run_dir / "squad_manifest.json", json.dumps(plan.to_dict(), indent=2, ensure_ascii=False))

    # 2. Request
    _write(run_dir / "01_request.md", _build_request_md(plan))

    # 3. Squad
    _write(run_dir / "02_squad.md", _build_squad_md(plan, squad_plan))

    # 4. Task plan
    _write(run_dir / "03_task_plan.md", _build_task_plan_md(plan, task_plan))

    # 5. Execution plan
    _write(run_dir / "04_execution_plan.md", _build_exec_plan_md(plan))

    # 6. Approval
    _write(run_dir / "05_approval.md", _build_approval_md(plan))

    # 7. Next actions
    _write(run_dir / "06_next_actions.md", _build_next_actions_md(plan))

    return run_dir


def _write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _build_request_md(p: SquadExecutionPlan) -> str:
    return f"""# Request — {p.squad_run_id}

**Request:** {p.request}
**Sector:** {p.sector}
**Created:** {p.created_at}
"""


def _build_squad_md(p: SquadExecutionPlan, squad_plan=None) -> str:
    lines = [f"# Squad — {p.squad_id}", "", f"**Sector:** {p.sector}",
             f"**Risk:** {p.risk_level}", f"**Roles:**"]
    if squad_plan:
        for r in squad_plan.roles:
            lines.append(f"- `{r.role_id}` — {r.role_name} (risk: {r.risk_level})")
    else:
        for rid in p.roles:
            lines.append(f"- `{rid}`")
    return "\n".join(lines)


def _build_task_plan_md(p: SquadExecutionPlan, task_plan=None) -> str:
    lines = [f"# Task Plan — {p.task_plan_id}", ""]
    if task_plan:
        for t in task_plan.tasks:
            deps = ", ".join(t.depends_on) or "none"
            lines.append(f"## {t.task_id} — {t.title}")
            lines.append(f"- Role: `{t.role_id}`")
            lines.append(f"- Output: `{t.expected_output}`")
            lines.append(f"- Depends on: {deps}")
            lines.append("")
    else:
        lines.append("*Task plan details not available.*")
    return "\n".join(lines)


def _build_exec_plan_md(p: SquadExecutionPlan) -> str:
    return f"""# Execution Plan — {p.squad_run_id}

**Status:** {p.status}
**Risk:** {p.risk_level}
**Approval Required:** {p.approval_required}

> This is a DRY-RUN plan. No agents are executed. No external calls made.
"""


def _build_approval_md(p: SquadExecutionPlan) -> str:
    if p.approval_required:
        return f"""# Approval — Required

**Status:** blocked_pending_approval
**Squad Run:** {p.squad_run_id}
**Risk:** {p.risk_level}

Approval is required before this squad run can proceed.
"""
    return f"""# Approval — Not Required

**Status:** planned_ready
**Squad Run:** {p.squad_run_id}
**Risk:** {p.risk_level}

No approval needed. Squad run is planned_ready.
"""


def _build_next_actions_md(p: SquadExecutionPlan) -> str:
    lines = [f"# Next Actions — {p.squad_run_id}", ""]
    for action in p.next_actions:
        lines.append(f"- [ ] {action}")
    return "\n".join(lines)


def no_secrets_in_manifest(manifest: dict) -> bool:
    for key in manifest:
        if any(key.lower().startswith(prefix) for prefix in FORBIDDEN_MANIFEST_PREFIXES):
            return False
    return True
