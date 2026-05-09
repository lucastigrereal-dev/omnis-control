"""CLI for Mission Report — close + report mission package. NUNCA publica."""
from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

mission_report_app = typer.Typer(
    name="mission-report",
    help="Mission Report — fechar missao e registrar resultado. NUNCA publica.",
    add_completion=False,
)
console = Console()


@mission_report_app.callback()
def _callback():
    """Mission Report — fecha missao e gera relatorio de encerramento."""


@mission_report_app.command(name="close")
def cmd_close(
    mission_id: str = typer.Argument(..., help="ID da missao (ex: mb_abc12345)"),
    outcome: str = typer.Option("completed", "--outcome", help="completed | cancelled | deferred"),
    notes: str = typer.Option("", "--notes", help="Notas de encerramento"),
    url: str = typer.Option("", "--url", help="URL publicado (se houver)"),
    json_out: bool = typer.Option(False, "--json", help="Saida em JSON"),
) -> None:
    """Fecha uma missao e gera relatorio 07_mission_report.md no pacote."""
    from src.mission_report import service as svc
    from src.mission_report.errors import (
        MissionNotFoundError,
        InvalidOutcomeError,
        MissionReportError,
    )

    try:
        report = svc.close_mission(
            mission_id=mission_id,
            outcome=outcome,
            notes=notes,
            published_url=url,
            packages_root=svc.PACKAGES_ROOT,
            reports_log=svc.REPORTS_LOG,
        )
    except InvalidOutcomeError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)
    except MissionNotFoundError as exc:
        console.print(f"[red]Missao nao encontrada: {exc}[/red]")
        raise typer.Exit(1)
    except MissionReportError as exc:
        console.print(f"[red]Falha ao gerar relatorio: {exc}[/red]")
        raise typer.Exit(1)

    if json_out:
        console.print_json(json.dumps(report.to_dict(), ensure_ascii=False))
        return

    outcome_color = {"completed": "green", "cancelled": "yellow", "deferred": "dim"}.get(
        outcome, "white"
    )
    console.print(Panel(f"[bold]Mission Closed[/bold] — {mission_id}", expand=False))
    console.print(f"  Report ID : {report.report_id}")
    console.print(f"  Outcome   : [{outcome_color}]{report.outcome}[/{outcome_color}]")
    console.print(f"  Conta     : @{report.account_handle}")
    console.print(f"  Fechado   : {report.closed_at}")
    if report.published_url:
        console.print(f"  URL       : {report.published_url}")
    console.print(f"\n  [dim]Relatorio em: exports/mission_packages/{mission_id}/07_mission_report.md[/dim]")


@mission_report_app.command(name="list")
def cmd_list(
    limit: int = typer.Option(10, "--limit", help="Numero maximo de relatorios"),
    json_out: bool = typer.Option(False, "--json", help="Saida em JSON"),
) -> None:
    """Lista missoes encerradas."""
    from src.mission_report import service as svc

    reports = svc.list_reports(reports_log=svc.REPORTS_LOG)[:limit]

    if json_out:
        console.print_json(json.dumps([r.to_dict() for r in reports], ensure_ascii=False))
        return

    if not reports:
        console.print("[dim]Nenhuma missao encerrada ainda.[/dim]")
        return

    table = Table(title="Mission Reports")
    table.add_column("Report ID", style="dim")
    table.add_column("Mission ID")
    table.add_column("Intent")
    table.add_column("Conta")
    table.add_column("Outcome")
    table.add_column("Fechado em")
    for r in reports:
        color = {"completed": "green", "cancelled": "yellow", "deferred": "dim"}.get(r.outcome, "white")
        table.add_row(
            r.report_id,
            r.mission_id,
            r.intent,
            f"@{r.account_handle}",
            f"[{color}]{r.outcome}[/{color}]",
            r.closed_at[:10],
        )
    console.print(table)


@mission_report_app.command(name="get")
def cmd_get(
    mission_id: str = typer.Argument(..., help="ID da missao"),
    json_out: bool = typer.Option(False, "--json", help="Saida em JSON"),
) -> None:
    """Mostra o relatorio de uma missao especifica."""
    from src.mission_report import service as svc

    report = svc.get_report(mission_id, reports_log=svc.REPORTS_LOG)
    if report is None:
        console.print(f"[yellow]Nenhum relatorio encontrado para {mission_id}[/yellow]")
        raise typer.Exit(1)

    if json_out:
        console.print_json(json.dumps(report.to_dict(), ensure_ascii=False))
        return

    console.print(Panel(f"[bold]Report[/bold] — {report.report_id}", expand=False))
    console.print(f"  Mission   : {report.mission_id}")
    console.print(f"  Intent    : {report.intent}")
    console.print(f"  Outcome   : {report.outcome}")
    console.print(f"  Conta     : @{report.account_handle}")
    console.print(f"  Fechado   : {report.closed_at}")
    if report.notes:
        console.print(f"  Notas     : {report.notes[:80]}")
