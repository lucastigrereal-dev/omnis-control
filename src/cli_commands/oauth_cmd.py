"""CLI commands para OAuth Readiness — P1.2a."""
from __future__ import annotations

import json
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.oauth_readiness import get_checker
from src.oauth_readiness.models import OAuthReadinessStatus

oauth_app = typer.Typer(
    name="oauth",
    help="OAuth Meta Readiness Gate — preparacao sem executar OAuth real",
    add_completion=False,
)
console = Console()


def _status_style(status: str) -> str:
    return {
        OAuthReadinessStatus.READY: "[green]",
        OAuthReadinessStatus.BLOCKED: "[red]",
        OAuthReadinessStatus.HUMAN_REQUIRED: "[yellow]",
        OAuthReadinessStatus.NOT_CONFIGURED: "[dim]",
        OAuthReadinessStatus.FAILED: "[red]",
    }.get(status, "")


def _check_icon(passed: bool, status: str) -> str:
    if passed:
        return "[green]PASS[/green]"
    if status == OAuthReadinessStatus.HUMAN_REQUIRED:
        return "[yellow]HUMAN[/yellow]"
    if status == OAuthReadinessStatus.FAILED:
        return "[red]FAIL[/red]"
    return "[red]FAIL[/red]"


@oauth_app.command(name="readiness")
def oauth_readiness(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Executa 12 checks de preparacao para OAuth Meta.

    Nao le .env, nao chama Meta, nao executa OAuth real.
    Detecta se META_APP_ID/SECRET estao documentados e se infra
    esta pronta para receber OAuth.
    """
    checker = get_checker()
    report = checker.check_all()

    if json_output:
        print(report.model_dump_json(indent=2))
        return

    console.print(Panel(
        f"[bold]OAuth Meta — Readiness Gate[/bold]\n"
        f"Status: {_status_style(report.overall_status)}{report.overall_status}[/]",
        title="P1.2a"
    ))

    table = Table(title=f"Checks — {report.passed}/{report.total_checks} passaram")
    table.add_column("Check", style="cyan")
    table.add_column("Resultado")
    table.add_column("Requerido")
    table.add_column("Detalhe")

    for c in report.checks:
        req = "[bold]sim[/bold]" if c.required else "nao"
        table.add_row(
            c.label,
            _check_icon(c.passed, c.status),
            req,
            c.detail[:60],
        )
    console.print(table)

    if report.blocked_by_required > 0:
        blocked = [c for c in report.checks if not c.passed and c.required]
        console.print(f"\n[bold]Bloqueios ({report.blocked_by_required}):[/bold]")
        for c in blocked:
            console.print(f"  [red]x[/red] {c.label}: {c.recommendation}")

    console.print(f"\n[bold]Proximo passo:[/bold] {report.next_action}")

    if report.can_proceed and report.overall_status != OAuthReadinessStatus.HUMAN_REQUIRED:
        console.print(f"\n[green]GO para OAuth Meta![/green]")


@oauth_app.command(name="checklist")
def oauth_checklist() -> None:
    """Lista os 12 checks exatos, sem executa-los."""
    console.print("[bold]OAuth Readiness Checklist — 12 precondicoes[/bold]\n")

    items = [
        ("docker_running", "Docker daemon acessivel", True),
        ("publisher_os_healthy", "Publisher Core health endpoint (:8000)", True),
        ("supabase_db_accessible", "Supabase Postgres acessivel (:5434)", True),
        ("redis_accessible", "Redis acessivel (:6382)", False),
        ("disk_space", "Espaco em disco >= 5% livre", True),
        ("meta_app_id_exists", "META_APP_ID documentado no .env.example", True),
        ("meta_app_secret_exists", "META_APP_SECRET documentado no .env.example", True),
        ("meta_app_id_configured", "META_APP_ID preenchido no .env (verificacao humana)", True),
        ("meta_app_secret_configured", "META_APP_SECRET preenchido no .env (verificacao humana)", True),
        ("meta_callback_url_documented", "Callback URL documentada no .env.example", True),
        ("instagram_accounts_registered", "Contas Instagram cadastradas no AccountRegistry", True),
        ("network_outbound", "Conectividade com graph.facebook.com", False),
    ]

    for check_id, label, required in items:
        req_str = "[bold]OBRIGATORIO[/bold]" if required else "[dim]opcional[/dim]"
        console.print(f"  [cyan]{check_id:<35}[/cyan] {label:<60} {req_str}")


@oauth_app.command(name="start")
def oauth_start() -> None:
    """Simula inicio do fluxo OAuth (SEMPRE bloqueia sem executar)."""
    checker = get_checker()
    report = checker.check_all()

    if not report.can_proceed:
        console.print("[red]OAuth NAO pode ser iniciado. Precondicoes nao atendidas.[/red]")
        console.print(f"\nExecute 'omnis oauth readiness' para ver os bloqueios.")
        console.print(f"\n{report.next_action}")
        raise typer.Exit(1)

    if report.overall_status == OAuthReadinessStatus.HUMAN_REQUIRED:
        console.print(Panel(
            "[yellow]OAuth requer acao humana[/yellow]\n\n"
            "Lucas precisa preencher META_APP_ID e META_APP_SECRET no arquivo:\n"
            "  ~/publisher-os/.env\n\n"
            "Depois de preenchido, execute novamente:\n"
            "  omnis oauth readiness\n"
            "  omnis oauth start",
            title="HUMAN REQUIRED"
        ))
        console.print(f"\n[bold]Status:[/bold] {report.overall_status}")
        console.print(f"[bold]Próximo:[/bold] Preencher .env com credenciais Meta reais quando Lucas acordar.")
        raise typer.Exit(1)

    console.print(Panel(
        "[yellow]OAuth pronto para iniciar — fluxo real bloqueado por segurança[/yellow]\n\n"
        "Este comando nunca executa OAuth real durante a Night Shift.\n"
        "Quando Lucas autorizar, o fluxo sera:\n"
        "  1. Carregar META_APP_ID/SECRET do .env\n"
        "  2. Gerar URL de autorizacao Meta\n"
        "  3. Lucas autoriza no navegador\n"
        "  4. Callback captura o code\n"
        "  5. Trocar code por access_token\n"
        "  6. Armazenar token no cofre seguro",
        title="READY (bloqueio de seguranca ativo)"
    ))
    console.print(f"\nStatus: [yellow]human_required[/yellow] — aguardando Lucas acordado.")
