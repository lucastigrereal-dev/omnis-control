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


# ── Brand Kits ───────────────────────────────────────────────────────────────

@delivery_app.command("brand-kit-set")
def cmd_brand_kit_set(
    account: str = typer.Option(..., "--account", help="Handle Instagram"),
    display_name: str = typer.Option(..., "--display-name", help="Nome de exibicao"),
    primary_color: str = typer.Option("#000000", "--primary-color", help="Cor primaria hex"),
    secondary_color: str = typer.Option("#FFFFFF", "--secondary-color", help="Cor secundaria hex"),
    tone: str = typer.Option("casual", "--tone", help="Tom de voz: formal|casual|inspiracional"),
    bio: str = typer.Option("", "--bio", help="Bio do perfil"),
    website: str = typer.Option(None, "--website", help="Website"),
    hashtags: str = typer.Option("", "--hashtags", help="Hashtags separadas por virgula"),
    json_out: bool = typer.Option(False, "--json", help="Saida em JSON"),
) -> None:
    """Define ou atualiza o brand kit de uma conta."""
    from src.delivery_templates.service import set_brand_kit

    tags = [h.strip().lstrip("#") for h in hashtags.split(",") if h.strip()] if hashtags else []
    kit = set_brand_kit(
        account_handle=account,
        display_name=display_name,
        primary_color=primary_color,
        secondary_color=secondary_color,
        tone=tone,
        bio=bio,
        website=website or None,
        hashtags=tags,
    )
    if json_out:
        console.print_json(json.dumps(kit.to_dict(), ensure_ascii=False))
        return
    console.print(f"[green]Brand kit salvo[/green] — @{kit.account_handle}")
    console.print(f"  {kit.display_name} | {kit.primary_color} | {kit.tone}")


@delivery_app.command("brand-kit-get")
def cmd_brand_kit_get(
    account: str = typer.Argument(..., help="Handle Instagram"),
    json_out: bool = typer.Option(False, "--json", help="Saida em JSON"),
) -> None:
    """Mostra o brand kit de uma conta."""
    from src.delivery_templates.service import get_brand_kit, BrandKitNotFoundError

    try:
        kit = get_brand_kit(account)
    except BrandKitNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)

    if json_out:
        console.print_json(json.dumps(kit.to_dict(), ensure_ascii=False))
        return
    console.print(f"[bold]Brand Kit:[/bold] @{kit.account_handle}")
    console.print(f"  Nome    : {kit.display_name}")
    console.print(f"  Cor 1   : {kit.primary_color}")
    console.print(f"  Cor 2   : {kit.secondary_color}")
    console.print(f"  Tom     : {kit.tone}")
    if kit.bio:
        console.print(f"  Bio     : {kit.bio[:60]}")
    if kit.hashtags:
        console.print(f"  Tags    : #{', #'.join(kit.hashtags[:5])}")


@delivery_app.command("brand-kit-list")
def cmd_brand_kit_list(
    json_out: bool = typer.Option(False, "--json", help="Saida em JSON"),
) -> None:
    """Lista todos os brand kits cadastrados."""
    from src.delivery_templates.service import list_brand_kits

    kits = list_brand_kits()
    if json_out:
        console.print_json(json.dumps([k.to_dict() for k in kits], ensure_ascii=False))
        return
    if not kits:
        console.print("[yellow]Nenhum brand kit cadastrado.[/yellow]")
        return
    table = Table(title=f"Brand Kits ({len(kits)})")
    table.add_column("Conta")
    table.add_column("Nome")
    table.add_column("Cor 1")
    table.add_column("Tom")
    for k in kits:
        table.add_row(f"@{k.account_handle}", k.display_name, k.primary_color, k.tone)
    console.print(table)


# ── Delivery Templates ────────────────────────────────────────────────────────

@delivery_app.command("template-create")
def cmd_template_create(
    name: str = typer.Option(..., "--name", help="Nome do template"),
    account: str = typer.Option(..., "--account", help="Handle Instagram"),
    format: str = typer.Option("custom", "--format", help="hotel_collab|restaurante_collab|press_kit|custom"),
    style: str = typer.Option("casual", "--style", help="formal|casual|inspiracional"),
    hashtags: int = typer.Option(5, "--hashtags", help="Numero de hashtags padrao (0-30)"),
    no_metrics: bool = typer.Option(False, "--no-metrics", help="Omitir metricas"),
    no_checklist: bool = typer.Option(False, "--no-checklist", help="Omitir checklist"),
    notes: str = typer.Option(None, "--notes", help="Notas personalizadas"),
    json_out: bool = typer.Option(False, "--json", help="Saida em JSON"),
) -> None:
    """Cria um template de entrega para uma conta."""
    from src.delivery_templates.service import create_template, ValidationError

    try:
        tmpl = create_template(
            name=name,
            account_handle=account,
            delivery_format=format,
            caption_style=style,
            default_hashtag_count=hashtags,
            include_metrics=not no_metrics,
            include_checklist=not no_checklist,
            custom_notes=notes,
        )
    except ValidationError as exc:
        console.print(f"[red]Validacao: {exc}[/red]")
        raise typer.Exit(1)

    if json_out:
        console.print_json(json.dumps(tmpl.to_dict(), ensure_ascii=False))
        return
    console.print(f"[green]Template criado[/green] — {tmpl.template_id}")
    console.print(f"  Nome    : {tmpl.name}")
    console.print(f"  Conta   : @{tmpl.account_handle}")
    console.print(f"  Formato : {tmpl.delivery_format}")


@delivery_app.command("template-list")
def cmd_template_list(
    account: str = typer.Option(None, "--account", help="Filtrar por conta"),
    json_out: bool = typer.Option(False, "--json", help="Saida em JSON"),
) -> None:
    """Lista templates de entrega."""
    from src.delivery_templates.service import list_templates

    templates = list_templates(account_handle=account)
    if json_out:
        console.print_json(json.dumps([t.to_dict() for t in templates], ensure_ascii=False))
        return
    if not templates:
        console.print("[yellow]Nenhum template cadastrado.[/yellow]")
        return
    table = Table(title=f"Templates de Entrega ({len(templates)})")
    table.add_column("ID", style="cyan")
    table.add_column("Nome")
    table.add_column("Conta")
    table.add_column("Formato")
    table.add_column("Tom")
    for t in templates:
        table.add_row(t.template_id[:12], t.name, f"@{t.account_handle}", t.delivery_format, t.caption_style)
    console.print(table)
