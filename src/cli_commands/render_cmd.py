"""CLI for Render Engine — local HTML preview of offline packages."""
import json
import typer
from rich.console import Console
from rich.table import Table

from src.render_engine.errors import PackageNotFoundError
from src.render_engine.service import render_package, list_renders, get_render

render_app = typer.Typer(name="render", help="Render Engine — gera preview HTML local. NUNCA publica.")
console = Console()


@render_app.command("package")
def cmd_render_package(
    package_id: str = typer.Argument(..., help="ID (ou prefixo) do pacote"),
    json_out: bool = typer.Option(False, "--json", help="Saida em JSON"),
):
    """Gera preview HTML local para um pacote offline."""
    try:
        result = render_package(package_id)
    except PackageNotFoundError as exc:
        console.print(f"[red]Pacote nao encontrado: {exc}[/red]")
        raise typer.Exit(1)
    except Exception as exc:
        console.print(f"[red]Erro: {exc}[/red]")
        raise typer.Exit(1)

    if json_out:
        console.print_json(json.dumps(result.to_dict(), ensure_ascii=False))
        return

    if result.errors:
        console.print(f"[red]FALHOU: {result.errors}[/red]")
        raise typer.Exit(1)

    console.print(f"[green]Render OK[/green] — {result.render_id}")
    console.print(f"  Pacote : {result.package_id}")
    console.print(f"  HTML   : {result.html_path}")
    if result.warnings:
        for w in result.warnings:
            console.print(f"  [yellow]AVISO: {w}[/yellow]")


@render_app.command("list")
def cmd_render_list():
    """Lista renders gerados."""
    renders = list_renders()
    if not renders:
        console.print("[yellow]Nenhum render gerado ainda.[/yellow]")
        return

    table = Table(title="Renders Gerados")
    table.add_column("render_id", style="cyan")
    table.add_column("package_id")
    table.add_column("status", style="green")
    table.add_column("rendered_at")

    for r in renders:
        table.add_row(
            r.get("render_id", ""),
            r.get("package_id", ""),
            r.get("status", ""),
            r.get("rendered_at", "")[:19],
        )
    console.print(table)


@render_app.command("show")
def cmd_render_show(
    render_id: str = typer.Argument(..., help="ID (ou prefixo) do render"),
):
    """Mostra detalhes de um render."""
    entry = get_render(render_id)
    if not entry:
        console.print(f"[red]Render '{render_id}' nao encontrado.[/red]")
        raise typer.Exit(1)
    console.print_json(json.dumps(entry, ensure_ascii=False, indent=2))
