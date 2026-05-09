"""Dashboard CLI — offline factory production summary. NUNCA publica."""
from __future__ import annotations

import json
import time

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

dashboard_app = typer.Typer(
    name="dashboard",
    help="Dashboard da Fábrica Offline — resumo de produção. NUNCA publica.",
    add_completion=False,
)
console = Console()


def _bar(current: int, target: int, width: int = 10) -> str:
    filled = round(width * current / target) if target > 0 else 0
    filled = min(filled, width)
    return "#" * filled + "-" * (width - filled)


def _render_dashboard(data: dict) -> None:
    pkg = data["packages"]
    qual = data["quality"]
    cam = data["campaigns"]
    oauth = data["oauth_gate"]

    console.print(Panel("[bold]Fábrica Offline — Dashboard[/bold]", expand=False))

    # Packages
    table = Table(title=f"Pacotes Offline ({pkg['total']} total)", show_header=True)
    table.add_column("Status")
    table.add_column("Qtd", justify="right")
    for status, count in sorted(pkg["by_status"].items()):
        style = {"ready": "green", "partial": "yellow", "blocked": "red",
                 "draft": "dim", "exported": "blue"}.get(status, "")
        table.add_row(f"[{style}]{status}[/{style}]" if style else status, str(count))
    console.print(table)

    # Renders + Quality
    avg = qual.get("avg_score")
    avg_str = f"{avg}/100" if avg is not None else "N/A"
    console.print(f"  Renders  : {data['renders']}")
    console.print(f"  Scores   : {qual['scored_count']} avaliados | média {avg_str}")

    # Campaigns
    cam_total = cam["total"]
    console.print(f"  Campanhas: {cam_total} total")
    for status, count in sorted(cam["by_status"].items()):
        console.print(f"    {status}: {count}")

    # Deliveries + Manual
    console.print(f"  Entregas : {data['deliveries']}")
    console.print(f"  Postados manualmente: {data['manual_published']}")

    # OAuth gate
    ready = oauth["ready"]
    target = oauth["target"]
    bar = _bar(ready, target)
    go_str = "[green]GO[/green]" if oauth["go"] else "[red]NO-GO[/red]"
    console.print(f"\n  OAuth Gate: [{bar}] {ready}/{target} READY — {go_str}")


@dashboard_app.command(name="offline")
def cmd_offline(
    json_out: bool = typer.Option(False, "--json", help="Saida em JSON"),
    watch: bool = typer.Option(False, "--watch", help="Atualiza a cada 30s (Ctrl+C para sair)"),
) -> None:
    """Mostra resumo da fábrica offline (pacotes, renders, qualidade, campanhas)."""
    from src.offline_dashboard.service import get_dashboard_data

    if watch:
        try:
            while True:
                console.clear()
                data = get_dashboard_data()
                if json_out:
                    console.print_json(json.dumps(data, ensure_ascii=False))
                else:
                    _render_dashboard(data)
                console.print("\n[dim]Atualizando em 30s — Ctrl+C para sair[/dim]")
                time.sleep(30)
        except KeyboardInterrupt:
            return

    data = get_dashboard_data()
    if json_out:
        console.print_json(json.dumps(data, ensure_ascii=False))
    else:
        _render_dashboard(data)


@dashboard_app.command(name="packages")
def cmd_packages(
    json_out: bool = typer.Option(False, "--json", help="Saida em JSON"),
) -> None:
    """Lista pacotes offline por status."""
    from src.offline_dashboard.service import get_dashboard_data

    data = get_dashboard_data()
    pkg = data["packages"]
    if json_out:
        console.print_json(json.dumps(pkg, ensure_ascii=False))
        return
    console.print(f"Pacotes: {pkg['total']} total")
    for status, count in sorted(pkg["by_status"].items()):
        console.print(f"  {status}: {count}")


@dashboard_app.command(name="campaigns")
def cmd_campaigns(
    json_out: bool = typer.Option(False, "--json", help="Saida em JSON"),
) -> None:
    """Lista campanhas por status."""
    from src.offline_dashboard.service import get_dashboard_data

    data = get_dashboard_data()
    cam = data["campaigns"]
    if json_out:
        console.print_json(json.dumps(cam, ensure_ascii=False))
        return
    console.print(f"Campanhas: {cam['total']} total")
    for status, count in sorted(cam["by_status"].items()):
        console.print(f"  {status}: {count}")


@dashboard_app.command(name="deliveries")
def cmd_deliveries(
    json_out: bool = typer.Option(False, "--json", help="Saida em JSON"),
) -> None:
    """Mostra contagem de entregas e registros de publicacao manual."""
    from src.offline_dashboard.service import get_dashboard_data

    data = get_dashboard_data()
    if json_out:
        console.print_json(json.dumps({
            "deliveries": data["deliveries"],
            "manual_published": data["manual_published"],
        }, ensure_ascii=False))
        return
    console.print(f"Entregas comerciais : {data['deliveries']}")
    console.print(f"Postados manualmente: {data['manual_published']}")
