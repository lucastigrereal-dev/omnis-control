"""CLI commands for Creative Production OS (Fase 2D)."""

import json
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from src.creative_production.briefs import get_brief, list_briefs, brief_stats
from src.creative_production.exporter import generate_export_package, list_packages

creative_app = typer.Typer(
    name="creative",
    help="Creative Production OS — briefs, export packages",
    add_completion=False,
)
console = Console()


@creative_app.command("status")
def cmd_status():
    """Status do módulo Creative Production."""
    stats = brief_stats()
    packages = list_packages()

    console.print("[bold]Creative Production OS[/bold]\n")

    console.print(f"[bold]Briefs:[/bold] {stats['total']} total")
    for st, count in sorted(stats.get("by_status", {}).items()):
        console.print(f"  - {st}: {count}")
    console.print(f"  - Por formato: {stats.get('by_format', {})}")

    console.print(f"\n[bold]Export Packages:[/bold] {len(packages)}")
    for p in packages:
        warn = " ⚠️" if p["has_warnings"] else ""
        console.print(f"  - {p['name']} ({p['file_count']} files){warn}")

    console.print("\n[dim]Pipeline: Queue → Caption Draft → Brief → Export → Argos (futuro)[/dim]")


@creative_app.command("list")
def cmd_list(
    limit: int = typer.Option(20, "--limit", "-l", help="Máximo de briefs"),
):
    """Lista creative briefs."""
    briefs = list_briefs()
    if not briefs:
        console.print("[yellow]Nenhum brief encontrado.[/yellow]")
        return

    table = Table(title=f"Creative Briefs ({len(briefs)})")
    table.add_column("ID", style="cyan")
    table.add_column("Conta")
    table.add_column("Formato")
    table.add_column("Objetivo")
    table.add_column("Status")
    for b in briefs[:limit]:
        table.add_row(
            b.creative_brief_id[:12],
            f"@{b.account_handle}" if b.account_handle else "-",
            b.format or "-",
            b.objective or "-",
            b.status or "-",
        )
    console.print(table)
    if len(briefs) > limit:
        console.print(f"[dim]({len(briefs) - limit} mais — use --limit {len(briefs)} para ver todos)[/dim]")


@creative_app.command("show")
def cmd_show(
    brief_id: str = typer.Argument(..., help="ID do creative brief"),
):
    """Mostra detalhes de um creative brief."""
    brief = get_brief(brief_id)
    if not brief:
        console.print(f"[red]Brief '{brief_id}' não encontrado.[/red]")
        raise typer.Exit(1)

    console.print(f"[bold]Creative Brief:[/bold] {brief.creative_brief_id}")
    console.print(f"  Queue ID: {brief.queue_id or '-'}")
    console.print(f"  Caption Draft ID: {brief.caption_draft_id or '-'}")
    console.print(f"  Conta: @{brief.account_handle or '-'}")
    console.print(f"  Formato: {brief.format or '-'}")
    console.print(f"  Objetivo: {brief.objective or '-'}")
    console.print(f"  Direção Visual: {brief.visual_direction or '-'}")
    console.print(f"  Status: {brief.status or '-'}")
    console.print(f"  Criado: {brief.created_at or '-'}")
    console.print(f"  Atualizado: {brief.updated_at or '-'}")

    if brief.script:
        snippet = brief.script[:200]
        console.print(f"\n  [bold]Script (início):[/bold] {snippet}{'...' if len(brief.script) > 200 else ''}")

    if brief.tool_suggestions:
        console.print(f"\n  [bold]Ferramentas:[/bold] {', '.join(brief.tool_suggestions)}")


@creative_app.command("export-package")
def cmd_export_package(
    brief_id: str = typer.Option(..., "--brief-id", "-b", help="ID do creative brief"),
    no_html: bool = typer.Option(False, "--no-html", help="Pular preview.html"),
    no_image: bool = typer.Option(False, "--no-image", help="Pular mock_image.png"),
):
    """Gera pacote de exportação (até 13 artefatos)."""
    result = generate_export_package(
        brief_id,
        include_html=not no_html,
        include_mock_image=not no_image,
    )
    if not result:
        console.print(f"[red]Brief '{brief_id}' não encontrado.[/red]")
        raise typer.Exit(1)

    console.print(f"[green]Package gerado:[/green] {result.package_id}")
    console.print(f"  Diretório: {result.package_path}")
    console.print(f"  Arquivos ({len(result.files_generated)}):")
    for f in result.files_generated:
        console.print(f"    - {f}")

    if result.warnings:
        console.print(f"\n[yellow]Warnings ({len(result.warnings)}):[/yellow]")
        for w in result.warnings:
            console.print(f"  ⚠ {w}")
    else:
        console.print(f"\n[green]✓ Nenhum warning — todos os campos preenchidos.[/green]")
