"""CLI commands para First Post Preflight — P1.3a."""
from __future__ import annotations

import json
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.first_post import get_preflight, PreflightStatus, PostPackage
from src.first_post.package import PostPackager

post_app = typer.Typer(
    name="post",
    help="First Post Preflight — validacao sem publicar nada",
    add_completion=False,
)
console = Console()


def _status_style(status: str) -> str:
    return {
        PreflightStatus.READY: "[green]",
        PreflightStatus.BLOCKED: "[red]",
        PreflightStatus.PARTIAL: "[yellow]",
        PreflightStatus.EMPTY: "[dim]",
        PreflightStatus.FAILED: "[red]",
    }.get(status, "")


def _check_icon(passed: bool) -> str:
    return "[green]PASS[/green]" if passed else "[red]FAIL[/red]"


@post_app.command(name="preflight")
def post_preflight(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Executa 8 checks de preflight antes de publicar.

    Nao publica nada. Verifica se queue, assets, captions, e sistema
    estao prontos para publicacao. Reporta itens prontos.
    """
    pf = get_preflight()
    report = pf.run()

    if json_output:
        print(report.model_dump_json(indent=2))
        return

    console.print(Panel(
        f"[bold]First Post — Preflight[/bold]\n"
        f"Status: {_status_style(report.overall_status)}{report.overall_status}[/]  |  "
        f"Itens prontos: {report.ready_items}",
        title="P1.3a"
    ))

    table = Table(title=f"Checks — {report.passed}/{report.total_checks} passaram")
    table.add_column("Check", style="cyan")
    table.add_column("Resultado")
    table.add_column("Requerido")
    table.add_column("Detalhe")

    for c in report.checks:
        req = "[bold]sim[/bold]" if c.required else "nao"
        table.add_row(c.label, _check_icon(c.passed), req, c.detail[:60])
    console.print(table)

    # Diagnostico
    console.print(f"\n[bold]Diagnostico:[/bold]")

    failed_required = [c for c in report.checks if not c.passed and c.required]
    failed_optional = [c for c in report.checks if not c.passed and not c.required]

    if failed_required:
        console.print(f"  [red]Bloqueios ({len(failed_required)}):[/red]")
        for c in failed_required:
            console.print(f"    - {c.label}: {c.recommendation}")

    if failed_optional:
        console.print(f"  [yellow]Avisos ({len(failed_optional)}):[/yellow]")
        for c in failed_optional:
            console.print(f"    - {c.label}: {c.recommendation}")

    if report.ready_items > 0:
        console.print(f"  [green]{report.ready_items} item(ns) pronto(s) para revisao humana[/green]")

    if not failed_required and not failed_optional:
        console.print(f"  [green]Todos os checks passaram[/green]")

    console.print(f"\n[bold]Proximo passo:[/bold] {report.next_action}")
    console.print(f"[bold]Itens prontos para publicar:[/bold] {report.ready_items}")

    if report.ready_items > 0:
        console.print(f"\n[dim]Use 'omnis post package' para ver detalhes do conteudo.[/dim]")


@post_app.command(name="package")
def post_package(
    queue_id: Optional[str] = typer.Argument(None, help="Queue ID especifico (vazio = proximo pronto)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Empacota conteudo pronto para revisao (nunca publica).

    Sem argumentos, empacota o primeiro item pronto da fila.
    Com queue_id, empacota slot especifico.
    """
    packager = PostPackager()

    if queue_id:
        pkg = packager.package_draft(queue_id)
    else:
        pkg = packager.package_next_ready()

    if pkg is None:
        console.print("[red]Nao foi possivel empacotar o conteudo.[/red]")
        if queue_id:
            console.print(f"  Queue ID: {queue_id[:8]}")
        raise typer.Exit(1)

    if json_output:
        print(pkg.model_dump_json(indent=2))
        return

    status_icon = "[green]READY[/green]" if pkg.ready else "[yellow]WARNINGS[/yellow]"
    console.print(Panel(
        f"[bold]Pacote de Publicacao[/bold]  {status_icon}\n\n"
        f"Queue ID:    {pkg.queue_id[:8]}\n"
        f"Conta:       @{pkg.account_handle}\n"
        f"Formato:     {pkg.format}\n"
        f"Asset:       {pkg.asset_id[:8] if pkg.asset_id else '(sem asset)'}\n"
        f"CTA:         {pkg.cta or '(nao definido)'}\n"
        f"Hashtags:    {', '.join(pkg.hashtags) if pkg.hashtags else '(nenhuma)'}",
        title="P1.3a"
    ))

    if pkg.caption_text:
        console.print(Panel(pkg.caption_text, title="Legenda"))
    else:
        console.print("[dim](sem legenda)[/dim]")

    if pkg.warnings:
        console.print(f"\n[yellow]Avisos ({len(pkg.warnings)}):[/yellow]")
        for w in pkg.warnings:
            console.print(f"  [yellow]![/yellow] {w}")

    if pkg.ready:
        console.print(f"\n[green]Pacote pronto para revisao humana.[/green]")
        console.print(f"[yellow]AVISO:[/yellow] Publicacao real bloqueada ate autorizacao de Lucas.")
    else:
        console.print(f"\n[yellow]Pacote NAO esta pronto para publicar.[/yellow]")


@post_app.command(name="status")
def post_status(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Status rapido: quantos itens prontos para publicar."""
    pf = get_preflight()
    report = pf.run()

    if json_output:
        print(json.dumps({
            "overall_status": report.overall_status,
            "ready_items": report.ready_items,
            "can_publish": report.can_publish,
            "next_action": report.next_action,
            "checked_at": report.checked_at,
        }, indent=2, ensure_ascii=False))
        return

    style = _status_style(report.overall_status)
    console.print(f"First Post Status: {style}{report.overall_status}[/]")
    console.print(f"  Itens prontos: {report.ready_items}")
    console.print(f"  Pode publicar: {'[green]Sim[/green]' if report.can_publish else '[red]Não[/red]'}")
    console.print(f"  Próximo: {report.next_action}")
