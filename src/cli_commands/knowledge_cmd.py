"""CLI for Knowledge + Context Pack — P2.9. NUNCA publica."""
from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.table import Table

knowledge_app = typer.Typer(
    name="knowledge",
    help="Knowledge + Context Pack — gestao de conhecimento e contexto. NUNCA publica.",
    add_completion=False,
)
console = Console()


@knowledge_app.callback()
def _callback():
    """Knowledge + Context Pack — gestao de conhecimento local."""


# ── Knowledge Packs ──────────────────────────────────────────────────────────

@knowledge_app.command(name="pack-create")
def cmd_pack_create(
    name: str = typer.Argument(..., help="Nome do pack"),
    description: str = typer.Option("", "--description", help="Descricao do pack"),
    tags: str = typer.Option("", "--tags", help="Tags separadas por virgula"),
    json_out: bool = typer.Option(False, "--json", help="Saida em JSON"),
) -> None:
    """Cria um novo Knowledge Pack."""
    from src.knowledge_context.service import create_pack, ValidationError

    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    try:
        pack = create_pack(name=name, description=description, tags=tag_list)
    except ValidationError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)

    if json_out:
        console.print_json(json.dumps(pack.to_dict(), ensure_ascii=False))
        return
    console.print(f"[green]Pack criado[/green] — {pack.pack_id}")
    console.print(f"  Nome: {pack.name}")
    if pack.tags:
        console.print(f"  Tags: {', '.join(pack.tags)}")


@knowledge_app.command(name="pack-entry-add")
def cmd_pack_entry_add(
    pack_id: str = typer.Argument(..., help="ID (ou prefixo) do pack"),
    title: str = typer.Option(..., "--title", help="Titulo da entrada"),
    content: str = typer.Option(..., "--content", help="Conteudo da entrada"),
    source: str = typer.Option("manual", "--source", help="manual | akasha | library"),
    tags: str = typer.Option("", "--tags", help="Tags separadas por virgula"),
    json_out: bool = typer.Option(False, "--json", help="Saida em JSON"),
) -> None:
    """Adiciona uma entrada a um Knowledge Pack."""
    from src.knowledge_context.service import add_entry, PackNotFoundError

    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    try:
        pack = add_entry(pack_id=pack_id, title=title, content=content, source=source, tags=tag_list)
    except PackNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)

    if json_out:
        console.print_json(json.dumps(pack.to_dict(), ensure_ascii=False))
        return
    console.print(f"[green]Entrada adicionada[/green] — Pack {pack.pack_id[:10]}: {pack.entry_count()} entradas")


@knowledge_app.command(name="pack-list")
def cmd_pack_list(
    tag: str = typer.Option(None, "--tag", help="Filtrar por tag"),
    json_out: bool = typer.Option(False, "--json", help="Saida em JSON"),
) -> None:
    """Lista Knowledge Packs."""
    from src.knowledge_context.service import list_packs

    packs = list_packs(tag=tag)
    if json_out:
        console.print_json(json.dumps([p.to_dict() for p in packs], ensure_ascii=False))
        return
    if not packs:
        console.print("[yellow]Nenhum pack encontrado.[/yellow]")
        return
    table = Table(title=f"Knowledge Packs ({len(packs)})")
    table.add_column("ID", style="cyan")
    table.add_column("Nome")
    table.add_column("Entradas", justify="right")
    table.add_column("Tags")
    for p in packs:
        table.add_row(p.pack_id[:12], p.name, str(p.entry_count()), ", ".join(p.tags[:3]))
    console.print(table)


@knowledge_app.command(name="pack-show")
def cmd_pack_show(
    pack_id: str = typer.Argument(..., help="ID (ou prefixo) do pack"),
    json_out: bool = typer.Option(False, "--json", help="Saida em JSON"),
) -> None:
    """Mostra detalhes de um Knowledge Pack."""
    from src.knowledge_context.service import get_pack, PackNotFoundError

    try:
        pack = get_pack(pack_id)
    except PackNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)

    if json_out:
        console.print_json(json.dumps(pack.to_dict(), ensure_ascii=False))
        return
    console.print(f"[bold]Pack:[/bold] {pack.name} ({pack.pack_id})")
    console.print(f"  {pack.description}")
    console.print(f"  Entradas: {pack.entry_count()} | Tags: {', '.join(pack.tags) or 'nenhuma'}")
    for e in pack.entries[:5]:
        console.print(f"  - [{e.source}] {e.title[:50]}")
    if pack.entry_count() > 5:
        console.print(f"  ... e mais {pack.entry_count() - 5}")


