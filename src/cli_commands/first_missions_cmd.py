"""W186 — CLI commands for First Real Missions (W181-W185)."""
from __future__ import annotations

import json
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.first_missions.models import (
    Mission,
    MissionRegistry,
    MissionStatus,
    MissionType,
    MissionPriority,
)
from src.first_missions.orchestrator import MissionOrchestrator

first_missions_app = typer.Typer(
    name="first-missions",
    help="First Real Missions — runtime mission orchestration (G20 W181-W185)",
    add_completion=False,
)
console = Console()


def _orch(dry_run: bool = True) -> MissionOrchestrator:
    return MissionOrchestrator(dry_run=dry_run)


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

@first_missions_app.command(name="list")
def fm_list(
    status: Optional[str] = typer.Option(None, "--status", help="Filter by status"),
    mission_type: Optional[str] = typer.Option(None, "--type", help="Filter by mission type"),
    priority: Optional[str] = typer.Option(None, "--priority", help="Filter by priority"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """List registered missions with optional filters."""
    orch = _orch(dry_run=True)

    # Use registry's query
    st = MissionStatus(status) if status else None
    mt = MissionType(mission_type) if mission_type else None
    mp = MissionPriority(priority) if priority else None

    # Populate some demo missions for discoverability
    if orch.registry.stats()["total"] == 0:
        _seed_demo(orch)

    missions = orch.registry.query(status=st, mission_type=mt, priority=mp)

    if json_output:
        print(json.dumps([m.to_dict() for m in missions], indent=2, ensure_ascii=False))
        return

    if not missions:
        console.print("No missions registered. Create one with [cyan]first-missions create[/cyan]")
        return

    table = Table(title=f"First Real Missions ({len(missions)})")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name")
    table.add_column("Type")
    table.add_column("Priority")
    table.add_column("Status")

    status_style = {
        MissionStatus.PENDING: "[dim]PENDING[/dim]",
        MissionStatus.RUNNING: "[yellow]RUNNING[/yellow]",
        MissionStatus.COMPLETED: "[green]DONE[/green]",
        MissionStatus.FAILED: "[red]FAILED[/red]",
        MissionStatus.CANCELLED: "[red]CANCELLED[/red]",
        MissionStatus.DRY_RUN: "[blue]DRY_RUN[/blue]",
    }

    for m in missions:
        icon = status_style.get(m.status, "?")
        table.add_row(
            m.mission_id[:12],
            m.name[:30],
            m.mission_type.value[:25],
            m.priority.value,
            f"{icon} {m.status.value}",
        )
    console.print(table)
    console.print(f"\n[dim]Registry: {orch.registry.stats()['total']} total, {orch.scheduler.stats()['pending']} pending[/dim]")


# ---------------------------------------------------------------------------
# Show
# ---------------------------------------------------------------------------

@first_missions_app.command(name="show")
def fm_show(
    mission_id: str = typer.Argument(..., help="Mission ID (full or prefix)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Show full details of a mission by ID."""
    orch = _orch(dry_run=True)
    _seed_demo(orch)

    actual = _resolve_id(orch, mission_id)
    if actual is None:
        console.print(f"[red]Mission not found: {mission_id}[/red]")
        raise typer.Exit(1)

    m = orch.registry.get(actual)
    if m is None:
        console.print(f"[red]Mission not found: {mission_id}[/red]")
        raise typer.Exit(1)

    if json_output:
        print(json.dumps(m.to_dict(), indent=2, ensure_ascii=False))
        return

    console.print(f"[bold]Mission: {m.name}[/bold]")
    console.print(f"  ID: [cyan]{m.mission_id}[/cyan]")
    console.print(f"  Type: {m.mission_type.value}")
    console.print(f"  Priority: {m.priority.value}")
    console.print(f"  Status: {m.status.value}")
    console.print(f"  Dry-run: {'[blue]Yes[/blue]' if m.dry_run else '[red]No (LIVE)[/red]'}")
    console.print(f"  Tags: {', '.join(m.tags) if m.tags else '-'}")

    if m.payload:
        console.print(f"\n  Payload:")
        for k, v in m.payload.items():
            console.print(f"    {k}: {v}")

    if m.result:
        console.print(f"\n  Result:")
        console.print(Panel(json.dumps(m.result, indent=2), title="result"))

    if m.error:
        console.print(f"\n  [red]Error: {m.error}[/red]")

    console.print(f"\n  Created: {m.created_at}")
    if m.started_at:
        console.print(f"  Started: {m.started_at}")
    if m.completed_at:
        console.print(f"  Completed: {m.completed_at}")


# ---------------------------------------------------------------------------
# Run / Execute
# ---------------------------------------------------------------------------

@first_missions_app.command(name="run")
def fm_run(
    mission_id: str = typer.Argument(..., help="Mission ID to execute"),
    live: bool = typer.Option(False, "--live", help="Execute for real (not dry-run)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Execute a single mission. Dry-run by default — use --live for real execution."""
    orch = _orch(dry_run=not live)
    _seed_demo(orch)

    actual = _resolve_id(orch, mission_id)
    if actual is None:
        console.print(f"[red]Mission not found: {mission_id}[/red]")
        raise typer.Exit(1)

    m = orch.registry.get(actual)
    if m is None:
        console.print(f"[red]Mission not found: {mission_id}[/red]")
        raise typer.Exit(1)

    if m.is_terminal:
        console.print(f"[yellow]Mission already in terminal state: {m.status.value}[/yellow]")
        console.print("Create a new mission or reset this one first.")
        raise typer.Exit(1)

    stored = orch.run_one(m)

    if json_output:
        print(json.dumps(stored.to_dict(), indent=2, ensure_ascii=False))
        return

    if stored.status == "COMPLETED":
        console.print(f"[green]Mission executed successfully![/green]")
    else:
        console.print(f"[red]Mission failed: {stored.error}[/red]")

    console.print(f"  Result ID: [cyan]{stored.result_id}[/cyan]")
    console.print(f"  Duration: {stored.duration_ms}ms")
    console.print(f"  Dry-run: {'[blue]Yes[/blue]' if stored.dry_run else '[yellow]No (LIVE)[/yellow]'}")


# ---------------------------------------------------------------------------
# Preview
# ---------------------------------------------------------------------------

@first_missions_app.command(name="preview")
def fm_preview(
    mission_id: str = typer.Argument(..., help="Mission ID to preview"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Preview what a mission would do — never changes state."""
    orch = _orch(dry_run=True)
    _seed_demo(orch)

    actual = _resolve_id(orch, mission_id)
    if actual is None:
        console.print(f"[red]Mission not found: {mission_id}[/red]")
        raise typer.Exit(1)

    m = orch.registry.get(actual)
    if m is None:
        console.print(f"[red]Mission not found: {mission_id}[/red]")
        raise typer.Exit(1)

    p = orch.preview(m)

    if json_output:
        print(json.dumps(p, indent=2, ensure_ascii=False))
        return

    console.print(f"[bold]Preview — {p['name']}[/bold]")
    console.print(f"  Mission ID: [cyan]{p['mission_id']}[/cyan]")
    console.print(f"  Type: {p['mission_type']}")
    console.print(f"  Priority: {p['priority']}")
    console.print(f"  Would execute: [yellow]{p['would_execute']}[/yellow]")
    console.print(f"  Would store: {'[green]Yes[/green]' if p['would_store'] else '[red]No[/red]'}")
    console.print(f"\n  [dim]{p['note']}[/dim]")


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

@first_missions_app.command(name="create")
def fm_create(
    name: str = typer.Option(..., "--name", help="Mission name"),
    mission_type: str = typer.Option("CUSTOM", "--type", help="Mission type"),
    priority: str = typer.Option("NORMAL", "--priority", help="LOW | NORMAL | HIGH | CRITICAL"),
    profile: Optional[str] = typer.Option(None, "--profile", help="Instagram profile (for content missions)"),
    topic: Optional[str] = typer.Option(None, "--topic", help="Content topic"),
    metric: Optional[str] = typer.Option(None, "--metric", help="Metric name (for metric missions)"),
    period: str = typer.Option("daily", "--period", help="Metric period"),
    tags: Optional[str] = typer.Option(None, "--tags", help="Tags comma-separated"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Create a new mission and add it to the registry."""
    orch = _orch(dry_run=True)

    try:
        mt = MissionType(mission_type)
    except ValueError:
        types = [t.value for t in MissionType]
        console.print(f"[red]Invalid type: '{mission_type}'. Options: {', '.join(types)}[/red]")
        raise typer.Exit(1)

    try:
        mp = MissionPriority(priority)
    except ValueError:
        levels = [p.value for p in MissionPriority]
        console.print(f"[red]Invalid priority: '{priority}'. Options: {', '.join(levels)}[/red]")
        raise typer.Exit(1)

    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    # Use factory methods for common types
    if mt == MissionType.CONTENT_GENERATION and profile and topic:
        m = Mission.content_generation(profile, topic)
        m.name = name
        m.tags = tag_list
        m.priority = mp
    elif mt == MissionType.METRIC_REPORT and metric:
        m = Mission.metric_report(metric, period)
        m.name = name
        m.tags = tag_list
        m.priority = mp
    elif mt == MissionType.HEALTH_SNAPSHOT:
        m = Mission.health_snapshot()
        m.name = name
        m.tags = tag_list
    else:
        m = Mission(
            name=name,
            mission_type=mt,
            priority=mp,
            tags=tag_list,
        )

    orch.submit(m)

    if json_output:
        print(json.dumps(m.to_dict(), indent=2, ensure_ascii=False))
    else:
        console.print(f"[green]Mission created and scheduled![/green]")
        console.print(f"  ID: [cyan]{m.mission_id}[/cyan]")
        console.print(f"  Name: {m.name}")
        console.print(f"  Type: {m.mission_type.value}")
        console.print(f"  Status: {m.status.value}")


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

@first_missions_app.command(name="stats")
def fm_stats(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Show aggregate stats from the orchestrator."""
    orch = _orch(dry_run=True)
    s = orch.status()

    if json_output:
        print(json.dumps(s, indent=2, ensure_ascii=False))
        return

    console.print("[bold]First Real Missions — Stats[/bold]\n")
    reg = s["registry"]
    console.print(f"  Registry: {reg['total']} total")
    if reg.get("by_status"):
        for st, count in sorted(reg["by_status"].items()):
            console.print(f"    {st}: {count}")

    sched = s["scheduler"]
    console.print(f"\n  Scheduler: {sched['queued']} queued, {sched['pending']} pending, {sched['dispatched']} dispatched")

    exe = s["executor"]
    console.print(f"\n  Executor: {exe['total_executions']} executed ({exe['successful']} ok, {exe['failed']} fail)")

    store = s["result_store"]
    console.print(f"\n  Results: {store['total']} stored")


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------

@first_missions_app.command(name="results")
def fm_results(
    status: Optional[str] = typer.Option(None, "--status", help="Filter by status"),
    mission_type: Optional[str] = typer.Option(None, "--type", help="Filter by mission type"),
    limit: int = typer.Option(20, "--limit", help="Max results"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """List stored mission results with optional filters."""
    orch = _orch(dry_run=True)
    results = orch.result_store.query(
        status=status,
        mission_type=mission_type,
        limit=limit,
    )

    if json_output:
        print(json.dumps([r.to_dict() for r in results], indent=2, ensure_ascii=False))
        return

    if not results:
        console.print("No results stored. Run a mission first.")
        return

    table = Table(title=f"Mission Results ({len(results)})")
    table.add_column("Result ID", style="cyan", no_wrap=True)
    table.add_column("Mission")
    table.add_column("Type")
    table.add_column("Status")
    table.add_column("Duration")
    table.add_column("Stored")

    status_style = {
        "COMPLETED": "[green]DONE[/green]",
        "FAILED": "[red]FAIL[/red]",
        "DRY_RUN": "[blue]DRY[/blue]",
    }

    for r in results:
        icon = status_style.get(r.status, r.status)
        table.add_row(
            r.result_id[:12],
            r.mission_name[:25],
            r.mission_type[:20],
            f"{icon}",
            f"{r.duration_ms:.0f}ms",
            r.stored_at[:16] if r.stored_at else "-",
        )
    console.print(table)


@first_missions_app.command(name="result-show")
def fm_result_show(
    result_id: str = typer.Argument(..., help="Result ID to show"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Show full details of a stored result."""
    orch = _orch(dry_run=True)
    r = orch.result_store.get(result_id)
    if r is None:
        console.print(f"[red]Result not found: {result_id}[/red]")
        raise typer.Exit(1)

    if json_output:
        print(json.dumps(r.to_dict(), indent=2, ensure_ascii=False))
        return

    console.print(f"[bold]Result: {r.result_id}[/bold]")
    console.print(f"  Mission ID: [cyan]{r.mission_id}[/cyan]")
    console.print(f"  Mission Name: {r.mission_name}")
    console.print(f"  Type: {r.mission_type}")
    console.print(f"  Status: {r.status}")
    console.print(f"  Duration: {r.duration_ms}ms")
    console.print(f"  Dry-run: {'[blue]Yes[/blue]' if r.dry_run else '[red]No (LIVE)[/red]'}")

    if r.result:
        console.print(f"\n  Result Data:")
        console.print(Panel(json.dumps(r.result, indent=2), title="result"))

    if r.error:
        console.print(f"\n  [red]Error: {r.error}[/red]")

    console.print(f"\n  Stored at: {r.stored_at}")


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

@first_missions_app.command(name="metrics")
def fm_metrics(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Show mission execution metrics summary."""
    orch = _orch(dry_run=True)
    s = orch.result_store.summary()

    if json_output:
        print(json.dumps(s, indent=2, ensure_ascii=False))
        return

    if s["total"] == 0:
        console.print("No results stored — metrics unavailable.")
        return

    console.print("[bold]Mission Metrics Summary[/bold]\n")
    console.print(f"  Total executions: {s['total']}")
    console.print(f"  Successful: [green]{s['successful']}[/green]")
    console.print(f"  Failed: [red]{s['failed']}[/red]")
    console.print(f"  Dry-run: [blue]{s['dry_run']}[/blue]")
    console.print(f"  Success rate: {s['success_rate']:.1%}")
    console.print(f"  Avg duration: {s['avg_duration_ms']:.1f}ms")


# ---------------------------------------------------------------------------
# Validate
# ---------------------------------------------------------------------------

@first_missions_app.command(name="validate")
def fm_validate(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Validate all registered missions and report issues."""
    orch = _orch(dry_run=True)
    _seed_demo(orch)
    report = orch.registry.validate()

    if json_output:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return

    if report["valid"]:
        console.print(f"[green]All {report['total']} missions valid — no issues.[/green]")
    else:
        console.print(f"[yellow]{report['issues']} issue(s) found in {report['total']} missions:[/yellow]")
        for d in report["details"]:
            icon = "[red]ERROR[/red]" if d["severity"] == "error" else "[yellow]WARN[/yellow]"
            console.print(f"  {icon} [{d['mission_id'][:12]}] {d['issue']}")


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

@first_missions_app.command(name="schedule")
def fm_schedule(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """List all scheduled missions (pending + waiting)."""
    orch = _orch(dry_run=True)
    _seed_demo(orch)

    entries = orch.scheduler.pending()

    if json_output:
        print(json.dumps([e.to_dict() for e in entries], indent=2, ensure_ascii=False))
        return

    if not entries:
        stats = orch.scheduler.stats()
        console.print(f"No pending entries. Queue: {stats['queued']}, Dispatched: {stats['dispatched']}")
        return

    table = Table(title=f"Scheduled Missions ({len(entries)})")
    table.add_column("Entry ID", style="cyan", no_wrap=True)
    table.add_column("Mission")
    table.add_column("Status")
    table.add_column("Run At")
    table.add_column("Recurrent")

    for e in entries:
        table.add_row(
            e.entry_id[:12],
            (e.mission.name[:25] if e.mission else "?"),
            e.status.value,
            e.run_at[:16] if e.run_at else "now",
            "[green]Yes[/green]" if e.recurrent else "-",
        )
    console.print(table)


@first_missions_app.command(name="schedule-add")
def fm_schedule_add(
    mission_id: str = typer.Argument(..., help="Mission ID to schedule"),
    run_at: Optional[str] = typer.Option(None, "--at", help="ISO timestamp (empty = now)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Add a mission to the scheduler (dry-run by default)."""
    orch = _orch(dry_run=True)
    _seed_demo(orch)

    actual = _resolve_id(orch, mission_id)
    if actual is None:
        console.print(f"[red]Mission not found: {mission_id}[/red]")
        raise typer.Exit(1)

    m = orch.registry.get(actual)
    if m is None:
        console.print(f"[red]Mission not found: {mission_id}[/red]")
        raise typer.Exit(1)

    entry = orch.scheduler.schedule(m, run_at=run_at or "")

    if json_output:
        print(json.dumps(entry.to_dict(), indent=2, ensure_ascii=False))
    else:
        console.print(f"[green]Mission scheduled![/green]")
        console.print(f"  Entry ID: [cyan]{entry.entry_id}[/cyan]")
        console.print(f"  Mission: {m.name}")
        console.print(f"  Run at: {run_at or 'immediate'}")
        console.print(f"  Status: {entry.status.value}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _seed_demo(orch: MissionOrchestrator) -> None:
    """Seed demo missions for discoverability on first use."""
    if orch.registry.stats()["total"] > 0:
        return
    for m in [
        Mission.content_generation("lucastigrereal", "travel tips"),
        Mission.metric_report("followers", "daily"),
        Mission.health_snapshot(),
    ]:
        orch.registry.register(m)


def _resolve_id(orch: MissionOrchestrator, id_fragment: str) -> Optional[str]:
    """Resolve mission ID by exact match or prefix."""
    # Exact match
    if orch.registry.get(id_fragment):
        return id_fragment

    # Prefix match
    missions = orch.registry.query(limit=500)
    candidates = [m.mission_id for m in missions if m.mission_id.startswith(id_fragment)]
    if len(candidates) == 1:
        return candidates[0]
    return None
