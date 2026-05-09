"""CLI for Asset Inbox — read-only real asset scanner. NUNCA importa ou move."""
from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

asset_inbox_app = typer.Typer(
    name="asset-inbox",
    help="Asset Inbox — scanner read-only de assets reais. NUNCA importa ou move arquivos.",
    add_completion=False,
)
console = Console()


@asset_inbox_app.callback()
def _callback():
    """Asset Inbox — escaneia arquivos locais (read-only). Nenhum arquivo e alterado."""


@asset_inbox_app.command(name="scan")
def cmd_scan(
    path: str = typer.Argument(..., help="Caminho para escanear (diretorio ou arquivo)"),
    limit: int = typer.Option(500, "--limit", help="Maximo de arquivos (default 500)"),
    exclude: list[str] = typer.Option([], "--exclude", help="Nomes de pasta para ignorar"),
    json_out: bool = typer.Option(False, "--json", help="Saida em JSON"),
) -> None:
    """Escaneia caminho localmente (read-only). Nenhum arquivo e movido, copiado ou apagado."""
    from src.asset_inbox.scanner import scan as do_scan
    from src.asset_inbox.errors import AssetInboxScanError, PathTraversalError
    from src.asset_inbox.models import STATUS_CANDIDATE

    root = Path(path)
    extra_exclude = set(exclude) if exclude else None

    try:
        result = do_scan(root, limit=limit, exclude=extra_exclude)
    except PathTraversalError as exc:
        console.print(f"[red]Path traversal bloqueado: {exc}[/red]")
        raise typer.Exit(1)
    except AssetInboxScanError as exc:
        console.print(f"[red]Erro no scan: {exc}[/red]")
        raise typer.Exit(1)

    if json_out:
        console.print_json(json.dumps(result.to_dict(), ensure_ascii=False))
        return

    console.print(Panel("[bold]Asset Inbox Scan[/bold]", expand=False))
    console.print(f"  Root path      : {result.root_path}")
    console.print(f"  Supported files: [green]{result.total_supported}[/green]")
    console.print(f"  Ignored files  : [dim]{result.total_ignored}[/dim]")
    console.print(f"  Too large      : [yellow]{result.total_too_large}[/yellow]")
    console.print(f"  Total size     : {_fmt_bytes(result.total_size_bytes)}")

    candidates = [i for i in result.items if i.status == STATUS_CANDIDATE]
    if candidates:
        console.print(f"\n  [bold]Top {min(10, len(candidates))} candidatos:[/bold]")
        for item in candidates[:10]:
            console.print(f"    [{item.media_type[:3].upper()}] {item.file_name}  {_fmt_bytes(item.size_bytes)}")

    if result.warnings:
        console.print("\n  [yellow]Avisos:[/yellow]")
        for w in result.warnings:
            console.print(f"    - {w}")

    console.print(f"\n  [dim]Proximo passo: B8B Safe Import Registry[/dim]")


def _fmt_bytes(n: int) -> str:
    if n >= 1024 ** 3:
        return f"{n / 1024 ** 3:.1f} GB"
    if n >= 1024 ** 2:
        return f"{n / 1024 ** 2:.1f} MB"
    if n >= 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n} B"
