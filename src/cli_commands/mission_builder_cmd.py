"""CLI for Mission Builder — P3.0. NUNCA publica."""
from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel

mission_builder_app = typer.Typer(
    name="mission-builder",
    help="Mission Builder — plano + pacote de missao local. NUNCA publica.",
    add_completion=False,
)
console = Console()


@mission_builder_app.callback()
def _callback():
    """Mission Builder — pedido simples -> plano -> pacote. NUNCA publica."""


@mission_builder_app.command(name="plan")
def cmd_plan(
    request: str = typer.Argument(..., help="Pedido em linguagem natural"),
    account: str = typer.Option(None, "--account", help="Handle Instagram (ex: afamiliatigrereal)"),
    objective: str = typer.Option("engajamento", "--objective", help="Objetivo do conteudo"),
    allow_unknown: bool = typer.Option(False, "--allow-unknown", help="Aceitar intent desconhecido"),
    json_out: bool = typer.Option(False, "--json", help="Saida em JSON"),
) -> None:
    """Gera plano de missao a partir de pedido em linguagem natural."""
    from src.mission_builder.planner import build_plan
    from src.mission_builder.errors import IntentUnknownError

    try:
        plan = build_plan(
            request_text=request,
            account_handle=account,
            objective=objective,
            allow_unknown=allow_unknown,
        )
    except IntentUnknownError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)

    if json_out:
        console.print_json(json.dumps(plan.to_dict(), ensure_ascii=False))
        return

    console.print(Panel(f"[bold]Mission Plan[/bold] — {plan.mission_id}", expand=False))
    console.print(f"  Pedido    : {plan.request_text[:60]}")
    console.print(f"  Intent    : [cyan]{plan.intent}[/cyan]")
    console.print(f"  Entregavel: {plan.deliverable}")
    console.print(f"  Formato   : {plan.format}")
    console.print(f"  Conta     : @{plan.account_handle}")
    console.print(f"  Slots     : {plan.estimated_slots}")
    console.print(f"\n  [bold]Etapas:[/bold]")
    for step in plan.steps:
        console.print(f"    {step}")
    console.print(f"\n  Para criar o pacote: [dim]mission-builder run \"{request[:40]}...\" --dry-run[/dim]")


@mission_builder_app.command(name="run")
def cmd_run(
    request: str = typer.Argument(..., help="Pedido em linguagem natural"),
    account: str = typer.Option(None, "--account", help="Handle Instagram"),
    objective: str = typer.Option("engajamento", "--objective", help="Objetivo do conteudo"),
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run", help="Criar pacote local (padrao: True)"),
    allow_unknown: bool = typer.Option(False, "--allow-unknown", help="Aceitar intent desconhecido"),
    json_out: bool = typer.Option(False, "--json", help="Saida em JSON"),
) -> None:
    """Gera plano e cria mission package local (dry-run)."""
    from src.mission_builder.executor import run
    from src.mission_builder.errors import IntentUnknownError, MissionPackageError

    try:
        plan, manifest = run(
            request_text=request,
            account_handle=account,
            objective=objective,
            dry_run=dry_run,
            allow_unknown=allow_unknown,
        )
    except IntentUnknownError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)
    except MissionPackageError as exc:
        console.print(f"[red]Falha ao criar pacote: {exc}[/red]")
        raise typer.Exit(1)

    if json_out:
        out = {"plan": plan.to_dict(), "manifest": manifest.to_dict() if manifest else None}
        console.print_json(json.dumps(out, ensure_ascii=False))
        return

    console.print(f"[green]Missao criada[/green] — {plan.mission_id}")
    console.print(f"  Intent    : {plan.intent}")
    console.print(f"  Formato   : {plan.format}")
    console.print(f"  Conta     : @{plan.account_handle}")

    if manifest:
        console.print(f"\n  [bold]Pacote em:[/bold] {manifest.package_dir}")
        console.print(f"  Arquivos  : {len(manifest.files)}")
        for f in manifest.files:
            console.print(f"    - {f}")
        console.print(f"\n  [dim]Ver proximo passo: {manifest.package_dir}/06_next_action.md[/dim]")
    else:
        console.print("  [yellow]dry-run=False: pacote nao gerado (fase segura)[/yellow]")
