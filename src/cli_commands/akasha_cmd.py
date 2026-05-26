"""CLI 'akasha' — Acesso direto ao Akasha via OMNIS.

Comandos:
    akasha status           — conectividade + row counts por tabela
    akasha search <query>   — busca em 607K+ chunks (FTS + ILIKE)
    akasha memories         — lista memórias OMNIS
    akasha remember <texto> — grava nova memória
    akasha aurora <query>   — roda Aurora com Akasha ativo e mostra contexto

Requer: AKASHA_DB_URL no environment
    Windows: $env:AKASHA_DB_URL = "postgresql://akasha:SENHA@localhost:5432/akasha"
    Linux:   export AKASHA_DB_URL="postgresql://akasha:SENHA@localhost:5432/akasha"
"""
from __future__ import annotations

import json
import os

import typer
from rich.console import Console
from rich.table import Table

akasha_app = typer.Typer(
    name="akasha",
    help="Acesso direto ao Akasha (607K chunks + memorias OMNIS).",
    add_completion=False,
)
console = Console()


def _get_connector():
    from src.akasha_connector.connector import AkashaConnector
    ak = AkashaConnector()
    if not ak.is_available():
        console.print("[red]AKASHA_DB_URL nao configurado.[/red]")
        console.print("  Windows: [cyan]$env:AKASHA_DB_URL = 'postgresql://akasha:SENHA@localhost:5432/akasha'[/cyan]")
        raise typer.Exit(1)
    return ak


# ------------------------------------------------------------------
# akasha status
# ------------------------------------------------------------------

@akasha_app.command(name="status")
def cmd_status(json_out: bool = typer.Option(False, "--json")) -> None:
    """Verifica conectividade e row counts do Akasha."""
    ak = _get_connector()
    st = ak.status()

    if json_out:
        console.print_json(json.dumps(st.to_dict(), ensure_ascii=False))
        return

    if st.connected:
        console.print(f"[green]Akasha ONLINE[/green]")
        console.print(f"  Documentos:       {st.documents:>7,}")
        console.print(f"  Chunks (FTS):     {st.chunks:>7,}")
        console.print(f"  Memorias OMNIS:   {st.omnis_memories:>7,}")
        console.print(f"  Memoria Global:   {st.memoria_global:>7,}")
        console.print(f"  Memoria Projetos: {st.memoria_projetos:>7,}")
    else:
        console.print(f"[red]Akasha OFFLINE — {st.error}[/red]")
        raise typer.Exit(1)


# ------------------------------------------------------------------
# akasha search
# ------------------------------------------------------------------

