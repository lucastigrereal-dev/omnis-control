"""CLI for Sector Registry."""
from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

sector_registry_app = typer.Typer(
    name="sector-registry",
    help="Sector Registry — mapeamento de setores e keywords. Deterministico.",
    add_completion=False,
)
console = Console()


@sector_registry_app.callback()
def _callback():
    """Sector Registry — mapeamento declarativo de setores do OMNIS."""


@sector_registry_app.command(name="list")
def cmd_list(
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Lista todos os setores registrados."""
    from src.sector_registry.matcher import list_sectors

    sectors = list_sectors()
    if json_out:
        console.print_json(json.dumps([s.to_dict() for s in sectors], ensure_ascii=False))
        return

    table = Table(title="Sector Registry")
    table.add_column("sector_id", style="dim")
    table.add_column("name")
    table.add_column("risk")
    table.add_column("outputs")
    for s in sectors:
        risk_color = {"low": "green", "medium": "yellow", "high": "red"}.get(s.risk_level, "white")
        table.add_row(
            s.sector_id, s.name,
            f"[{risk_color}]{s.risk_level}[/{risk_color}]",
            ", ".join(s.default_outputs[:2]),
        )
    console.print(table)


@sector_registry_app.command(name="match")
def cmd_match(
    text: str = typer.Argument(..., help="Texto para detectar setor"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Detecta o setor mais provavel para um pedido."""
    from src.sector_registry.matcher import match_sector

    result = match_sector(text)
    if result is None:
        if json_out:
            console.print_json(json.dumps({"sector_id": "unknown", "confidence": 0.0}, ensure_ascii=False))
        else:
            console.print("[yellow]Nenhum setor identificado para o texto fornecido.[/yellow]")
        return

    if json_out:
        console.print_json(json.dumps(result.to_dict(), ensure_ascii=False))
        return

    risk_color = {"low": "green", "medium": "yellow", "high": "red"}.get(result.risk_level, "white")
    console.print(Panel(f"[bold]Setor Detectado[/bold]", expand=False))
    console.print(f"  sector     : {result.sector_id}")
    console.print(f"  name       : {result.sector_name}")
    console.print(f"  confidence : {result.confidence:.0%}")
    console.print(f"  risk       : [{risk_color}]{result.risk_level}[/{risk_color}]")
    console.print(f"  keywords   : {', '.join(result.matched_keywords)}")
    console.print(f"  outputs    : {', '.join(result.default_outputs)}")


@sector_registry_app.command(name="show")
def cmd_show(
    sector_id: str = typer.Argument(..., help="ID do setor (ex: marketing)"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Mostra detalhes de um setor."""
    from src.sector_registry.matcher import get_sector

    sector = get_sector(sector_id)
    if sector is None:
        console.print(f"[yellow]Setor '{sector_id}' nao encontrado.[/yellow]")
        raise typer.Exit(1)

    if json_out:
        console.print_json(json.dumps(sector.to_dict(), ensure_ascii=False))
        return

    risk_color = {"low": "green", "medium": "yellow", "high": "red"}.get(sector.risk_level, "white")
    console.print(Panel(f"[bold]{sector.name}[/bold] — {sector.sector_id}", expand=False))
    console.print(f"  risk_level : [{risk_color}]{sector.risk_level}[/{risk_color}]")
    console.print(f"  keywords   : {', '.join(sector.keywords[:8])}")
    console.print(f"  outputs    : {', '.join(sector.default_outputs)}")
