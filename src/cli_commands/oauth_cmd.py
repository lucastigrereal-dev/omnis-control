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


@oauth_app.command(name="accounts")
def oauth_accounts(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Lista todas as contas com status de OAuth readiness.

    Nao mostra secrets, tokens ou valores reais.
    """
    from src.content_queue.accounts import AccountRegistry
    from src.oauth_readiness.account_readiness import (
        build_account_readiness,
        normalize_handle,
        KNOWN_HANDLES,
    )
    from src.oauth_readiness.checklist import get_env_probe_summary

    registry = AccountRegistry()
    accounts = registry.list_all()
    probe = get_env_probe_summary()

    env_status: dict[str, str] = {}
    for r in probe.results:
        env_status[r.canonical_name] = r.status

    callback_ok = False
    try:
        from src.oauth_readiness.checklist import _check_callback_route_exists
        callback_check = _check_callback_route_exists()
        callback_ok = callback_check.passed
    except Exception:
        pass

    # Enrich with known handles not in registry
    seen_handles = {normalize_handle(a.handle) for a in accounts}
    readiness_list = []
    for a in accounts:
        readiness_list.append(
            build_account_readiness(
                handle=a.handle,
                account_registry_id=a.account_id,
                env_probe_results=env_status,
                has_asset=False,
                has_caption=False,
                callback_http_200=callback_ok,
            )
        )

    if json_output:
        import json as _json
        output = [
            {
                "handle": r.account_handle,
                "registry_id": r.account_registry_id,
                "risk_level": r.risk_level.value,
                "is_test_candidate": r.is_test_candidate,
                "oauth_ready": r.ready_for_oauth,
                "first_post_ready": r.ready_for_first_post,
                "blockers": r.blockers,
                "warnings": r.warnings,
                "next_actions": r.next_actions,
            }
            for r in readiness_list
        ]
        print(_json.dumps(output, indent=2, ensure_ascii=False))
        return

    if not readiness_list:
        console.print("[yellow]Nenhuma conta encontrada no registry.[/yellow]")
        console.print("[dim]Handles conhecidos (nao registrados):[/dim]")
        for h, info in KNOWN_HANDLES.items():
            risk_color = {
                "critical": "red",
                "high": "yellow",
                "medium": "dim",
                "low": "green",
            }.get(info["risk"].value, "dim")
            console.print(f"  @{h} — {info['followers']:,} seguidores — [{risk_color}]risk: {info['risk'].value}[/{risk_color}]")
        console.print("\n[dim]Use 'omnis oauth account-readiness <handle>' para avaliar uma conta.[/dim]")
        return

    # Sort: critical/high first, then medium/low
    risk_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    readiness_list.sort(key=lambda r: (risk_order.get(r.risk_level.value, 9), r.account_handle))

    table = Table(title=f"Contas — OAuth Readiness ({len(readiness_list)})")
    table.add_column("Handle", style="cyan")
    table.add_column("Risk")
    table.add_column("Test?")
    table.add_column("OAuth")
    table.add_column("Biz ID")
    table.add_column("Page ID")
    table.add_column("Token")

    for r in readiness_list:
        risk_style = {
            "critical": "[red]",
            "high": "[yellow]",
            "medium": "[dim]",
            "low": "[green]",
        }.get(r.risk_level.value, "")

        test_icon = "[green]sim[/green]" if r.is_test_candidate else "[red]bloqueado[/red]"
        oauth_icon = "[green]ready[/green]" if r.ready_for_oauth else "[red]no-go[/red]"
        biz_icon = "[green]ok[/green]" if r.instagram_business_account_id_status == "present" else "[dim]faltando[/dim]"
        page_icon = "[green]ok[/green]" if r.facebook_page_id_status == "present" else "[dim]faltando[/dim]"
        token_icon = "[green]ok[/green]" if r.token_status == "present" else "[dim]faltando[/dim]"

        table.add_row(
            f"@{r.account_handle}",
            f"{risk_style}{r.risk_level.value}[/{risk_style}]",
            test_icon,
            oauth_icon,
            biz_icon,
            page_icon,
            token_icon,
        )
    console.print(table)

    # Missing handles
    missing = [h for h in KNOWN_HANDLES if h not in seen_handles]
    if missing:
        console.print(f"\n[dim]Handles conhecidos nao registrados: {', '.join('@' + h for h in missing)}[/dim]")


@oauth_app.command(name="account-readiness")
def oauth_account_readiness(
    handle: str = typer.Argument(..., help="Handle da conta (ex: @afamiliatigrereal)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Mostra readiness detalhada de uma conta para OAuth/publicacao.

    NUNCA mostra secrets, tokens ou valores reais.
    """
    from src.oauth_readiness.account_readiness import (
        build_account_readiness,
        normalize_handle,
        risk_for_handle,
        is_allowed_first_test,
        KNOWN_HANDLES,
    )
    from src.oauth_readiness.checklist import get_env_probe_summary
    from src.content_queue.accounts import AccountRegistry

    norm = normalize_handle(handle)
    registry = AccountRegistry()
    account = registry.get_by_handle(norm)

    probe = get_env_probe_summary()
    env_status: dict[str, str] = {}
    for r in probe.results:
        env_status[r.canonical_name] = r.status

    callback_ok = False
    try:
        from src.oauth_readiness.checklist import _check_callback_route_exists
        callback_check = _check_callback_route_exists()
        callback_ok = callback_check.passed
    except Exception:
        pass

    readiness = build_account_readiness(
        handle=norm,
        account_registry_id=account.account_id if account else None,
        env_probe_results=env_status,
        has_asset=False,
        has_caption=False,
        callback_http_200=callback_ok,
    )

    if json_output:
        import json as _json
        output = {
            "handle": readiness.account_handle,
            "registry_id": readiness.account_registry_id,
            "risk_level": readiness.risk_level.value,
            "is_test_candidate": readiness.is_test_candidate,
            "oauth_ready": readiness.ready_for_oauth,
            "first_post_ready": readiness.ready_for_first_post,
            "instagram_business_account_id": readiness.instagram_business_account_id_status,
            "facebook_page_id": readiness.facebook_page_id_status,
            "meta_app_secret": readiness.meta_app_secret_status,
            "meta_graph_version": readiness.meta_graph_version_status,
            "callback": readiness.callback_status,
            "token": readiness.token_status,
            "asset": readiness.asset_candidate_status,
            "caption": readiness.caption_candidate_status,
            "blockers": readiness.blockers,
            "warnings": readiness.warnings,
            "next_actions": readiness.next_actions,
        }
        # Add known handle info if not in registry
        if not account:
            info = KNOWN_HANDLES.get(norm)
            if info:
                output["source"] = "known_handle"
                output["followers"] = info["followers"]
                output["niche"] = info["niche"]
        print(_json.dumps(output, indent=2, ensure_ascii=False))
        return

    # Rich output
    status_emoji = {
        "ready": "[green]READY[/green]",
        "partial": "[yellow]PARTIAL[/yellow]",
        "blocked": "[red]BLOCKED[/red]",
        "human_required": "[yellow]HUMAN_REQUIRED[/yellow]",
        "not_configured": "[dim]NOT CONFIGURED[/dim]",
    }

    oauth_status = "ready" if readiness.ready_for_oauth else "blocked"
    first_post_status = "ready" if readiness.ready_for_first_post else "blocked"

    info = ""
    if not account:
        known = KNOWN_HANDLES.get(norm)
        if known:
            info = f"\n[dim]Fonte: handles conhecidos (nao esta no registry)[/dim]"
            info += f"\n[dim]Seguidores: {known['followers']:,} | Nicho: {known['niche']}[/dim]"

    console.print(Panel(
        f"[bold]Account: @{readiness.account_handle}[/bold]"
        f"{info}\n"
        f"Risk Level: {status_emoji.get(readiness.risk_level.value, readiness.risk_level.value)}\n"
        f"Test Candidate: {'[green]Sim[/green]' if readiness.is_test_candidate else '[red]Nao (bloqueado)[/red]'}\n"
        f"OAuth Ready: {status_emoji[oauth_status]}\n"
        f"First Post Ready: {status_emoji[first_post_status]}",
        title="P1.6A — Account Readiness"
    ))

    # Fields table
    ftable = Table(title="Campos")
    ftable.add_column("Campo", style="cyan")
    ftable.add_column("Status")
    for label, status in [
        ("Instagram Business Account ID", readiness.instagram_business_account_id_status),
        ("Facebook Page ID", readiness.facebook_page_id_status),
        ("META_APP_SECRET", readiness.meta_app_secret_status),
        ("META_GRAPH_VERSION", readiness.meta_graph_version_status),
        ("Callback Route", readiness.callback_status),
        ("Access Token", readiness.token_status),
        ("Asset", readiness.asset_candidate_status),
        ("Caption", readiness.caption_candidate_status),
    ]:
        s_style = {
            "present": "[green]present[/green]",
            "missing": "[red]missing[/red]",
            "empty": "[yellow]empty[/yellow]",
            "alias_present": "[yellow]alias[/yellow]",
            "not_configured": "[dim]not configured[/dim]",
        }.get(status, status)
        ftable.add_row(label, s_style)
    console.print(ftable)

    if readiness.blockers:
        console.print("\n[bold red]Blockers:[/bold red]")
        for b in readiness.blockers:
            console.print(f"  [red]x[/red] {b}")
    if readiness.warnings:
        console.print("\n[bold yellow]Warnings:[/bold yellow]")
        for w in readiness.warnings:
            console.print(f"  [yellow]![/yellow] {w}")
    if readiness.next_actions:
        console.print("\n[bold]Next Actions:[/bold]")
        for a in readiness.next_actions:
            console.print(f"  [cyan]>[/cyan] {a}")
