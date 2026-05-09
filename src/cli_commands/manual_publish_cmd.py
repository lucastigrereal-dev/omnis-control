"""CLI for Manual Publishing Tracker. NUNCA publica automaticamente."""
import json
import typer
from rich.console import Console
from rich.table import Table

from src.manual_publishing.errors import PublishRecordNotFoundError
import src.manual_publishing.service as pub_svc

manual_publish_app = typer.Typer(name="manual-publish", help="Manual Publishing Tracker — registra postagens humanas. NUNCA publica automaticamente.")
console = Console()


@manual_publish_app.callback()
def _callback():
    """Manual Publishing Tracker."""


@manual_publish_app.command("mark")
def cmd_mark(
    package_id: str = typer.Argument(..., help="ID do pacote postado"),
    platform: str = typer.Option("instagram", "--platform", help="Plataforma"),
    url: str = typer.Option(None, "--url", help="URL do post publicado"),
    notes: str = typer.Option(None, "--notes", help="Notas adicionais"),
):
    """Marca um pacote como postado manualmente."""
    record = pub_svc.mark_published(package_id=package_id, platform=platform, url=url, notes=notes)
    console.print(f"[green]Registrado[/green] — {record.package_id}")
    console.print(f"  Plataforma : {record.platform}")
    console.print(f"  Postado em : {record.posted_at[:19]}")
    if record.url:
        console.print(f"  URL        : {record.url}")


@manual_publish_app.command("list")
def cmd_list():
    """Lista registros de publicacao manual."""
    records = pub_svc.list_published()
    if not records:
        console.print("[yellow]Nenhum registro de publicacao.[/yellow]")
        return
    table = Table(title="Publicacoes Manuais")
    table.add_column("package_id", style="cyan")
    table.add_column("platform")
    table.add_column("posted_at")
    table.add_column("status", style="green")
    for r in records:
        table.add_row(r.get("package_id", ""), r.get("platform", ""), r.get("posted_at", "")[:19], r.get("status", ""))
    console.print(table)


@manual_publish_app.command("show")
def cmd_show(
    package_id: str = typer.Argument(..., help="ID (ou prefixo) do pacote"),
):
    """Mostra registro de publicacao de um pacote."""
    try:
        record = pub_svc.get_published(package_id)
    except PublishRecordNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)
    console.print_json(json.dumps(record, ensure_ascii=False, indent=2))
