"""CLI for Task Decomposer."""
from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

task_decomposer_app = typer.Typer(
    name="tasks-plan",
    help="Task Decomposer — decompoe squads em tarefas determinísticas.",
    add_completion=False,
)
console = Console()


@task_decomposer_app.callback()
def _callback():
    """Task Decomposer — nenhuma tarefa é executada, apenas planejada."""


@task_decomposer_app.command(name="from-request")
def cmd_from_request(
    request: str = typer.Argument(..., help="Pedido em linguagem natural"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Gera plano de tarefas a partir de um pedido."""
    from src.squad_composer.composer import compose_squad
    from src.task_decomposer.decomposer import decompose_squad

    squad = compose_squad(request)
    plan = decompose_squad(squad)

    if json_out:
        console.print_json(json.dumps(plan.to_dict(), ensure_ascii=False))
        return

    color = {"low": "green", "medium": "yellow", "high": "red"}.get(plan.risk_level, "white")
    console.print(Panel(f"[bold]Task Plan[/bold] — {plan.task_plan_id}", expand=False))
    console.print(f"  squad_id       : {plan.squad_id}")
    console.print(f"  request        : {plan.request[:60]}")
    console.print(f"  risk           : [{color}]{plan.risk_level}[/{color}]")
    console.print(f"  approval_req   : {plan.approval_required}")
    console.print("")

    table = Table(title=f"Tasks ({len(plan.tasks)})")
    table.add_column("task_id", style="dim")
    table.add_column("role")
    table.add_column("title")
    table.add_column("output")
    table.add_column("depends_on")
    for t in plan.tasks:
        deps = ", ".join(t.depends_on) if t.depends_on else "—"
        table.add_row(t.task_id, t.role_id, t.title, t.expected_output, deps)
    console.print(table)


@task_decomposer_app.command(name="from-squad")
def cmd_from_squad(
    squad_id: str = typer.Argument(..., help="squad_id (informational — re-composes from request)"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Referência a squad_id (use from-request para gerar plano completo)."""
    console.print(f"[yellow]Hint:[/yellow] Use 'tasks-plan from-request \"<request>\"' para gerar plano completo.")
    console.print(f"  squad_id referenciado: {squad_id}")
