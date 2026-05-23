"""CLI commands for the CaptionDraftAgent — `omnis agent <cmd>`."""
from __future__ import annotations

import json
import os

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.agentic.agent_models import AgentRunRepository, AgentRunStatus, StepStatus
from src.agentic.caption_draft_agent import CaptionDraftAgent
from src.memory.caption_memory import CaptionMemoryReader

agent_app = typer.Typer(name="agent", help="CaptionDraftAgent — loop completo de geração")
console = Console()

_ROOT = os.path.normpath(os.getenv("OMNIS_ROOT", os.path.expanduser("~/omnis-control")))


# ── run ───────────────────────────────────────────────────────────────────────

@agent_app.command(name="run")
def agent_run(
    queue_id: str = typer.Argument(..., help="ID do QueueItem a processar"),
    dry_run: bool = typer.Option(True, "--dry-run/--real", help="Simula sem persistir"),
    json_out: bool = typer.Option(False, "--json", help="Saída em JSON"),
) -> None:
    """Executa o loop completo para um item da fila."""
    agent = CaptionDraftAgent(dry_run=dry_run)
    run = agent.run(queue_id)

    if json_out:
        console.print_json(json.dumps(run.to_dict()))
        raise typer.Exit(0 if run.status != AgentRunStatus.FAILED else 1)

    _print_run(run)
    raise typer.Exit(0 if run.status != AgentRunStatus.FAILED else 1)


# ── runs (histórico) ──────────────────────────────────────────────────────────

@agent_app.command(name="runs")
def agent_runs(
    limit: int = typer.Option(10, "--limit", "-n", help="Número de runs a mostrar"),
    account: str | None = typer.Option(None, "--account", "-a", help="Filtrar por conta"),
    json_out: bool = typer.Option(False, "--json", help="Saída em JSON"),
) -> None:
    """Lista runs anteriores do agente."""
    repo = AgentRunRepository()
    runs = repo.list_all()
    if account:
        runs = [r for r in runs if r.account_handle == account]
    runs = list(reversed(runs))[:limit]

    if json_out:
        console.print_json(json.dumps([r.to_dict() for r in runs]))
        return

    if not runs:
        console.print("[yellow]Nenhum run encontrado.[/yellow]")
        return

    table = Table(title=f"Agent Runs (últimos {len(runs)})", show_lines=False)
    table.add_column("run_id", style="cyan", no_wrap=True)
    table.add_column("account", style="white")
    table.add_column("objective", style="white")
    table.add_column("status", style="bold")
    table.add_column("gate", style="white")
    table.add_column("steps", justify="right")
    table.add_column("started_at", style="dim")

    for r in runs:
        status_color = {
            AgentRunStatus.COMPLETED: "green",
            AgentRunStatus.DRY_RUN: "blue",
            AgentRunStatus.FAILED: "red",
            AgentRunStatus.RUNNING: "yellow",
        }.get(r.status, "white")
        gate = r.result.get("gate_verdict", "—") if r.result else "—"
        table.add_row(
            r.run_id,
            r.account_handle,
            r.objective,
            f"[{status_color}]{r.status}[/{status_color}]",
            str(gate),
            str(len(r.steps)),
            r.started_at[:19].replace("T", " "),
        )
    console.print(table)


# ── memory ────────────────────────────────────────────────────────────────────

@agent_app.command(name="memory")
def agent_memory(
    account: str | None = typer.Option(None, "--account", "-a", help="Filtrar por conta"),
    objective: str | None = typer.Option(None, "--objective", "-o", help="Filtrar por objetivo"),
    limit: int = typer.Option(5, "--limit", "-n"),
) -> None:
    """Mostra legendas aprovadas gravadas na memória do agente."""
    reader = CaptionMemoryReader()

    if account and objective:
        captions = reader.find_similar(account, objective, top_k=limit)
        if not captions:
            console.print(f"[yellow]Nenhuma legenda na memória para {account}/{objective}[/yellow]")
            return
        console.print(f"[bold]Memória:[/bold] {account} / {objective} ({len(captions)} entradas)")
        for i, text in enumerate(captions, 1):
            console.print(Panel(text, title=f"#{i}", expand=False))
        return

    total = reader.count(account)
    label = account or "todas as contas"
    console.print(f"[bold]Legendas na memória[/bold] — {label}: [cyan]{total}[/cyan] entradas")


# ── internals ─────────────────────────────────────────────────────────────────

def _print_run(run) -> None:  # type: ignore[no-untyped-def]
    status_color = {
        AgentRunStatus.COMPLETED: "green",
        AgentRunStatus.DRY_RUN: "blue",
        AgentRunStatus.FAILED: "red",
    }.get(run.status, "white")

    console.print(f"\n[bold]Run[/bold] [cyan]{run.run_id}[/cyan]  "
                  f"[{status_color}]{run.status}[/{status_color}]")
    console.print(f"  Conta:    {run.account_handle}")
    console.print(f"  Objetivo: {run.objective}")

    table = Table(show_header=True, show_lines=False, box=None, padding=(0, 1))
    table.add_column("step", style="dim", width=20)
    table.add_column("status", width=10)
    table.add_column("output", style="white")

    for step in run.steps:
        s_color = {
            StepStatus.OK: "green",
            StepStatus.ERROR: "red",
            StepStatus.SKIPPED: "yellow",
        }.get(step.status, "white")
        summary = step.output_summary or step.error or ""
        table.add_row(step.name, f"[{s_color}]{step.status}[/{s_color}]", summary[:80])
    console.print(table)

    if run.result:
        console.print(f"\n  gate:    {run.result.get('gate_verdict', '—')}")
        console.print(f"  draft:   {run.result.get('draft_id', '—')}")
        console.print(f"  memory:  {'✓' if run.result.get('memory_written') else '—'}")
        console.print(f"  model:   {run.result.get('model_used', '—')}")

    if run.error:
        console.print(f"\n[red]Erro:[/red] {run.error}")
