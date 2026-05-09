"""CLI for Mission Orchestrator Lite."""
from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

orchestrator_app = typer.Typer(
    name="orchestrator",
    help="Mission Orchestrator Lite — plano e execucao local. NUNCA publica.",
    add_completion=False,
)
console = Console()


@orchestrator_app.callback()
def _callback():
    """Mission Orchestrator — local, determinístico, sem LangGraph."""


@orchestrator_app.command(name="plan")
def cmd_plan(
    request: str = typer.Argument(..., help="Pedido em linguagem natural"),
    account: str = typer.Option("", "--account", help="Handle da conta (ex: oinatalrn)"),
    objective: str = typer.Option("engajamento", "--objective"),
    allow_unknown: bool = typer.Option(False, "--allow-unknown"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Gera plano de orquestracao sem executar."""
    from src.mission_orchestrator import service as svc
    from src.mission_orchestrator.errors import UnknownIntentError

    try:
        orch_run = svc.plan(
            request_text=request,
            account_handle=account,
            objective=objective,
            allow_unknown=allow_unknown,
        )
    except UnknownIntentError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)

    if json_out:
        console.print_json(json.dumps(orch_run.to_dict(), ensure_ascii=False))
        return

    console.print(Panel(f"[bold]Orchestrator Plan[/bold] — {orch_run.run_id}", expand=False))
    console.print(f"  intent    : {orch_run.intent}")
    console.print(f"  conta     : @{orch_run.account_handle}")
    console.print(f"  status    : {orch_run.status}")
    console.print("\n  [bold]Steps:[/bold]")
    for s in orch_run.steps:
        color = {"done": "green", "skipped": "dim", "failed": "red"}.get(s.status, "white")
        console.print(f"    [{color}][{s.status}][/{color}] {s.label}")


@orchestrator_app.command(name="run")
def cmd_run(
    request: str = typer.Argument(..., help="Pedido em linguagem natural"),
    account: str = typer.Option("", "--account", help="Handle da conta"),
    objective: str = typer.Option("engajamento", "--objective"),
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run"),
    allow_unknown: bool = typer.Option(False, "--allow-unknown"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Planejar + executar (dry-run) + persistir run."""
    from src.mission_orchestrator import service as svc
    from src.mission_orchestrator.errors import UnknownIntentError

    try:
        orch_run = svc.run(
            request_text=request,
            account_handle=account,
            objective=objective,
            dry_run=dry_run,
            allow_unknown=allow_unknown,
            runs_root=svc.DEFAULT_RUNS_ROOT,
            runs_log=svc.DEFAULT_RUNS_LOG,
        )
    except UnknownIntentError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)

    if json_out:
        console.print_json(json.dumps(orch_run.to_dict(), ensure_ascii=False))
        return

    status_color = "green" if orch_run.status in ("dry_run", "complete") else "red"
    console.print(Panel(f"[bold]Orchestrator Run[/bold] — {orch_run.run_id}", expand=False))
    console.print(f"  status    : [{status_color}]{orch_run.status}[/{status_color}]")
    console.print(f"  intent    : {orch_run.intent}")
    if orch_run.mission_id:
        console.print(f"  mission   : {orch_run.mission_id}")
    for s in orch_run.steps:
        color = {"done": "green", "skipped": "dim", "failed": "red"}.get(s.status, "white")
        console.print(f"  [{color}][{s.status}][/{color}] {s.label}")
    if orch_run.blockers:
        for b in orch_run.blockers:
            console.print(f"  [red]BLOCKER: {b}[/red]")
        raise typer.Exit(1)


@orchestrator_app.command(name="status")
def cmd_status(
    run_id: str = typer.Argument(..., help="run_id (ex: run_abc123)"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Mostra status de um run."""
    from src.mission_orchestrator import service as svc

    orch_run = svc.get_run(run_id, runs_log=svc.DEFAULT_RUNS_LOG)
    if orch_run is None:
        console.print(f"[yellow]Run {run_id} nao encontrado.[/yellow]")
        raise typer.Exit(1)

    if json_out:
        console.print_json(json.dumps(orch_run.to_dict(), ensure_ascii=False))
        return

    console.print(Panel(f"[bold]Run[/bold] — {orch_run.run_id}", expand=False))
    console.print(f"  status  : {orch_run.status}")
    console.print(f"  intent  : {orch_run.intent}")
    console.print(f"  criado  : {orch_run.created_at}")


@orchestrator_app.command(name="run-full")
def cmd_run_full(
    request: str = typer.Argument(..., help="Pedido em linguagem natural"),
    account: str = typer.Option("", "--account", help="Handle da conta"),
    objective: str = typer.Option("engajamento", "--objective"),
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run"),
    allow_unknown: bool = typer.Option(False, "--allow-unknown"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Pipeline completo: Orchestrator → Squad → Graph (dry-run)."""
    from src.execution_graph.mission_bridge import run_full_pipeline

    orch_run, step_run = run_full_pipeline(
        request_text=request,
        account_handle=account,
        objective=objective,
        dry_run=dry_run,
        allow_unknown=allow_unknown,
    )

    if orch_run is None:
        console.print("[red]Pipeline failed: orchestrator returned None[/red]")
        raise typer.Exit(1)

    if json_out:
        result = {
            "orchestrator": orch_run.to_dict(),
            "graph": step_run.to_dict() if step_run else None,
        }
        console.print_json(json.dumps(result, ensure_ascii=False))
        return

    orch_color = "green" if orch_run.status in ("dry_run", "complete") else "red"
    console.print(Panel(f"[bold]Full Pipeline Run[/bold] — {orch_run.run_id}", expand=False))
    console.print(f"  orchestrator    : [{orch_color}]{orch_run.status}[/{orch_color}]")
    console.print(f"  intent          : {orch_run.intent}")
    console.print(f"  sector          : {orch_run.sector_id}")
    console.print(f"  approval_req    : {orch_run.approval_required}")

    if step_run is None:
        console.print(f"  graph           : [red]not executed[/red]")
        if orch_run.blockers:
            for b in orch_run.blockers:
                console.print(f"  [red]BLOCKER: {b}[/red]")
        raise typer.Exit(1)

    graph_color = {"done": "green", "failed": "red", "blocked_pending_approval": "yellow"}.get(
        step_run.status, "yellow"
    )
    console.print(f"  graph_run_id    : {step_run.graph_run_id}")
    console.print(f"  graph_status    : [{graph_color}]{step_run.status}[/{graph_color}]")
    console.print(f"  steps executed  : {len(step_run.step_states)}")
    console.print(f"  squad_id        : {orch_run.squad_id or 'N/A'}")

    # Orchestrator steps
    console.print(f"\n  [bold]Orchestrator Steps:[/bold]")
    for s in orch_run.steps:
        color = {"done": "green", "skipped": "dim", "failed": "red"}.get(s.status, "white")
        console.print(f"    [{color}][{s.status}][/{color}] {s.label}")

    # Graph steps
    if step_run.status not in ("blocked_pending_approval",):
        table = Table(title="Graph Step States")
        table.add_column("step_id", style="dim")
        table.add_column("status")
        for sid, s in step_run.step_states.items():
            sc = {"done": "green", "failed": "red", "skipped": "yellow"}.get(s, "white")
            table.add_row(sid, f"[{sc}]{s}[/{sc}]")
        console.print(table)

    if orch_run.blockers:
        for b in orch_run.blockers:
            console.print(f"  [red]BLOCKER: {b}[/red]")


@orchestrator_app.command(name="list")
def cmd_list(
    limit: int = typer.Option(10, "--limit"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Lista runs recentes."""
    from src.mission_orchestrator import service as svc

    runs = svc.list_runs(runs_log=svc.DEFAULT_RUNS_LOG, limit=limit)
    if json_out:
        console.print_json(json.dumps([r.to_dict() for r in runs], ensure_ascii=False))
        return

    if not runs:
        console.print("[dim]Nenhum run registrado ainda.[/dim]")
        return

    table = Table(title="Orchestrator Runs")
    table.add_column("run_id", style="dim")
    table.add_column("intent")
    table.add_column("status")
    table.add_column("mission_id")
    table.add_column("criado")
    for r in runs:
        color = "green" if r.status in ("dry_run", "complete") else "red"
        table.add_row(
            r.run_id, r.intent,
            f"[{color}]{r.status}[/{color}]",
            r.mission_id or "—",
            r.created_at[:10],
        )
    console.print(table)
