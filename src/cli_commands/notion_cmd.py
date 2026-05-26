"""CLI 'notion' — Acesso direto ao Notion via OMNIS.

Comandos:
    notion status           — verifica conectividade (token + whoami)
    notion search [query]   — busca páginas/databases compartilhados com o bot
    notion page <id>        — mostra conteúdo de uma página
    notion aurora <query>   — roda Aurora context engine com fonte Notion ativa

Requer: NOTION_TOKEN no environment
    Windows PowerShell: $env:NOTION_TOKEN = "seu_token"
    Linux/Mac:          export NOTION_TOKEN="seu_token"
"""
from __future__ import annotations

import json
import os

import typer
from rich.console import Console
from rich.table import Table

notion_app = typer.Typer(
    name="notion",
    help="Acesso direto ao Notion — busca, pages, aurora.",
    add_completion=False,
)
console = Console()


def _get_connector():
    from src.notion.connector import NotionConnector
    nc = NotionConnector()
    if not nc.is_available():
        console.print("[red]NOTION_TOKEN nao configurado.[/red]")
        console.print("  Windows: [cyan]$env:NOTION_TOKEN = 'seu_token'[/cyan]")
        console.print("  Linux:   [cyan]export NOTION_TOKEN='seu_token'[/cyan]")
        raise typer.Exit(1)
    return nc


# ------------------------------------------------------------------
# notion status
# ------------------------------------------------------------------

@notion_app.command(name="status")
def cmd_status(json_out: bool = typer.Option(False, "--json")) -> None:
    """Verifica conectividade com o Notion (token + whoami)."""
    nc = _get_connector()
    info = nc.whoami()

    if json_out:
        console.print_json(json.dumps(info, ensure_ascii=False))
        return

    if info:
        console.print(f"[green]Notion conectado[/green]")
        console.print(f"  Bot:  {info.get('name', '?')}")
        console.print(f"  Type: {info.get('type', '?')}")
        console.print(f"  ID:   {info.get('id', '?')[:8]}...")
        console.print()
        console.print("[dim]Dica: para o bot ver suas paginas, compartilhe-as com a integracao OMNIS no Notion.[/dim]")
    else:
        console.print("[red]Falha ao conectar com o Notion.[/red]")
        raise typer.Exit(1)


# ------------------------------------------------------------------
# notion search
# ------------------------------------------------------------------

@notion_app.command(name="search")
def cmd_search(
    query: str = typer.Argument("", help="Texto para buscar (vazio = lista tudo)"),
    limit: int = typer.Option(20, "--limit", "-n", help="Maximo de resultados"),
    tipo: str = typer.Option("", "--type", "-t", help="Filtro: page | database"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Busca paginas e databases compartilhados com o bot OMNIS no Notion."""
    nc = _get_connector()

    filter_type = tipo if tipo in ("page", "database") else None
    pages = nc.search(query=query, page_size=limit, filter_type=filter_type)

    if json_out:
        console.print_json(json.dumps([p.to_dict() for p in pages], ensure_ascii=False))
        return

    if not pages:
        console.print("[yellow]Nenhuma pagina encontrada.[/yellow]")
        console.print("[dim]O bot OMNIS precisa ser convidado para paginas no Notion.[/dim]")
        console.print("[dim]Abra a pagina no Notion -> Share -> Convidar 'OMNIS'[/dim]")
        return

    table = Table(title=f"Notion — {len(pages)} resultado(s)")
    table.add_column("Tipo",    style="dim",   width=10)
    table.add_column("Titulo",  style="cyan",  width=40)
    table.add_column("ID",      style="dim",   width=10)
    table.add_column("URL",     width=35)

    for p in pages:
        table.add_row(
            p.object_type,
            p.title[:40],
            p.page_id[:8],
            p.url[:35],
        )

    console.print(table)


# ------------------------------------------------------------------
# notion page
# ------------------------------------------------------------------

@notion_app.command(name="page")
def cmd_page(
    page_id: str = typer.Argument(..., help="ID da pagina (8+ chars)"),
    blocks: bool = typer.Option(True, "--blocks/--no-blocks", help="Mostra conteudo dos blocos"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Mostra metadados e conteudo de uma pagina Notion."""
    nc = _get_connector()

    page = nc.get_page(page_id)
    if not page:
        console.print(f"[red]Pagina {page_id} nao encontrada ou sem acesso.[/red]")
        raise typer.Exit(1)

    if blocks:
        page_blocks = nc.get_page_blocks(page_id, page_size=50)
    else:
        page_blocks = []

    if json_out:
        out = {**page.to_dict(), "blocks": [b.to_dict() for b in page_blocks]}
        console.print_json(json.dumps(out, ensure_ascii=False))
        return

    console.print(f"\n[bold]{page.title}[/bold]")
    console.print(f"  ID:           {page.page_id[:8]}...")
    console.print(f"  Tipo:         {page.object_type}")
    console.print(f"  Criado:       {page.created_time[:10]}")
    console.print(f"  Ultima edicao:{page.last_edited[:10]}")
    console.print(f"  URL:          {page.url}")

    if page_blocks:
        console.print(f"\n  [dim]--- Conteudo ({len(page_blocks)} blocos) ---[/dim]")
        for b in page_blocks[:20]:
            if b.text:
                prefix = "  # " if "heading" in b.block_type else "  - " if "list" in b.block_type else "  "
                console.print(f"{prefix}{b.text[:100]}")


# ------------------------------------------------------------------
# notion aurora
# ------------------------------------------------------------------

@notion_app.command(name="aurora")
def cmd_aurora(
    query: str = typer.Argument("leads hoteis publicidade"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Roda Aurora context engine com Notion ativo e mostra contexto retornado."""
    if not os.environ.get("NOTION_TOKEN"):
        console.print("[red]NOTION_TOKEN nao configurado.[/red]")
        raise typer.Exit(1)

    from src.aurora.context_engine import ContextEngine
    from pathlib import Path

    engine = ContextEngine(data_dir=Path("data"), dry_run=True)
    ctx = engine.build(query=query, max_results_per_source=5)

    if json_out:
        console.print_json(json.dumps(ctx.to_dict(), ensure_ascii=False))
        return

    console.print(f"\n[bold]Aurora Context — query=[/bold][cyan]{query}[/cyan]")
    console.print(f"  Fontes ativas:  {', '.join(ctx.sources_available) or 'nenhuma'}")
    console.print(f"  Fontes falhas:  {', '.join(ctx.sources_failed) or 'nenhuma'}")
    console.print(f"  Resultados:     {len(ctx.results)}")
    console.print()

    notion_results = [r for r in ctx.results if r.source == "notion"]
    if notion_results:
        console.print(f"[green]Notion ({len(notion_results)} itens):[/green]")
        for r in notion_results:
            console.print(f"  - {r.content[:80]}")
    else:
        console.print("[yellow]Notion: 0 resultados (nenhuma pagina compartilhada com o bot)[/yellow]")
        console.print("[dim]  Abra a pagina no Notion -> Share -> Convidar 'OMNIS'[/dim]")

    other_results = [r for r in ctx.results if r.source != "notion"]
    if other_results:
        console.print(f"\n[dim]Outras fontes ({len(other_results)} itens):[/dim]")
        for r in other_results[:5]:
            console.print(f"  [{r.source}] {r.content[:60]}...")
