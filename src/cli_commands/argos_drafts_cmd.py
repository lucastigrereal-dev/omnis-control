"""CLI commands for Argos Draft Bridge (Fase 2E)."""

import json
import os
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from src.argos_bridge.draft_builder import DraftBuilder, list_all, get_by_id, stats
from src.argos_bridge.exporter import export_csv, export_json
from src.content_queue import Queue as CQQueue
from src.caption_approval import DraftsManager

argos_app = typer.Typer(
    name="argos-drafts",
    help="Gerencia drafts de publicação (bridge Caption → Publisher OS)",
    add_completion=False,
)
console = Console()

# ── Helpers ─────────────────────────────────────────────

def _get_queue_provider():
    q = CQQueue()
    return q.get

def _get_caption_provider():
    dm = DraftsManager()
    # Find approved caption by queue_id
    def find_by_queue(queue_id):
        drafts = dm.list_all()
        for d in drafts:
            if d.queue_id == queue_id and d.status == "approved":
                return d
        # Fallback: any caption for this queue_id
        for d in drafts:
            if d.queue_id == queue_id:
                return d
        return None
    return find_by_queue


# ── Commands ────────────────────────────────────────────

@argos_app.command("create")
def cmd_create(
    queue_id: str = typer.Argument(..., help="ID do queue item"),
):
    """Cria um ArgosDraft a partir de um queue item com caption aprovado."""
    builder = DraftBuilder(
        queue_provider=_get_queue_provider(),
        caption_provider=_get_caption_provider(),
    )
    draft, errors = builder.create(queue_id)
    if errors:
        console.print("[red]ERRO:[/red]")
        for e in errors:
            console.print(f"  - {e}")
        raise typer.Exit(1)
    console.print(f"[green]ArgosDraft criado:[/green] {draft.draft_id}")
    console.print(f"  Queue: {draft.queue_id}")
    console.print(f"  Conta: @{draft.account_handle}")
    console.print(f"  Status: {draft.status}")
    if draft.warnings:
        console.print(f"  [yellow]Warnings: {', '.join(draft.warnings)}[/yellow]")


@argos_app.command("list")
def cmd_list():
    """Lista todos os ArgosDrafts."""
    drafts = list_all()
    if not drafts:
        console.print("[yellow]Nenhum ArgosDraft encontrado.[/yellow]")
        return
    table = Table(title=f"ArgosDrafts ({len(drafts)})")
    table.add_column("ID", style="cyan")
    table.add_column("Queue", style="dim")
    table.add_column("Conta")
    table.add_column("Status")
    table.add_column("Warnings")
    for d in drafts:
        warns = ", ".join(d.warnings) if d.warnings else ""
        table.add_row(d.draft_id[:8], d.queue_id[:8], f"@{d.account_handle}", d.status, warns)
    console.print(table)


@argos_app.command("show")
def cmd_show(
    draft_id: str = typer.Argument(..., help="ID do ArgosDraft"),
):
    """Mostra detalhes de um ArgosDraft."""
    draft = get_by_id(draft_id)
    if not draft:
        console.print(f"[red]ArgosDraft '{draft_id}' não encontrado.[/red]")
        raise typer.Exit(1)
    console.print(f"[bold]ArgosDraft:[/bold] {draft.draft_id}")
    console.print(f"  Queue ID: {draft.queue_id}")
    console.print(f"  Caption Draft ID: {draft.caption_draft_id}")
    console.print(f"  Conta: @{draft.account_handle}")
    console.print(f"  Status: {draft.status}")
    console.print(f"  Post Type: {draft.post_type}")
    console.print(f"  Data: {draft.scheduled_date} {draft.scheduled_time or ''}")
    console.print(f"  Asset ID: {draft.asset_id or '(sem asset)'}")
    if draft.warnings:
        console.print(f"  [yellow]Warnings: {', '.join(draft.warnings)}[/yellow]")
    console.print(f"\n  [bold]Caption:[/bold]")
    console.print(f"  {draft.caption_text[:200]}{'...' if len(draft.caption_text) > 200 else ''}")
    if draft.hashtags:
        console.print(f"\n  [bold]Hashtags:[/bold] {' '.join(draft.hashtags)}")
    if draft.cta:
        console.print(f"\n  [bold]CTA:[/bold] {draft.cta}")
    if draft.notes:
        console.print(f"\n  Notes: {draft.notes}")


@argos_app.command("export")
def cmd_export(
    format: str = typer.Option("csv", "--format", "-f", help="Formato: csv ou json"),
):
    """Exporta ArgosDrafts para CSV ou JSON."""
    drafts = list_all()
    if not drafts:
        console.print("[yellow]Nenhum ArgosDraft para exportar.[/yellow]")
        return
    if format == "csv":
        path = export_csv(drafts)
    elif format == "json":
        path = export_json(drafts)
    else:
        console.print(f"[red]Formato não suportado: {format}[/red]")
        raise typer.Exit(1)
    console.print(f"[green]Exportado {len(drafts)} draft(s) para:[/green] {path}")


@argos_app.command("stats")
def cmd_stats():
    """Estatísticas dos ArgosDrafts."""
    s = stats()
    console.print(f"[bold]ArgosDrafts Stats[/bold]")
    console.print(f"  Total: {s['total']}")
    if s['by_status']:
        console.print("  Por status:")
        for st, count in sorted(s['by_status'].items()):
            console.print(f"    - {st}: {count}")
    if s['by_account']:
        console.print("  Por conta:")
        for ac, count in sorted(s['by_account'].items()):
            console.print(f"    - @{ac}: {count}")
    console.print(f"  Com warnings: {s['with_warnings']}")
