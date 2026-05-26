"""CLI 'runs' — visualiza histórico de mission runs.

Comandos:
    runs list [--limit N] [--command X] [--status X]
    runs show <run_id>
    runs log  <command> [--status success|error] [--note TEXT]
"""
from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.table import Table

runs_app = typer.Typer(
    name="runs",
    help="Histórico de mission runs (wave executions).",
    add_completion=False,
)
console = Console()


@runs_app.command(name="list")
def cmd_list(
    limit: int = typer.Option(20, "--limit", help="Máximo de runs a exibir"),
    command: str = typer.Option("", "--command", "-c", help="Filtra por comando"),
    status: str = typer.Option("", "--status", "-s", help="Filtra por status"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Lista os últimos mission runs."""
    from src.mission_logger import MissionLogger

    runs = MissionLogger.read_runs(
        limit=limit,
        command_filter=command or None,
        status_filter=status or None,
    )

    if json_out:
        console.print_json(json.dumps([r.to_dict() for r in runs], ensure_ascii=False))
        return

    if not runs:
        console.print("[yellow]Nenhum run registrado.[/yellow]")
        return

    table = Table(title=f"Mission Runs ({len(runs)} mais recentes)")
    table.add_column("run_id",   style="cyan",  width=12)
    table.add_column("command",  style="blue",  width=16)
    table.add_column("module",   style="dim",   width=20)
    table.add_column("status",   width=8)
    table.add_column("dur(ms)",  justify="right", width=8)
    table.add_column("started",  width=20)

    _S = {"success": "green", "error": "red", "aborted": "yellow"}
    for r in runs:
        s_style = _S.get(r.status, "dim")
        table.add_row(
            r.run_id[:10],
            r.command,
            r.module[:20],
            f"[{s_style}]{r.status}[/{s_style}]",
            str(r.duration_ms),
            (r.started_at or "")[:19],
        )
    console.print(table)


@runs_app.command(name="show")
def cmd_show(
    run_id: str = typer.Argument(..., help="ID do run"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Exibe detalhes de um run específico."""
    from src.mission_logger import MissionLogger

    runs = MissionLogger.read_runs(limit=500)
    match = next((r for r in runs if r.run_id.startswith(run_id)), None)
    if not match:
        console.print(f"[red]Run '{run_id}' não encontrado.[/red]")
        raise typer.Exit(1)

    if json_out:
        console.print_json(json.dumps(match.to_dict(), ensure_ascii=False))
        return

    console.print(f"[bold]Run:[/bold] {match.run_id}")
    console.print(f"  command:  {match.command}")
    console.print(f"  module:   {match.module}")
    console.print(f"  status:   {match.status}")
    console.print(f"  duration: {match.duration_ms}ms")
    console.print(f"  started:  {match.started_at}")
    if match.inputs:
        console.print("  inputs:")
        for k, v in match.inputs.items():
            console.print(f"    {k}: {v}")
    if match.outputs:
        console.print("  outputs:")
        for k, v in match.outputs.items():
            console.print(f"    {k}: {v}")
    if match.warnings:
        for w in match.warnings:
            console.print(f"  [yellow]AVISO:[/yellow] {w}")
    if match.errors:
        for e in match.errors:
            console.print(f"  [red]ERRO:[/red] {e}")


@runs_app.command(name="log")
def cmd_log(
    command: str = typer.Argument(..., help="Nome do comando/wave"),
    module: str = typer.Option("cli", "--module", "-m"),
    status_val: str = typer.Option("success", "--status", "-s", help="success|error"),
    note: str = typer.Option("", "--note", "-n", help="Nota livre"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Loga manualmente uma execução (útil para testes de rastro)."""
    from src.mission_logger import MissionLogger

    ml = MissionLogger.start(command=command, module=module)
    if note:
        ml.add_metadata("note", note)
    run = ml.finish(status=status_val)

    if json_out:
        console.print_json(json.dumps(run.to_dict(), ensure_ascii=False))
        return

    console.print(f"[green]Run registrado:[/green] {run.run_id}")
    console.print(f"  command: {run.command}")
    console.print(f"  status:  {run.status}")
    console.print(f"  dur:     {run.duration_ms}ms")
