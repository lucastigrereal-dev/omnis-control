"""CLI for Squad Composer."""
from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

squad_composer_app = typer.Typer(
    name="squad",
    help="Squad Composer — compoe squads locais a partir de um pedido.",
    add_completion=False,
)
console = Console()


@squad_composer_app.callback()
def _callback():
    """Squad Composer — determinístico, sem LLM, sem agentes reais."""


@squad_composer_app.command(name="compose")
def cmd_compose(
    request: str = typer.Argument(..., help="Pedido em linguagem natural"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Compoe um squad para o pedido dado."""
    from src.squad_composer.composer import compose_squad

    plan = compose_squad(request)

    if json_out:
        console.print_json(json.dumps(plan.to_dict(), ensure_ascii=False))
        return

    color = {"low": "green", "medium": "yellow", "high": "red"}.get(plan.risk_level, "white")
    console.print(Panel(f"[bold]Squad Plan[/bold] — {plan.squad_id}", expand=False))
    console.print(f"  request         : {plan.request[:60]}")
    console.print(f"  sector          : {plan.sector}")
    console.print(f"  risk            : [{color}]{plan.risk_level}[/{color}]")
    console.print(f"  approval_req    : {plan.approval_required}")
    console.print(f"  rationale       : {plan.rationale}")
    if plan.warnings:
        for w in plan.warnings:
            console.print(f"  [yellow]warn[/yellow]          : {w}")
    console.print("")

    table = Table(title="Roles")
    table.add_column("role_id", style="dim")
    table.add_column("name")
    table.add_column("risk")
    table.add_column("outputs")
    for r in plan.roles:
        rc = {"low": "white", "medium": "yellow", "high": "red"}.get(r.risk_level, "white")
        table.add_row(r.role_id, r.role_name, f"[{rc}]{r.risk_level}[/{rc}]", ", ".join(r.expected_outputs[:3]))
    console.print(table)

    if plan.next_actions:
        console.print(f"\n  next : {plan.next_actions[0]}")