# ── Context Packs ─────────────────────────────────────────────────────────────

@knowledge_app.command(name="context-set")
def cmd_context_set(
    account: str = typer.Argument(..., help="Handle Instagram"),
    display_name: str = typer.Option(..., "--display-name", help="Nome de exibicao"),
    tone: str = typer.Option("casual", "--tone", help="Tom: formal|casual|inspiracional"),
    language: str = typer.Option("pt-BR", "--language", help="Idioma"),
    topics: str = typer.Option("", "--topics", help="Topicos separados por virgula"),
    json_out: bool = typer.Option(False, "--json", help="Saida em JSON"),
) -> None:
    """Define ou atualiza o contexto de uma conta."""
    from src.knowledge_context.service import set_context

    topic_list = [t.strip() for t in topics.split(",") if t.strip()] if topics else None
    ctx = set_context(
        account_handle=account,
        display_name=display_name,
        tone=tone,
        language=language,
        topics=topic_list,
    )
    if json_out:
        console.print_json(json.dumps(ctx.to_dict(), ensure_ascii=False))
        return
    console.print(f"[green]Contexto salvo[/green] — @{ctx.account_handle}")
    console.print(f"  {ctx.display_name} | {ctx.tone} | {ctx.language}")


@knowledge_app.command(name="context-fact-set")
def cmd_context_fact_set(
    account: str = typer.Argument(..., help="Handle Instagram"),
    key: str = typer.Option(..., "--key", help="Chave do fato"),
    value: str = typer.Option(..., "--value", help="Valor do fato"),
    category: str = typer.Option("general", "--category", help="Categoria"),
) -> None:
    """Define ou atualiza um fato no contexto de uma conta."""
    from src.knowledge_context.service import set_context_fact, ContextNotFoundError

    try:
        ctx = set_context_fact(account, key=key, value=value, category=category)
    except ContextNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)
    console.print(f"[green]Fato salvo[/green] — @{ctx.account_handle}: {key}={value}")


@knowledge_app.command(name="context-get")
def cmd_context_get(
    account: str = typer.Argument(..., help="Handle Instagram"),
    json_out: bool = typer.Option(False, "--json", help="Saida em JSON"),
) -> None:
    """Mostra o contexto de uma conta."""
    from src.knowledge_context.service import get_context, ContextNotFoundError

    try:
        ctx = get_context(account)
    except ContextNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)

    if json_out:
        console.print_json(json.dumps(ctx.to_dict(), ensure_ascii=False))
        return
    console.print(f"[bold]Contexto:[/bold] @{ctx.account_handle} — {ctx.display_name}")
    console.print(f"  Tom: {ctx.tone} | Idioma: {ctx.language}")
    if ctx.topics:
        console.print(f"  Topicos: {', '.join(ctx.topics[:5])}")
    if ctx.facts:
        console.print(f"  Fatos ({len(ctx.facts)}):")
        for f in ctx.facts[:5]:
            console.print(f"    [{f.category}] {f.key}: {f.value[:60]}")


@knowledge_app.command(name="context-list")
def cmd_context_list(
    json_out: bool = typer.Option(False, "--json", help="Saida em JSON"),
) -> None:
    """Lista todos os contextos cadastrados."""
    from src.knowledge_context.service import list_contexts

    contexts = list_contexts()
    if json_out:
        console.print_json(json.dumps([c.to_dict() for c in contexts], ensure_ascii=False))
        return
    if not contexts:
        console.print("[yellow]Nenhum contexto cadastrado.[/yellow]")
        return
    table = Table(title=f"Contextos ({len(contexts)})")
    table.add_column("Conta")
    table.add_column("Nome")
    table.add_column("Tom")
    table.add_column("Fatos", justify="right")
    for c in contexts:
        table.add_row(f"@{c.account_handle}", c.display_name, c.tone, str(len(c.facts)))
    console.print(table)
