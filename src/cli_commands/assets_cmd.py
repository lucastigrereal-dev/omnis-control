"""CLI commands para Asset Assignment Center — P1.9."""
from __future__ import annotations

import json
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.asset_assignment import check_assignment_status, add_mock_asset, list_ready_candidates

assets_app = typer.Typer(
    name="assets",
    help="Asset Assignment Center — vincula assets a slots da fila. NUNCA publica.",
    add_completion=False,
)
console = Console()


@assets_app.command(name="assignment-status")
def cmd_assignment_status(
    queue_id: str = typer.Argument(..., help="Queue ID (prefixo aceito)"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
) -> None:
    """Verifica estado de assignment de um slot da fila.

    Mostra: asset atribuido, caption aprovada, se pacote pode ser READY.
    NUNCA chama Meta. NUNCA publica.
    """
    result = check_assignment_status(queue_id)

    if json_output:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        return

    ready_style = "[green]SIM[/green]" if result.ready_for_package else "[yellow]NAO[/yellow]"
    asset_display = result.asset_id or "[dim](nenhum)[/dim]"
    caption_display = result.caption_id or "[dim](nenhuma aprovada)[/dim]"

    console.print(Panel(
        f"[bold]Queue: {result.queue_id}[/bold]\n\n"
        f"Conta:          @{result.account_handle}\n"
        f"Status atual:   {result.previous_status}\n"
        f"Asset ID:       {asset_display}\n"
        f"Caption ID:     {caption_display}\n"
        f"Asset em disco: {'[green]SIM[/green]' if result.asset_exists_on_disk else '[dim]NAO[/dim]'}\n"
        f"Pronto p/ pkg:  {ready_style}",
        title="P1.9 — Asset Assignment Status"
    ))

    if result.blockers:
        console.print(f"\n[red]Blockers ({len(result.blockers)}):[/red]")
        for b in result.blockers:
            console.print(f"  [red]![/red] {b}")

    if result.warnings:
        console.print(f"\n[yellow]Warnings ({len(result.warnings)}):[/yellow]")
        for w in result.warnings:
            console.print(f"  [yellow]![/yellow] {w}")

    if result.next_actions:
        console.print(f"\n[bold]Next actions:[/bold]")
        for a in result.next_actions:
            console.print(f"  -> {a}")


@assets_app.command(name="add-mock")
def cmd_add_mock(
    name: str = typer.Argument(..., help="Nome do asset mock (ex: natal_video_01.mp4)"),
    queue_id: str = typer.Option("", "--queue", help="Atribuir imediatamente a este queue_id"),
    format: str = typer.Option("carousel", "--format", help="Formato: carousel|reel|static|story"),
    account: str = typer.Option("", "--account", help="Account handle alvo"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
) -> None:
    """Registra um asset mock local para testes de packaging offline.

    Cria entrada no registry de video_assets sem precisar de arquivo real.
    Util para testar o fluxo completo: asset -> pacote READY -> validate -> zip.
    NUNCA chama Meta. NUNCA publica.
    """
    result = add_mock_asset(
        name=name,
        queue_id=queue_id or None,
        format=format,
        account_handle=account,
    )

    if json_output:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    assigned_str = f"@{result['assigned_to_queue']}" if result.get("assigned_to_queue") else "[dim](nao atribuido)[/dim]"
    console.print(Panel(
        f"[bold]Asset Mock Registrado[/bold]  [green]OK[/green]\n\n"
        f"Asset ID:    {result['asset_id']}\n"
        f"Nome:        {result['name']}\n"
        f"Formato:     {result['format']}\n"
        f"Atribuido:   {assigned_str}",
        title="P1.9 — Add Mock Asset"
    ))

    if result.get("warning"):
        console.print(f"\n[yellow]Warning:[/yellow] {result['warning']}")
    if result.get("assign_error"):
        console.print(f"\n[red]Erro ao atribuir ao slot:[/red] {result['assign_error']}")

    if result.get("assigned_to_queue"):
        console.print(f"\n[bold]Proximo passo:[/bold]")
        console.print(f"  -> python jarvis.py offline package-carousel {result['assigned_to_queue']}")


@assets_app.command(name="ready-candidates")
def cmd_ready_candidates(
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
) -> None:
    """Lista slots da fila com caption aprovada e/ou asset atribuido.

    Mostra quais slots estao prontos para gerar pacote READY.
    """
    candidates = list_ready_candidates()

    if json_output:
        print(json.dumps(candidates, indent=2, ensure_ascii=False))
        return

    if not candidates:
        console.print("[dim]Nenhum candidato encontrado. Use 'assets add-mock' para criar um.[/dim]")
        return

    table = Table(title=f"Candidatos para Package ({len(candidates)})")
    table.add_column("Queue ID", style="cyan")
    table.add_column("Conta")
    table.add_column("Data")
    table.add_column("Status")
    table.add_column("Asset")
    table.add_column("Caption")
    table.add_column("Pronto?")

    for c in candidates:
        ready = "[green]SIM[/green]" if c["ready_for_package"] else "[yellow]parcial[/yellow]"
        has_asset = "[green]sim[/green]" if c["has_asset"] else "[dim]nao[/dim]"
        has_caption = "[green]sim[/green]" if c["has_caption"] else "[dim]nao[/dim]"
        table.add_row(
            c["queue_id"][:12],
            f"@{c['account_handle']}",
            c["date"],
            c["status"],
            has_asset,
            has_caption,
            ready,
        )

    console.print(table)
