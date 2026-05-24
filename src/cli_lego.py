"""CLI lego — inspeciona e aciona os Legos externos OMNIS.

Comandos:
    omnis lego list                   — lista legos + status de saúde
    omnis lego research <topic>       — pesquisa via ResearchConductorLego
    omnis lego send <message>         — despacha mensagem via ChannelMessengerLego
"""
from __future__ import annotations

import json
import os

import typer
from rich.console import Console
from rich.table import Table

from src.legos.registry import LegoRegistry, default_registry

lego_app = typer.Typer(name="lego", help="Legos OMNIS — capacidades externas")
console = Console()


def _get_registry() -> LegoRegistry:
    return default_registry()


# ── list ──────────────────────────────────────────────────────────────────────

@lego_app.command("list")
def list_legos(
    json_out: bool = typer.Option(False, "--json", help="Saída em JSON"),
) -> None:
    """Lista todos os legos registrados com status de saúde."""
    reg = _get_registry()
    health = reg.health_check_all()

    if json_out:
        payload = [
            {"name": name, "healthy": healthy}
            for name, healthy in sorted(health.items())
        ]
        console.print_json(json.dumps({"legos": payload, "total": len(payload)}))
        return

    table = Table(title="OMNIS Legos", show_header=True)
    table.add_column("Nome", style="cyan")
    table.add_column("Saúde", justify="center")

    for name in reg.list_available():
        healthy = health.get(name, False)
        status = "[green]OK[/green]" if healthy else "[yellow]não configurado[/yellow]"
        table.add_row(name, status)

    console.print(table)
    console.print(f"[dim]{len(reg)} lego(s) registrado(s)[/dim]")


# ── research ──────────────────────────────────────────────────────────────────

@lego_app.command("research")
def research(
    topic: str = typer.Argument(..., help="Tópico a pesquisar"),
    dry_run: bool = typer.Option(True, "--dry-run/--real", help="Simula sem chamar APIs"),
    perspectives: int = typer.Option(3, "--perspectives", "-p", help="Número de perspectivas"),
    json_out: bool = typer.Option(False, "--json", help="Saída em JSON"),
) -> None:
    """Pesquisa um tópico via ResearchConductorLego (STORM-adapted)."""
    from src.legos.research_conductor_lego import ResearchConductorLego
    from src.interfaces.research_conductor import ResearchSpec

    lego = ResearchConductorLego()
    spec = ResearchSpec(
        topic=topic,
        max_perspectives=perspectives,
        dry_run=dry_run,
    )

    if json_out:
        result = lego.execute(spec)
        console.print_json(json.dumps({
            "success": result.success,
            "topic": result.topic,
            "perspective_count": result.perspective_count,
            "citation_count": result.citation_count,
            "dry_run": result.dry_run,
            "error": result.error,
        }))
        return

    mode_label = "[dim]dry-run[/dim]" if dry_run else "[bold]real[/bold]"
    console.print(f"[cyan]Pesquisando:[/cyan] {topic!r} ({mode_label})")
    result = lego.execute(spec)

    if result.success:
        console.print(f"[green]OK[/green] — {result.perspective_count} perspectiva(s), "
                      f"{result.citation_count} citação(ões)")
        if result.report:
            console.print(result.report[:500] + ("…" if len(result.report) > 500 else ""))
    else:
        console.print(f"[red]Falhou:[/red] {result.error}")
        raise typer.Exit(1)


# ── send ──────────────────────────────────────────────────────────────────────

@lego_app.command("send")
def send(
    message: str = typer.Argument(..., help="Conteúdo da mensagem"),
    channel: str = typer.Option("all", "--channel", "-c",
                                help="Canal destino: all | whatsapp | telegram"),
    recipient: str = typer.Option("", "--to", "-t", help="Destinatário (telefone/chat_id)"),
    dry_run: bool = typer.Option(True, "--dry-run/--real", help="Simula sem chamar APIs"),
    json_out: bool = typer.Option(False, "--json", help="Saída em JSON"),
) -> None:
    """Despacha mensagem via ChannelMessengerLego (WhatsApp + Telegram)."""
    from src.legos.channel_messenger_lego import ChannelMessengerLego
    from src.interfaces.channel_messenger import MessageSpec

    lego = ChannelMessengerLego()
    spec = MessageSpec(
        content=message,
        channels=[channel],
        recipient=recipient,
        dry_run=dry_run,
    )
    result = lego.send(spec)

    if json_out:
        console.print_json(json.dumps({
            "success": result.success,
            "delivered": result.delivered_count,
            "failed": result.failed_count,
            "dry_run": result.dry_run,
            "error": result.error,
        }))
        return

    mode_label = "[dim]dry-run[/dim]" if dry_run else "[bold]real[/bold]"
    if result.success:
        console.print(f"[green]Enviado[/green] ({mode_label}) — "
                      f"{result.delivered_count} canal(is) entregue(s)")
    else:
        console.print(f"[red]Falhou[/red] ({mode_label}): {result.error}")
        raise typer.Exit(1)
