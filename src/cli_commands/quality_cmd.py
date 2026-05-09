"""CLI for Quality Layer — scores offline packages."""
import json
import typer
from rich.console import Console

from src.quality_layer.errors import PackageNotFoundError
from src.quality_layer.models import QualityGrade
from src.quality_layer.service import score_package

quality_app = typer.Typer(name="quality", help="Quality Layer — pontua pacotes offline. NUNCA publica.")
console = Console()


@quality_app.callback()
def _callback():
    """Quality Layer — pontua pacotes offline."""


def _grade_style(grade: QualityGrade) -> str:
    return {
        QualityGrade.READY: "green",
        QualityGrade.NEEDS_ADJUSTMENT: "yellow",
        QualityGrade.BLOCKED: "red",
    }.get(grade, "white")


@quality_app.command("package")
def cmd_quality_package(
    package_id: str = typer.Argument(..., help="ID (ou prefixo) do pacote"),
    json_out: bool = typer.Option(False, "--json", help="Saida em JSON"),
):
    """Pontua qualidade de um pacote offline."""
    try:
        result = score_package(package_id)
    except PackageNotFoundError as exc:
        console.print(f"[red]Pacote nao encontrado: {exc}[/red]")
        raise typer.Exit(1)
    except Exception as exc:
        console.print(f"[red]Erro: {exc}[/red]")
        raise typer.Exit(1)

    if json_out:
        console.print_json(json.dumps(result.to_dict(), ensure_ascii=False))
        return

    style = _grade_style(result.grade)
    console.print(f"[{style}]Score: {result.score}/100 - {result.grade.value}[/{style}]")
    console.print(f"  Pacote: {result.package_id}")

    if result.checks_passed:
        console.print(f"  [green]OK ({len(result.checks_passed)}):[/green] {', '.join(result.checks_passed[:3])}" +
                      (f" ..." if len(result.checks_passed) > 3 else ""))

    if result.checks_failed:
        console.print(f"  [red]FALHOU ({len(result.checks_failed)}):[/red]")
        for c in result.checks_failed:
            console.print(f"    - {c}")

    if result.warnings:
        for w in result.warnings:
            console.print(f"  [yellow]AVISO: {w}[/yellow]")
