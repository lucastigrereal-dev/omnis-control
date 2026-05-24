"""Orchestrator Service — plan, run, persist, list."""
from __future__ import annotations

import json
from pathlib import Path

from src.mission_orchestrator.models import OrchestratorRun, _now_iso
from src.mission_orchestrator.planner import build_plan
from src.mission_orchestrator.executor import execute
from src.mission_orchestrator.errors import RunNotFoundError
from src.mission_orchestrator.execution_manifest import write_manifest

BASE = Path(__file__).resolve().parent.parent.parent
DEFAULT_RUNS_ROOT = BASE / "exports" / "orchestrator_runs"
DEFAULT_RUNS_LOG = BASE / "data" / "orchestrator_runs.jsonl"


def plan(
    request_text: str,
    account_handle: str = "",
    objective: str = "engajamento",
    dry_run: bool = True,
    allow_unknown: bool = False,
    config_path: Path | None = None,
    run_context=None,
) -> OrchestratorRun:
    """Build a plan without executing. Returns OrchestratorRun."""
    return build_plan(
        request_text=request_text,
        account_handle=account_handle,
        objective=objective,
        dry_run=dry_run,
        allow_unknown=allow_unknown,
        config_path=config_path,
        run_context=run_context,
    )


def run(
    request_text: str,
    account_handle: str = "",
    objective: str = "engajamento",
    dry_run: bool = True,
    allow_unknown: bool = False,
    config_path: Path | None = None,
    runs_root: Path = DEFAULT_RUNS_ROOT,
    runs_log: Path = DEFAULT_RUNS_LOG,
    packages_root: Path | None = None,
    run_context=None,
) -> OrchestratorRun:
    """Plan + execute + persist. Returns OrchestratorRun.

    run_context: optional RunContext — when provided, propagates its run_id
    so orchestrator, graph, and LLM calls all share the same ID.
    """
    orch_run = build_plan(
        request_text=request_text,
        account_handle=account_handle,
        objective=objective,
        dry_run=dry_run,
        allow_unknown=allow_unknown,
        config_path=config_path,
        run_context=run_context,
    )
    orch_run = execute(orch_run, packages_root=packages_root)
    _persist(orch_run, runs_root, runs_log)
    return orch_run


def run_with_approval(
    request_text: str,
    account_handle: str = "",
    objective: str = "engajamento",
    dry_run: bool = True,
    allow_unknown: bool = False,
    approval_id: str | None = None,
    runs_root: Path = DEFAULT_RUNS_ROOT,
    runs_log: Path = DEFAULT_RUNS_LOG,
    packages_root: Path | None = None,
    approvals_log: Path | None = None,
    run_context=None,
) -> OrchestratorRun:
    """Plan + execute with approval gate enforcement. Returns OrchestratorRun."""
    orch_run = build_plan(
        request_text=request_text,
        account_handle=account_handle,
        objective=objective,
        dry_run=dry_run,
        allow_unknown=allow_unknown,
        run_context=run_context,
    )
    if approval_id is not None:
        orch_run.approval_id = approval_id
    orch_run = execute(orch_run, packages_root=packages_root, approvals_log=approvals_log)
    _persist(orch_run, runs_root, runs_log)
    return orch_run


def get_run(
    run_id: str,
    runs_log: Path = DEFAULT_RUNS_LOG,
) -> OrchestratorRun | None:
    """Load a run from the log by run_id."""
    if not runs_log.exists():
        return None
    with runs_log.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                if data.get("run_id") == run_id:
                    return OrchestratorRun.from_dict(data)
            except (json.JSONDecodeError, KeyError, TypeError):
                continue
    return None


def list_runs(
    runs_log: Path = DEFAULT_RUNS_LOG,
    limit: int = 20,
) -> list[OrchestratorRun]:
    """List runs newest first."""
    if not runs_log.exists():
        return []
    runs: list[OrchestratorRun] = []
    with runs_log.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                runs.append(OrchestratorRun.from_dict(data))
            except (json.JSONDecodeError, KeyError, TypeError):
                continue
    return list(reversed(runs))[:limit]


def _persist(
    orch_run: OrchestratorRun,
    runs_root: Path,
    runs_log: Path,
) -> None:
    """Write run folder + append to log."""
    run_dir = Path(runs_root) / orch_run.run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    _write(run_dir / "run_manifest.json", json.dumps(orch_run.to_dict(), ensure_ascii=False, indent=2))
    _write(run_dir / "01_request.md", f"# Request\n\n{orch_run.request_text}\n")
    _write(run_dir / "02_plan.md", _build_plan_md(orch_run))
    _write(run_dir / "03_execution_log.md", _build_exec_log_md(orch_run))
    _write(run_dir / "04_outputs.md", _build_outputs_md(orch_run))
    _write(run_dir / "05_next_action.md", _build_next_action_md(orch_run))
    write_manifest(orch_run, run_dir)

    Path(runs_log).parent.mkdir(parents=True, exist_ok=True)
    with Path(runs_log).open("a", encoding="utf-8") as f:
        f.write(json.dumps(orch_run.to_dict(), ensure_ascii=False) + "\n")


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _build_plan_md(r: OrchestratorRun) -> str:
    lines = [f"# Plan — {r.run_id}", "", f"**Pedido:** {r.request_text}",
             f"**Intent:** {r.intent}", f"**Conta:** @{r.account_handle}",
             f"**Objetivo:** {r.objective}", f"**Dry-run:** {r.dry_run}", ""]
    lines.append("## Steps")
    for s in r.steps:
        lines.append(f"- [{s.status}] {s.label}: `{s.command}`")
    return "\n".join(lines)


def _build_exec_log_md(r: OrchestratorRun) -> str:
    lines = [f"# Execution Log — {r.run_id}", ""]
    for s in r.steps:
        lines.append(f"## {s.step_id} — {s.label}")
        lines.append(f"- Status: {s.status}")
        if s.output:
            lines.append(f"- Output: {s.output}")
        if s.notes:
            lines.append(f"- Notes: {s.notes}")
        lines.append("")
    return "\n".join(lines)


def _build_outputs_md(r: OrchestratorRun) -> str:
    lines = [f"# Outputs — {r.run_id}", ""]
    if r.mission_id:
        lines.append(f"- **Mission Package:** {r.mission_id}")
    done = [s for s in r.steps if s.status == "done"]
    for s in done:
        if s.output:
            lines.append(f"- {s.label}: {s.output}")
    return "\n".join(lines)


def _build_next_action_md(r: OrchestratorRun) -> str:
    pending = [s for s in r.steps if s.status == "pending"]
    lines = [f"# Next Actions — {r.run_id}", ""]
    if not pending:
        lines.append("Todos os passos concluidos ou pulados.")
    for s in pending:
        lines.append(f"- [ ] {s.label}")
        lines.append(f"  `{s.command}`")
        if s.notes:
            lines.append(f"  _{s.notes}_")
    return "\n".join(lines)
