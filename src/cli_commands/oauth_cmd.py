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
    """Lista todos os checks de preparacao, sem executa-los."""
    from src.oauth_readiness.checklist import get_all_checks

    checks = get_all_checks()
    console.print(f"[bold]OAuth Readiness Checklist — {len(checks)} precondicoes[/bold]\n")

    for fn in checks:
        try:
            c = fn()
            req_str = "[bold]OBRIGATORIO[/bold]" if c.required else "[dim]opcional[/dim]"
            console.print(f"  [cyan]{c.check_id:<38}[/cyan] {c.label:<55} {req_str}")
        except Exception:
            name = fn.__name__
            console.print(f"  [red]{name:<38}[/red] {'(falhou ao carregar)':<55} [dim]---[/dim]")


@oauth_app.command(name="probe")
def oauth_probe(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Verifica variaveis Meta no .env com seguranca — sem mostrar valores.

    Retorna status de cada variavel: present, missing, empty, invalid_format.
    NUNCA imprime ou armazena valores reais.
    """
    from src.oauth_readiness.checklist import get_env_probe_summary
    from src.oauth_readiness.env_probe import safe_summary

    probe = get_env_probe_summary()

    if json_output:
        print(json.dumps(probe.to_dict(), indent=2, ensure_ascii=False))
        return

    console.print(Panel(
        f"[bold]OAuth Meta — Env Probe[/bold]\n"
        f"Arquivo: {probe.source_path}\n"
        f"Existe: {'[green]Sim[/green]' if probe.file_exists else '[red]Nao[/red]'}\n"
        f"Variaveis: {probe.present_count} presentes, "
        f"{probe.empty_count} vazias, "
        f"{probe.missing_count} ausentes",
        title="P1.4"
    ))

    for r in probe.results:
        icon = {
            "present": "[green]PRESENT[/green]",
            "missing": "[dim]MISSING[/dim]",
            "empty": "[yellow]EMPTY[/yellow]",
            "invalid_format": "[red]INVALID[/red]",
            "alias_present": "[yellow]ALIAS[/yellow]",
        }.get(r.status, "[?]")
        req = " [bold](obrigatorio)[/bold]" if r.required else ""
        note = f" [dim]({r.format_note})[/dim]" if r.format_note else ""
        alias_info = f" [dim](alias: {r.found_via_alias})[/dim]" if r.found_via_alias else ""
        console.print(f"  {icon} {r.var_name}{req}{alias_info}{note}")

    console.print(f"\n[dim]Use 'omnis oauth readiness' para o report completo de infra + env.[/dim]")


@oauth_app.command(name="validate")
def oauth_validate(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Valida readiness completa: probe + infra + resumo do que falta."""
    from src.oauth_readiness.checklist import get_env_probe_summary

    checker = get_checker()
    report = checker.check_all()
    probe = get_env_probe_summary()

    if json_output:
        output = {
            "overall_status": report.overall_status,
            "can_proceed": report.can_proceed,
            "total_checks": report.total_checks,
            "passed": report.passed,
            "failed": report.failed,
            "blocked_by_required": report.blocked_by_required,
            "next_action": report.next_action,
            "env_probe": probe.to_dict(),
            "checked_at": report.checked_at,
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return

    status_style = _status_style(report.overall_status)
    console.print(Panel(
        f"[bold]OAuth Meta — Validacao Completa[/bold]\n"
        f"Status: {status_style}{report.overall_status}[/]  |  "
        f"Checks: {report.passed}/{report.total_checks} passaram  |  "
        f"Bloqueios: {report.blocked_by_required}",
        title="P1.4"
    ))

    # Resumo de variaveis
    console.print(f"\n[bold]Variaveis no .env:[/bold]")
    for r in probe.results:
        if r.status == "present":
            continue
        icon = {
            "missing": "[red]FALTA[/red]",
            "empty": "[yellow]VAZIO[/yellow]",
            "invalid_format": "[red]INVALIDO[/red]",
            "alias_present": "[yellow]ALIAS[/yellow]",
        }.get(r.status, "[?]")
        console.print(f"  {icon} {r.canonical_name}")

    if probe.present_count == probe.total_checked:
        console.print(f"  [green]Todas as {probe.total_checked} variaveis presentes[/green]")

    # Bloqueios de infra
    failed_infra = [c for c in report.checks if not c.passed and c.required and not c.check_id.startswith("env_")]
    if failed_infra:
        console.print(f"\n[bold]Infra com problema:[/bold]")
        for c in failed_infra:
            console.print(f"  [red]x[/red] {c.label}: {c.recommendation}")

    console.print(f"\n[bold]Acao necessaria:[/bold] {report.next_action}")

    # GO/NO-GO
    if report.overall_status == "ready":
        console.print(f"\n[green][bold]GO[/bold] para OAuth manual controlado.[/green]")
        console.print(f"[yellow]AVISO:[/yellow] OAuth real exige Lucas acordado no navegador.")
    elif report.overall_status == "human_required":
        console.print(f"\n[yellow][bold]NO-GO[/bold] — requer acao humana.[/yellow]")
    else:
        console.print(f"\n[red][bold]NO-GO[/bold] — bloqueios precisam ser resolvidos.[/red]")


@oauth_app.command(name="start")
def oauth_start() -> None:
    """Simula inicio do fluxo OAuth (SEMPRE bloqueia sem executar)."""
    checker = get_checker()
    report = checker.check_all()

    if not report.can_proceed:
        console.print("[red]OAuth NAO pode ser iniciado. Precondicoes nao atendidas.[/red]")
        console.print(f"\nExecute 'omnis oauth validate' para ver o que falta.")
        console.print(f"\n{report.next_action}")
        raise typer.Exit(1)

    if report.overall_status == OAuthReadinessStatus.HUMAN_REQUIRED:
        console.print(Panel(
            "[yellow]OAuth requer acao humana[/yellow]\n\n"
            "Variaveis obrigatorias precisam ser preenchidas no arquivo:\n"
            "  ~/publisher-os/.env\n\n"
            "Use 'omnis oauth probe' para ver quais estao vazias.\n"
            "Depois de preenchido:\n"
            "  omnis oauth readiness\n"
            "  omnis oauth start",
            title="HUMAN REQUIRED"
        ))
        console.print(f"\n[bold]Status:[/bold] {report.overall_status}")
        console.print(f"[bold]Próximo:[/bold] Preencher .env com credenciais Meta reais.")
        raise typer.Exit(1)

    console.print(Panel(
        "[yellow]OAuth pronto para iniciar — fluxo real bloqueado por seguranca[/yellow]\n\n"
        "Este comando nunca executa OAuth real sem autorizacao.\n"
        "Quando Lucas autorizar, o fluxo sera:\n"
        "  1. Carregar credenciais do .env\n"
        "  2. Gerar URL de autorizacao Meta\n"
        "  3. Lucas autoriza no navegador\n"
        "  4. Callback captura o code\n"
        "  5. Trocar code por access_token\n"
        "  6. Armazenar token no cofre seguro",
        title="READY (bloqueio de seguranca ativo)"
    ))
    console.print(f"\n[bold]Status:[/bold] [yellow]human_required[/yellow] — aguardando Lucas acordado para OAuth real.")