@akasha_app.command(name="search")
def cmd_search(
    query: str = typer.Argument(..., help="Texto para buscar nos chunks"),
    limit: int = typer.Option(5, "--limit", "-n", help="Max resultados"),
    domain: str = typer.Option("", "--domain", "-d", help="Filtro de dominio (ex: juridico)"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Busca em 607K+ chunks de documentos (FTS tsvector + ILIKE fallback)."""
    ak = _get_connector()
    results = ak.search_chunks(
        query=query,
        max_results=limit,
        domain_filter=domain or None,
    )

    if json_out:
        console.print_json(json.dumps([r.to_dict() for r in results], ensure_ascii=False))
        return

    if not results:
        console.print(f"[yellow]Nenhum resultado para '{query}'.[/yellow]")
        return

    table = Table(title=f"Akasha — {len(results)} chunk(s) para '{query}'")
    table.add_column("Dominio",  style="dim",  width=14)
    table.add_column("Arquivo",  style="cyan", width=22)
    table.add_column("Estrategia", style="dim", width=10)
    table.add_column("Texto",    width=55)

    for r in results:
        table.add_row(
            r.domain[:14],
            r.file_name[:22],
            r.strategy[:10],
            r.chunk_text[:55].replace("\n", " "),
        )

    console.print(table)


# ------------------------------------------------------------------
# akasha memories
# ------------------------------------------------------------------

@akasha_app.command(name="memories")
def cmd_memories(
    limit: int = typer.Option(10, "--limit", "-n"),
    keyword: str = typer.Option("", "--keyword", "-k", help="Filtra por keyword no conteudo"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Lista memorias OMNIS armazenadas no Akasha."""
    ak = _get_connector()
    memories = ak.read_memories(limit=limit, keyword=keyword or None)

    if json_out:
        console.print_json(json.dumps([m.to_dict() for m in memories], ensure_ascii=False))
        return

    if not memories:
        console.print("[yellow]Nenhuma memoria encontrada.[/yellow]")
        return

    table = Table(title=f"Memorias OMNIS ({len(memories)} registros)")
    table.add_column("ID",       style="dim",  width=14)
    table.add_column("Conteudo", style="cyan", width=55)
    table.add_column("Meta",     style="dim",  width=20)
    table.add_column("Data",     style="dim",  width=12)

    for m in memories:
        meta_str = str(m.metadata)[:20] if m.metadata else ""
        table.add_row(
            m.memory_id[:14],
            m.content[:55],
            meta_str,
            m.created_at[:10],
        )

    console.print(table)


# ------------------------------------------------------------------
# akasha remember
# ------------------------------------------------------------------

@akasha_app.command(name="remember")
def cmd_remember(
    content: str = typer.Argument(..., help="Texto da memoria a gravar"),
    memory_id: str = typer.Option("", "--id", help="ID unico (gerado se omitido)"),
    tag: str = typer.Option("", "--tag", help="Tag/tipo da memoria"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Grava uma nova memoria no Akasha (omnis_memories)."""
    ak = _get_connector()

    metadata: dict = {}
    if tag:
        metadata["tipo"] = tag
    metadata["origem"] = "cli_akasha_remember"

    mid = ak.write_memory(
        content=content,
        memory_id=memory_id or None,
        metadata=metadata,
    )

    if json_out:
        console.print_json(json.dumps({"memory_id": mid, "status": "ok" if mid else "error"}, ensure_ascii=False))
        return

    if mid:
        console.print(f"[green]Memoria gravada:[/green] {mid}")
        console.print(f"  Conteudo: {content[:60]}")
    else:
        console.print("[red]Falha ao gravar memoria.[/red]")
        raise typer.Exit(1)


# ------------------------------------------------------------------
# akasha aurora
# ------------------------------------------------------------------

@akasha_app.command(name="aurora")
def cmd_aurora(
    query: str = typer.Argument("OMNIS negocio instagram leads", help="Query para o contexto"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Roda Aurora context engine com Akasha ativo e mostra contexto retornado."""
    if not os.environ.get("AKASHA_DB_URL"):
        console.print("[red]AKASHA_DB_URL nao configurado.[/red]")
        raise typer.Exit(1)

    from src.aurora.context_engine import ContextEngine
    from pathlib import Path

    engine = ContextEngine(data_dir=Path("data"), dry_run=True)
    ctx = engine.build(query=query, max_results_per_source=5)

    if json_out:
        console.print_json(json.dumps(ctx.to_dict(), ensure_ascii=False))
        return

    console.print(f"\n[bold]Aurora Context — query:[/bold] [cyan]{query}[/cyan]")
    console.print(f"  Fontes ativas:  {', '.join(ctx.sources_available) or 'nenhuma'}")
    console.print(f"  Fontes falhas:  {', '.join(ctx.sources_failed) or 'nenhuma'}")
    console.print(f"  Resultados:     {len(ctx.results)}")
    console.print()

    akasha_results = [r for r in ctx.results if r.source == "akasha"]
    if akasha_results:
        console.print(f"[green]Akasha ({len(akasha_results)} chunks):[/green]")
        for r in akasha_results:
            meta = r.metadata
            domain = meta.get("domain", "")
            fname = meta.get("file_name", "")
            # Sanitize para CP1252 (Windows console)
            safe = r.content[:70].encode("cp1252", errors="replace").decode("cp1252")
            console.print(f"  [{domain}/{fname[:20]}] {safe}")
    else:
        console.print("[yellow]Akasha: 0 resultados para este query.[/yellow]")

    other_results = [r for r in ctx.results if r.source != "akasha"]
    if other_results:
        console.print(f"\n[dim]Outras fontes ({len(other_results)} itens):[/dim]")
        for r in other_results[:3]:
            console.print(f"  [{r.source}] {r.content[:60]}...")
