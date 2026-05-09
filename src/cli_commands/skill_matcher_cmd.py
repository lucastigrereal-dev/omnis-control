"""CLI for Skill Matcher Lite."""
from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

skill_matcher_app = typer.Typer(
    name="skill-matcher",
    help="Skill Matcher Lite — sugere capabilities disponiveis para um pedido.",
    add_completion=False,
)
console = Console()


@skill_matcher_app.callback()
def _callback():
    """Skill Matcher — keyword-based, sem LLM, sem rede."""


@skill_matcher_app.command(name="list")
def cmd_list(
    sector: str = typer.Option("", "--sector", help="Filtrar por setor"),
    all_caps: bool = typer.Option(False, "--all", help="Incluir inativas"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Lista capabilities disponíveis."""
    from src.skill_matcher.matcher import list_capabilities

    caps = list_capabilities(active_only=not all_caps)
    if sector:
        caps = [c for c in caps if c.sector == sector]

    if json_out:
        console.print_json(json.dumps([c.to_dict() for c in caps], ensure_ascii=False))
        return

    table = Table(title="Capabilities")
    table.add_column("capability_id", style="dim")
    table.add_column("sector")
    table.add_column("output")
    table.add_column("risk")
    for c in caps:
        risk_color = {"low": "green", "medium": "yellow", "high": "red"}.get(c.risk_level, "white")
        table.add_row(c.capability_id, c.sector, c.output,
                      f"[{risk_color}]{c.risk_level}[/{risk_color}]")
    console.print(table)


@skill_matcher_app.command(name="match")
def cmd_match(
    text: str = typer.Argument(..., help="Texto do pedido"),
    sector: str = typer.Option("", "--sector", help="Limitar a setor"),
    limit: int = typer.Option(5, "--limit"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Sugere capabilities para um pedido."""
    from src.skill_matcher.matcher import match_capabilities

    results = match_capabilities(text, sector_filter=sector or None, limit=limit)

    if json_out:
        console.print_json(json.dumps([r.to_dict() for r in results], ensure_ascii=False))
        return

    if not results:
        console.print("[yellow]Nenhuma capability encontrada para o texto.[/yellow]")
        return

    console.print(Panel("[bold]Capabilities Sugeridas[/bold]", expand=False))
    for r in results:
        risk_color = {"low": "green", "medium": "yellow", "high": "red"}.get(r.risk_level, "white")
        approval = " [red][approval required][/red]" if r.requires_approval else ""
        console.print(f"  [{risk_color}]{r.capability_id}[/{risk_color}]{approval}")
        console.print(f"    cmd: {r.command}")
        console.print(f"    out: {r.output} | conf: {r.confidence:.0%}")


@skill_matcher_app.command(name="show")
def cmd_show(
    capability_id: str = typer.Argument(..., help="ID da capability"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Mostra detalhes de uma capability."""
    from src.skill_matcher.matcher import get_capability

    cap = get_capability(capability_id)
    if cap is None:
        console.print(f"[yellow]Capability '{capability_id}' nao encontrada.[/yellow]")
        raise typer.Exit(1)

    if json_out:
        console.print_json(json.dumps(cap.to_dict(), ensure_ascii=False))
        return

    risk_color = {"low": "green", "medium": "yellow", "high": "red"}.get(cap.risk_level, "white")
    console.print(Panel(f"[bold]{cap.capability_id}[/bold]", expand=False))
    console.print(f"  sector     : {cap.sector}")
    console.print(f"  command    : {cap.command}")
    console.print(f"  output     : {cap.output}")
    console.print(f"  risk_level : [{risk_color}]{cap.risk_level}[/{risk_color}]")
    console.print(f"  status     : {cap.status}")
