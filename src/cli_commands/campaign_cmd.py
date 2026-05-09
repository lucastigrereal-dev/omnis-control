"""CLI for Campaign Package — local campaign bundles. NUNCA publica."""
import json
import typer
from rich.console import Console
from rich.table import Table

from src.campaign_package.errors import CampaignNotFoundError, CampaignValidationError
import src.campaign_package.service as campaign_svc

campaign_app = typer.Typer(name="campaign", help="Campaign Package — pacotes de campanha local. NUNCA publica.")
console = Console()


@campaign_app.callback()
def _callback():
    """Campaign Package — pacotes de campanha local."""


@campaign_app.command("create")
def cmd_campaign_create(
    name: str = typer.Option("campanha_sem_nome", "--name", help="Nome da campanha"),
    count: int = typer.Option(10, "--count", help="Numero de posts"),
    account: str = typer.Option("afamiliatigrereal", "--account", help="Perfil"),
):
    """Cria campanha local com N posts."""
    try:
        campaign = campaign_svc.create_campaign(name=name, count=count, account_handle=account)
    except CampaignValidationError as exc:
        console.print(f"[red]Erro de validacao: {exc}[/red]")
        raise typer.Exit(1)
    console.print(f"[green]Campanha criada[/green] — {campaign.campaign_id}")
    console.print(f"  Nome  : {campaign.name}")
    console.print(f"  Posts : {campaign.post_count}")
    console.print(f"  Conta : {campaign.account_handle}")
    console.print(f"  Dir   : {campaign.output_dir}")


@campaign_app.command("list")
def cmd_campaign_list():
    """Lista campanhas geradas."""
    campaigns = campaign_svc.list_campaigns()
    if not campaigns:
        console.print("[yellow]Nenhuma campanha gerada ainda.[/yellow]")
        return
    table = Table(title="Campanhas")
    table.add_column("campaign_id", style="cyan")
    table.add_column("name")
    table.add_column("posts")
    table.add_column("status", style="green")
    table.add_column("conta")
    for c in campaigns:
        table.add_row(c.get("campaign_id", ""), c.get("name", ""), str(c.get("post_count", "")), c.get("status", ""), c.get("account_handle", ""))
    console.print(table)


@campaign_app.command("show")
def cmd_campaign_show(
    campaign_id: str = typer.Argument(..., help="ID (ou prefixo) da campanha"),
):
    """Mostra detalhes de uma campanha."""
    entry = campaign_svc.get_campaign(campaign_id)
    if not entry:
        console.print(f"[red]Campanha '{campaign_id}' nao encontrada.[/red]")
        raise typer.Exit(1)
    console.print_json(json.dumps(entry, ensure_ascii=False, indent=2))


@campaign_app.command("validate")
def cmd_campaign_validate(
    campaign_id: str = typer.Argument(..., help="ID (ou prefixo) da campanha"),
):
    """Valida estrutura de uma campanha."""
    try:
        result = campaign_svc.validate_campaign(campaign_id)
    except CampaignNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)
    if result["is_valid"]:
        console.print(f"[green]Campanha valida[/green] — {result['campaign_id']}")
    else:
        console.print(f"[red]Invalida[/red] — {result['campaign_id']}")
        for f in result["checks_failed"]:
            console.print(f"  [red]FALHOU: {f}[/red]")


@campaign_app.command("zip")
def cmd_campaign_zip(
    campaign_id: str = typer.Argument(..., help="ID (ou prefixo) da campanha"),
):
    """Gera ZIP de uma campanha."""
    try:
        result = campaign_svc.zip_campaign(campaign_id)
    except CampaignNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)
    console.print(f"[green]ZIP criado[/green] — {result['zip_path']}")
    console.print(f"  Tamanho: {result['size_kb']}KB")


def _grade_style(grade: str) -> str:
    return {"ready": "green", "needs_adjustment": "yellow", "blocked": "red", "unscored": "dim"}.get(grade, "")


@campaign_app.command("audit")
def cmd_campaign_audit(
    campaign_id: str = typer.Argument(..., help="ID (ou prefixo) da campanha"),
    json_out: bool = typer.Option(False, "--json", help="Saida em JSON"),
) -> None:
    """Audita qualidade dos pacotes de uma campanha."""
    from src.campaign_auditor.service import audit_campaign, CampaignNotFoundError as AuditNotFound

    try:
        result = audit_campaign(campaign_id)
    except AuditNotFound as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)

    if json_out:
        console.print_json(json.dumps(result.to_dict(), ensure_ascii=False))
        return

    grade = result.overall_grade()
    style = _grade_style(grade)
    avg_str = f"{result.avg_score}/100" if result.avg_score is not None else "N/A"
    console.print(f"[bold]Campanha:[/bold] {result.campaign_id} — {result.campaign_name}")
    console.print(f"  Conta   : @{result.account_handle}")
    console.print(f"  Score   : [{style}]{avg_str} ({grade})[/{style}]")
    console.print(f"  Posts   : {result.scored_posts} scored / {result.unscored_posts} sem pacote")
    console.print(f"  Ready   : {result.ready_count} | Ajuste: {result.needs_adjustment_count} | Bloqueado: {result.blocked_count}")

    if result.errors:
        for e in result.errors:
            console.print(f"  [red]{e}[/red]")


@campaign_app.command("audit-all")
def cmd_campaign_audit_all(
    json_out: bool = typer.Option(False, "--json", help="Saida em JSON"),
) -> None:
    """Audita qualidade de todas as campanhas."""
    from src.campaign_auditor.service import audit_all_campaigns

    results = audit_all_campaigns()

    if json_out:
        console.print_json(json.dumps([r.to_dict() for r in results], ensure_ascii=False))
        return

    if not results:
        console.print("[yellow]Nenhuma campanha encontrada.[/yellow]")
        return

    table = Table(title=f"Auditoria de Campanhas ({len(results)})")
    table.add_column("ID", style="cyan")
    table.add_column("Nome")
    table.add_column("Conta")
    table.add_column("Score Medio", justify="right")
    table.add_column("Pronto", justify="right")
    table.add_column("Bloqueado", justify="right")
    table.add_column("Grade")

    for r in results:
        grade = r.overall_grade()
        style = _grade_style(grade)
        avg = f"{r.avg_score:.0f}" if r.avg_score is not None else "N/A"
        table.add_row(
            r.campaign_id[:14],
            r.campaign_name[:20],
            f"@{r.account_handle}",
            avg,
            str(r.ready_count),
            str(r.blocked_count),
            f"[{style}]{grade}[/{style}]" if style else grade,
        )
    console.print(table)
