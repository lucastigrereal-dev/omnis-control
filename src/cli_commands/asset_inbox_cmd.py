"""CLI for Asset Inbox — scanner + safe import registry. NUNCA move original."""
from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

asset_inbox_app = typer.Typer(
    name="asset-inbox",
    help="Asset Inbox — scanner + importacao segura de assets. NUNCA move original.",
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

    console.print(f"\n  [dim]Proximo passo: asset-inbox import <path>[/dim]")


@asset_inbox_app.command(name="import")
def cmd_import(
    path: str = typer.Argument(..., help="Caminho do arquivo a importar"),
    json_out: bool = typer.Option(False, "--json", help="Saida em JSON"),
) -> None:
    """Importa COPIA segura do arquivo para storage local. NUNCA move ou modifica original."""
    from src.asset_inbox import importer as imp_mod

    result = imp_mod.import_asset(
        source_path=path,
        storage_root=imp_mod.DEFAULT_STORAGE_ROOT,
        registry_path=imp_mod.DEFAULT_REGISTRY_PATH,
    )

    if json_out:
        console.print_json(json.dumps(result.to_dict(), ensure_ascii=False))
        return

    status_color = {"imported": "green", "duplicate": "yellow"}.get(result.status, "red")
    console.print(Panel("[bold]Asset Import[/bold]", expand=False))
    console.print(f"  Status     : [{status_color}]{result.status}[/{status_color}]")
    if result.asset:
        console.print(f"  asset_id   : {result.asset.asset_id}")
        console.print(f"  source     : {result.asset.source_path}")
        console.print(f"  stored     : {result.asset.stored_path}")
        console.print(f"  fp_match   : {result.asset.fingerprint_match}")
        console.print(f"  size       : {_fmt_bytes(result.asset.size_bytes)}")
    if result.blockers:
        for b in result.blockers:
            console.print(f"  [red]BLOCKER: {b}[/red]")
    if result.warnings:
        for w in result.warnings:
            console.print(f"  [yellow]WARNING: {w}[/yellow]")
    console.print(f"\n  [dim]Proximo passo: B8C Assign Imported Asset → Package READY[/dim]")


@asset_inbox_app.command(name="list")
def cmd_list(
    limit: int = typer.Option(20, "--limit", help="Maximo de registros"),
    json_out: bool = typer.Option(False, "--json", help="Saida em JSON"),
) -> None:
    """Lista assets importados no registry."""
    from src.asset_inbox import registry as reg_mod

    reg = reg_mod.AssetInboxRegistry(reg_mod.DEFAULT_REGISTRY_PATH)
    assets = reg.list()[:limit]

    if json_out:
        console.print_json(json.dumps([a.to_dict() for a in assets], ensure_ascii=False))
        return

    if not assets:
        console.print("[dim]Nenhum asset importado ainda.[/dim]")
        return

    table = Table(title="Imported Assets")
    table.add_column("asset_id", style="dim")
    table.add_column("file_name")
    table.add_column("type")
    table.add_column("size")
    table.add_column("status")
    table.add_column("importado")
    for a in assets:
        color = "green" if a.status == "imported" else "yellow"
        table.add_row(
            a.asset_id, a.file_name, a.media_type,
            _fmt_bytes(a.size_bytes),
            f"[{color}]{a.status}[/{color}]",
            a.created_at[:10],
        )
    console.print(table)


@asset_inbox_app.command(name="show")
def cmd_show(
    asset_id: str = typer.Argument(..., help="ID do asset (ex: ai_abc123...)"),
    json_out: bool = typer.Option(False, "--json", help="Saida em JSON"),
) -> None:
    """Mostra detalhes de um asset importado."""
    from src.asset_inbox import registry as reg_mod

    reg = reg_mod.AssetInboxRegistry(reg_mod.DEFAULT_REGISTRY_PATH)
    asset = reg.get(asset_id)
    if asset is None:
        console.print(f"[yellow]Asset {asset_id} nao encontrado no registry.[/yellow]")
        raise typer.Exit(1)

    if json_out:
        console.print_json(json.dumps(asset.to_dict(), ensure_ascii=False))
        return

    console.print(Panel(f"[bold]Asset[/bold] — {asset.asset_id}", expand=False))
    console.print(f"  file_name  : {asset.file_name}")
    console.print(f"  type       : {asset.media_type}")
    console.print(f"  size       : {_fmt_bytes(asset.size_bytes)}")
    console.print(f"  source     : {asset.source_path}")
    console.print(f"  stored     : {asset.stored_path}")
    console.print(f"  fp_match   : {asset.fingerprint_match}")
    console.print(f"  status     : {asset.status}")
    console.print(f"  importado  : {asset.created_at}")


def _fmt_bytes(n: int) -> str:
    if n >= 1024 ** 3:
        return f"{n / 1024 ** 3:.1f} GB"
    if n >= 1024 ** 2:
        return f"{n / 1024 ** 2:.1f} MB"
    if n >= 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n} B"
