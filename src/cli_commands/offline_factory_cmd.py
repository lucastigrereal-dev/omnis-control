"""CLI commands para Offline Delivery Factory — P1.7."""
from __future__ import annotations

import json
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.offline_factory import (
    create_carousel_package,
    create_reels_script_package,
    list_packages,
)
from src.offline_factory.packager import EXPORT_ROOT

offline_app = typer.Typer(
    name="offline",
    help="Offline Delivery Factory — gera pacotes de conteudo locais. NUNCA publica.",
    add_completion=False,
)
console = Console()


def _status_style(status: str) -> str:
    return {
        "ready": "[green]",
        "partial": "[yellow]",
        "blocked": "[red]",
        "draft": "[dim]",
        "exported": "[blue]",
    }.get(status, "")


@offline_app.command(name="package-carousel")
def package_carousel(
    queue_id: str = typer.Argument(..., help="Queue ID (ex: 0b79aa1c)"),
    slides: int = typer.Option(5, "--slides", help="Numero de slides"),
    account: str = typer.Option("", "--account", help="Override do account handle"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
) -> None:
    """Gera pacote de carrossel local para um item da fila.

    NUNCA chama Meta. NUNCA publica. NUNCA agenda.
    Cria arquivos locais em exports/offline_factory/<package_id>/
    """
    try:
        pkg = create_carousel_package(queue_id, num_slides=slides, account_handle=account)
    except Exception as e:
        console.print(f"[red]Erro ao criar pacote:[/red] {e}")
        raise typer.Exit(1)

    if json_output:
        print(pkg.model_dump_json(indent=2))
        return

    style = _status_style(pkg.status.value)
    console.print(Panel(
        f"[bold]Pacote Carrossel[/bold]  {style}{pkg.status.value}[/]\n\n"
        f"Package ID:  {pkg.package_id}\n"
        f"Queue ID:    {pkg.source_queue_id}\n"
        f"Conta:       @{pkg.account_handle}\n"
        f"Slides:      {slides}\n"
        f"Arquivos:    {len(pkg.files)}\n"
        f"Destino:     {pkg.output_dir}",
        title="P1.7 — Offline Factory"
    ))

    if pkg.blockers:
        console.print(f"\n[red]Blockers ({len(pkg.blockers)}):[/red]")
        for b in pkg.blockers:
            console.print(f"  [red]![/red] {b}")

    if pkg.warnings:
        console.print(f"\n[yellow]Warnings ({len(pkg.warnings)}):[/yellow]")
        for w in pkg.warnings:
            console.print(f"  [yellow]![/yellow] {w}")

    if pkg.next_actions:
        console.print(f"\n[bold]Next actions:[/bold]")
        for a in pkg.next_actions:
            console.print(f"  → {a}")

    console.print(f"\n[dim]Manifesto: {pkg.manifest_path}[/dim]")


@offline_app.command(name="package-reels")
def package_reels(
    queue_id: str = typer.Argument(..., help="Queue ID (ex: 0b79aa1c)"),
    account: str = typer.Option("", "--account", help="Override do account handle"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
) -> None:
    """Gera pacote de script/Reels local para um item da fila.

    NUNCA chama Meta. NUNCA publica. NUNCA agenda.
    Cria arquivos locais em exports/offline_factory/<package_id>/
    """
    try:
        pkg = create_reels_script_package(queue_id, account_handle=account)
    except Exception as e:
        console.print(f"[red]Erro ao criar pacote:[/red] {e}")
        raise typer.Exit(1)

    if json_output:
        print(pkg.model_dump_json(indent=2))
        return

    style = _status_style(pkg.status.value)
    console.print(Panel(
        f"[bold]Pacote Reels Script[/bold]  {style}{pkg.status.value}[/]\n\n"
        f"Package ID:  {pkg.package_id}\n"
        f"Queue ID:    {pkg.source_queue_id}\n"
        f"Conta:       @{pkg.account_handle}\n"
        f"Arquivos:    {len(pkg.files)}\n"
        f"Destino:     {pkg.output_dir}",
        title="P1.7 — Offline Factory"
    ))

    if pkg.blockers:
        console.print(f"\n[red]Blockers ({len(pkg.blockers)}):[/red]")
        for b in pkg.blockers:
            console.print(f"  [red]![/red] {b}")

    if pkg.warnings:
        console.print(f"\n[yellow]Warnings ({len(pkg.warnings)}):[/yellow]")
        for w in pkg.warnings:
            console.print(f"  [yellow]![/yellow] {w}")

    if pkg.next_actions:
        console.print(f"\n[bold]Next actions:[/bold]")
        for a in pkg.next_actions:
            console.print(f"  → {a}")

    console.print(f"\n[dim]Manifesto: {pkg.manifest_path}[/dim]")


@offline_app.command(name="list")
def offline_list(
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
) -> None:
    """Lista pacotes offline gerados em exports/offline_factory/."""
    packages = list_packages()

    if json_output:
        print(json.dumps(packages, indent=2, ensure_ascii=False))
        return

    if not packages:
        console.print(f"Nenhum pacote em {EXPORT_ROOT}")
        return

    table = Table(title=f"Pacotes Offline ({len(packages)})")
    table.add_column("Package ID", style="cyan", no_wrap=True)
    table.add_column("Tipo")
    table.add_column("Conta")
    table.add_column("Status")
    table.add_column("Arquivos")
    table.add_column("Gerado em")

    for p in packages:
        status = p.get("status", "?")
        style = _status_style(status)
        files_count = len(p.get("files", []))
        table.add_row(
            p.get("package_id", "?")[:30],
            p.get("package_type", "?"),
            f"@{p.get('account_handle', '?')}",
            f"{style}{status}[/]",
            str(files_count),
            p.get("generated_at", "?")[:16],
        )
    console.print(table)


@offline_app.command(name="show")
def offline_show(
    package_id: str = typer.Argument(..., help="Package ID (prefixo aceito)"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
) -> None:
    """Mostra detalhes de um pacote offline."""
    packages = list_packages()
    match = [p for p in packages if p.get("package_id", "").startswith(package_id)]

    if not match:
        console.print(f"[red]Pacote '{package_id}' nao encontrado.[/red]")
        raise typer.Exit(1)

    p = match[0]

    if json_output:
        print(json.dumps(p, indent=2, ensure_ascii=False))
        return

    status = p.get("status", "?")
    style = _status_style(status)
    console.print(Panel(
        f"[bold]{p.get('title', p.get('package_id', '?'))}[/bold]\n\n"
        f"Package ID:    {p.get('package_id', '?')}\n"
        f"Tipo:          {p.get('package_type', '?')}\n"
        f"Conta:         @{p.get('account_handle', '?')}\n"
        f"Queue ID:      {p.get('source_queue_id', '?')}\n"
        f"Caption ID:    {p.get('source_caption_id', '(nenhuma)')}\n"
        f"Status:        {style}{status}[/]\n"
        f"Gerado em:     {p.get('generated_at', '?')}",
        title="Pacote Offline"
    ))

    files = p.get("files", [])
    if files:
        console.print(f"\n[bold]Arquivos ({len(files)}):[/bold]")
        for f in files:
            name = f.get("name", "?") if isinstance(f, dict) else str(f)
            size = f.get("size_bytes", 0) if isinstance(f, dict) else 0
            console.print(f"  {name:<30} {size:>8} bytes")

    blockers = p.get("blockers", [])
    if blockers:
        console.print(f"\n[red]Blockers ({len(blockers)}):[/red]")
        for b in blockers:
            console.print(f"  [red]![/red] {b}")

    warnings = p.get("warnings", [])
    if warnings:
        console.print(f"\n[yellow]Warnings ({len(warnings)}):[/yellow]")
        for w in warnings:
            console.print(f"  [yellow]![/yellow] {w}")

    next_actions = p.get("next_actions", [])
    if next_actions:
        console.print(f"\n[bold]Next actions:[/bold]")
        for a in next_actions:
            console.print(f"  → {a}")
