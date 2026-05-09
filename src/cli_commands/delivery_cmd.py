"""CLI for Client Delivery — client-ready export bundles. NUNCA publica."""
import json
import typer
from rich.console import Console
from rich.table import Table

from src.client_delivery.errors import DeliveryNotFoundError, DeliverySourceError
import src.client_delivery.service as delivery_svc

delivery_app = typer.Typer(name="delivery", help="Client Delivery — entrega comercial para humano/cliente. NUNCA publica.")
console = Console()


@delivery_app.callback()
def _callback():
    """Client Delivery — exporta entrega comercial organizada."""


@delivery_app.command("create")
def cmd_delivery_create(
    from_package: str = typer.Option(None, "--from-package", help="ID (ou prefixo) do pacote offline"),
    from_campaign: str = typer.Option(None, "--from-campaign", help="ID (ou prefixo) da campanha"),
):
    """Cria entrega comercial a partir de pacote ou campanha."""
    if from_package:
        try:
            d = delivery_svc.create_delivery_from_package(from_package)
        except DeliverySourceError as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(1)
    elif from_campaign:
        try:
            d = delivery_svc.create_delivery_from_campaign(from_campaign)
        except DeliverySourceError as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(1)
    else:
        console.print("[red]Use --from-package ou --from-campaign.[/red]")
        raise typer.Exit(1)

    console.print(f"[green]Entrega criada[/green] — {d.delivery_id}")
    console.print(f"  Fonte  : {d.source_type.value} / {d.source_id}")
    console.print(f"  Status : {d.status.value}")
    console.print(f"  Dir    : {d.output_dir}")


@delivery_app.command("list")
def cmd_delivery_list():
    """Lista entregas criadas."""
    deliveries = delivery_svc.list_deliveries()
    if not deliveries:
        console.print("[yellow]Nenhuma entrega criada ainda.[/yellow]")
        return
    table = Table(title="Entregas Comerciais")
    table.add_column("delivery_id", style="cyan")
    table.add_column("source_type")
    table.add_column("source_id")
    table.add_column("status", style="green")
    for d in deliveries:
        table.add_row(d.get("delivery_id", ""), d.get("source_type", ""), d.get("source_id", ""), d.get("status", ""))
    console.print(table)


@delivery_app.command("show")
def cmd_delivery_show(
    delivery_id: str = typer.Argument(..., help="ID (ou prefixo) da entrega"),
):
    """Mostra detalhes de uma entrega."""
    entry = delivery_svc.get_delivery(delivery_id)
    if not entry:
        console.print(f"[red]Entrega '{delivery_id}' nao encontrada.[/red]")
        raise typer.Exit(1)
    console.print_json(json.dumps(entry, ensure_ascii=False, indent=2))


@delivery_app.command("zip")
def cmd_delivery_zip(
    delivery_id: str = typer.Argument(..., help="ID (ou prefixo) da entrega"),
):
    """Gera ZIP de uma entrega."""
    try:
        result = delivery_svc.zip_delivery(delivery_id)
    except DeliveryNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)
    console.print(f"[green]ZIP criado[/green] — {result['zip_path']}")
    console.print(f"  Tamanho: {result['size_kb']}KB")
