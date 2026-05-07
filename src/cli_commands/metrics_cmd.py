"""CLI commands para Metrics Spine — P0.9."""
from __future__ import annotations

import json
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.metrics import get_recorder, MetricsRecorder

metrics_app = typer.Typer(
    name="metrics",
    help="Metrics Spine — metricas de execucao, ferramentas e pipelines",
    add_completion=False,
)
console = Console()


def _recorder() -> MetricsRecorder:
    return get_recorder()


def _status_style(status: str) -> str:
    return {
        "success": "[green]",
        "failed": "[red]",
        "blocked": "[yellow]",
        "running": "[blue]",
        "paused": "[dim]",
    }.get(status, "")


def _status_label(status: str) -> str:
    style = _status_style(status)
    return f"{style}{status}[/]"


# ── Commands ──────────────────────────────────────────────────────────


@metrics_app.command(name="status")
def metrics_status(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Resumo geral da Metrics Spine hoje."""
    rec = _recorder()
    summary = rec.summarize_today()

    if json_output:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return

    if summary["total"] == 0:
        console.print("[dim]Metrics Spine — sem runs hoje.[/dim]")
        return

    console.print(f"[bold]Metrics Spine — Hoje[/bold]\n")

    console.print(f"  Total runs:     {summary['total']}")
    console.print(f"  Concluidas:     [green]{summary['succeeded']}[/green]")
    console.print(f"  Falhadas:       [red]{summary['failed']}[/red]")
    console.print(f"  Bloqueadas:     [yellow]{summary['blocked']}[/yellow]")
    if summary["running"] > 0:
        console.print(f"  Em execucao:    [blue]{summary['running']}[/blue]")
    console.print(f"  Ferramentas:    {summary['unique_tools_used']} distintas")
    console.print(f"  Avg duracao:    {summary.get('avg_duration_ms', 0):.0f}ms")
    console.print(f"  Total tokens:   {summary.get('total_tokens', 0)}")
    console.print(f"  Total custo:    ${summary.get('total_cost_usd', 0):.4f}")

    if summary.get("tools_list"):
        console.print(f"\n  Ferramentas usadas: {', '.join(summary['tools_list'])}")


@metrics_app.command(name="today")
def metrics_today(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Detalhe das runs de hoje."""
    rec = _recorder()
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    runs = rec.store.get_runs(limit=0)
    today_runs = [r for r in runs if r.started_at.startswith(today)]

    if json_output:
        print(json.dumps([r.model_dump() for r in today_runs], indent=2, ensure_ascii=False))
        return

    if not today_runs:
        console.print("[dim]Nenhuma run hoje.[/dim]")
        return

    table = Table(title=f"Runs de hoje — {len(today_runs)}")
    table.add_column("Run ID", style="cyan", no_wrap=True)
    table.add_column("Mission", no_wrap=True)
    table.add_column("Status")
    table.add_column("Duracao")
    table.add_column("Tools")
    table.add_column("Tokens")

    for r in today_runs:
        table.add_row(
            r.run_id,
            r.mission_id[:12] + "..." if len(r.mission_id) > 12 else r.mission_id or "-",
            _status_label(r.status),
            f"{r.duration_ms:.0f}ms",
            str(len(r.tools_used)),
            str(r.total_tokens),
        )
    console.print(table)


@metrics_app.command(name="mission")
def metrics_mission(
    mission_id: str = typer.Argument(..., help="Mission ID (completo ou prefixo)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Metricas detalhadas de uma missao especifica."""
    rec = _recorder()

    # Try exact match first, then prefix match
    runs = rec.store.get_runs(limit=0)
    matching = [r for r in runs if r.mission_id == mission_id or r.mission_id.startswith(mission_id)]

    if not matching:
        console.print(f"[red]Nenhuma run encontrada para mission '{mission_id}'.[/red]")
        raise typer.Exit(1)

    summary = rec.summarize_mission(matching[0].mission_id)

    if json_output:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return

    stats = summary["run_stats"]
    by_type = summary["by_event_type"]
    by_tool = summary["by_tool"]

    console.print(f"[bold]Mission: {matching[0].mission_id}[/bold]")
    console.print(f"  Total events: {summary['total_events']}")
    console.print(f"  Total runs:   {summary['total_runs']}")
    console.print(f"  Succeeded:    [green]{stats['succeeded']}[/green]")
    console.print(f"  Failed:       [red]{stats['failed']}[/red]")
    console.print(f"  Avg duracao:  {stats.get('avg_duration_ms', 0):.0f}ms")

    if by_type:
        console.print(f"\n[bold]Por tipo de evento:[/bold]")
        for et, data in by_type.items():
            console.print(f"  {et}: {data['count']} eventos, avg={data['avg_value']:.2f}")

    if by_tool:
        console.print(f"\n[bold]Ferramentas usadas:[/bold]")
        for tid, data in by_tool.items():
            console.print(f"  {tid}: {data['count']} usos, last={data.get('last_used', '?')[:10]}")


@metrics_app.command(name="tools")
def metrics_tools(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Metricas de uso de ferramentas."""
    rec = _recorder()
    summary = rec.summarize_tools()

    if json_output:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return

    by_tool = summary["by_tool"]
    if not by_tool:
        console.print("[dim]Nenhuma metrica de ferramenta registrada.[/dim]")
        return

    console.print(f"[bold]Uso de Ferramentas[/bold] — {summary['unique_tools']} distintas\n")

    table = Table()
    table.add_column("Tool ID", style="cyan")
    table.add_column("Usos", justify="right")
    table.add_column("Primeiro uso")
    table.add_column("Ultimo uso")
    table.add_column("Status breakdown")

    for tid, data in sorted(by_tool.items(), key=lambda x: x[1]["count"], reverse=True):
        if tid == "__no_tool__":
            continue
        status_str = ", ".join(f"{s}:{c}" for s, c in data.get("by_status", {}).items())
        table.add_row(
            tid,
            str(data["count"]),
            data.get("first_used", "")[:10],
            data.get("last_used", "")[:10],
            status_str or "-",
        )
    console.print(table)


@metrics_app.command(name="export")
def metrics_export(
    fmt: str = typer.Option("json", "--format", help="Formato: json ou csv"),
) -> None:
    """Exporta dados da Metrics Spine."""
    rec = _recorder()
    metrics = rec.store.get_metrics(limit=0)
    runs = rec.store.get_runs(limit=0)

    if fmt == "csv":
        import csv
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["type", "id", "mission_id", "run_id", "tool_id", "name", "value", "status", "timestamp"])
        for m in metrics:
            writer.writerow(["metric", m.metric_id, m.mission_id, m.run_id, m.tool_id, m.name, m.value, m.status, m.timestamp])
        for r in runs:
            writer.writerow(["run", r.run_id, r.mission_id, "", "", "", "", r.status, r.started_at])
        print(output.getvalue())
    else:
        data = {
            "total_metrics": len(metrics),
            "total_runs": len(runs),
            "metrics": [m.model_dump() for m in metrics],
            "runs": [r.model_dump() for r in runs],
        }
        print(json.dumps(data, indent=2, ensure_ascii=False))
