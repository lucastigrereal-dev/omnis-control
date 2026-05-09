"""CLI for Video Production Plan — P2.5. NUNCA publica."""
from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.table import Table

video_production_app = typer.Typer(
    name="video",
    help="Video Production Plan — agenda e rastreia producao de video. NUNCA publica.",
    add_completion=False,
)
console = Console()


@video_production_app.callback()
def _callback():
    """Video Production Plan — NUNCA publica."""


def _slot_style(status: str) -> str:
    return {"pending": "dim", "assigned": "yellow", "produced": "green", "skipped": "red"}.get(status, "")


@video_production_app.command(name="plan-create")
def cmd_plan_create(
    account: str = typer.Option(..., "--account", help="Handle Instagram (ex: afamiliatigrereal)"),
    format: str = typer.Option("reel", "--format", help="reel | carousel | static | story"),
    quantity: int = typer.Option(10, "--quantity", help="Numero de videos (1-100)"),
    days: int = typer.Option(30, "--days", help="Janela de producao em dias (1-365)"),
    json_out: bool = typer.Option(False, "--json", help="Saida em JSON"),
) -> None:
    """Cria um plano de producao de video para a proxima janela."""
    from src.video_production.service import create_plan, PlanValidationError

    try:
        plan = create_plan(account_handle=account, format=format, quantity=quantity, days_ahead=days)
    except PlanValidationError as exc:
        console.print(f"[red]Validacao: {exc}[/red]")
        raise typer.Exit(1)

    if json_out:
        console.print_json(json.dumps(plan.to_dict(), ensure_ascii=False))
        return

    console.print(f"[green]Plano criado[/green] — {plan.plan_id}")
    console.print(f"  Conta   : @{plan.account_handle}")
    console.print(f"  Formato : {plan.format}")
    console.print(f"  Slots   : {len(plan.slots)} ({plan.days_ahead} dias)")
    console.print(f"  Status  : {plan.status.value}")
    if plan.slots:
        console.print(f"  Primeiro slot: {plan.slots[0].date}")
        console.print(f"  Ultimo slot  : {plan.slots[-1].date}")


@video_production_app.command(name="plan-list")
def cmd_plan_list(
    account: str = typer.Option(None, "--account", help="Filtrar por conta"),
    status: str = typer.Option(None, "--status", help="draft | active | done | archived"),
    json_out: bool = typer.Option(False, "--json", help="Saida em JSON"),
) -> None:
    """Lista planos de producao de video."""
    from src.video_production.service import list_plans

    plans = list_plans(account_handle=account, status=status)

    if json_out:
        console.print_json(json.dumps([p.to_dict() for p in plans], ensure_ascii=False))
        return

    if not plans:
        console.print("[yellow]Nenhum plano encontrado.[/yellow]")
        return

    table = Table(title=f"Planos de Producao ({len(plans)})")
    table.add_column("ID", style="cyan")
    table.add_column("Conta")
    table.add_column("Formato")
    table.add_column("Slots")
    table.add_column("Pendentes", justify="right")
    table.add_column("Produzidos", justify="right")
    table.add_column("Status")

    for p in plans:
        table.add_row(
            p.plan_id[:12],
            f"@{p.account_handle}",
            p.format,
            str(len(p.slots)),
            str(p.pending_count()),
            str(p.produced_count()),
            p.status.value,
        )
    console.print(table)


@video_production_app.command(name="plan-show")
def cmd_plan_show(
    plan_id: str = typer.Argument(..., help="ID (ou prefixo) do plano"),
    json_out: bool = typer.Option(False, "--json", help="Saida em JSON"),
) -> None:
    """Mostra detalhes de um plano de producao."""
    from src.video_production.service import get_plan, PlanNotFoundError

    try:
        plan = get_plan(plan_id)
    except PlanNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)

    if json_out:
        console.print_json(json.dumps(plan.to_dict(), ensure_ascii=False))
        return

    console.print(f"[bold]Plano:[/bold] {plan.plan_id}")
    console.print(f"  Conta    : @{plan.account_handle}")
    console.print(f"  Formato  : {plan.format}")
    console.print(f"  Janela   : {plan.days_ahead} dias")
    console.print(f"  Status   : {plan.status.value}")
    console.print(f"  Pendentes: {plan.pending_count()} / {len(plan.slots)}")
    console.print(f"  Produzidos: {plan.produced_count()}")

    if plan.slots:
        table = Table(title="Slots")
        table.add_column("Slot ID", style="dim")
        table.add_column("Data")
        table.add_column("Formato")
        table.add_column("Status")
        table.add_column("Asset ID")

        for s in plan.slots:
            style = _slot_style(s.status.value)
            table.add_row(
                s.slot_id[:10],
                s.date,
                s.format,
                f"[{style}]{s.status.value}[/{style}]" if style else s.status.value,
                s.asset_id[:8] if s.asset_id else "-",
            )
        console.print(table)


@video_production_app.command(name="slot-mark")
def cmd_slot_mark(
    plan_id: str = typer.Argument(..., help="ID (ou prefixo) do plano"),
    slot_id: str = typer.Argument(..., help="ID (ou prefixo) do slot"),
    status: str = typer.Option(..., "--status", help="pending | assigned | produced | skipped"),
    asset_id: str = typer.Option(None, "--asset-id", help="ID do asset (opcional)"),
    json_out: bool = typer.Option(False, "--json", help="Saida em JSON"),
) -> None:
    """Atualiza o status de um slot no plano."""
    from src.video_production.service import mark_slot, PlanNotFoundError, PlanValidationError

    try:
        plan = mark_slot(plan_id=plan_id, slot_id=slot_id, status=status, asset_id=asset_id)
    except (PlanNotFoundError, PlanValidationError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)

    if json_out:
        console.print_json(json.dumps(plan.to_dict(), ensure_ascii=False))
        return
    console.print(f"[green]Slot {slot_id[:8]} atualizado[/green] — {status}")
