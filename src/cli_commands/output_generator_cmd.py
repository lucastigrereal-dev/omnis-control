"""CLI commands for Output Generator — P10.0."""
from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from src.output_generator import (
    OutputGeneratorRegistry,
    OutputWriterService,
    select_generator,
)
from src.output_generator.errors import GeneratorNotFoundError

output_generator_app = typer.Typer(
    name="output-generator",
    help="Output Generator — deterministic local writers. NUNCA chama LLM/rede.",
    add_completion=False,
)
console = Console()


@output_generator_app.command(name="list")
def cmd_list() -> None:
    """Lista todos os generators registrados."""
    reg = OutputGeneratorRegistry()
    generators = reg.list_all()

    if not generators:
        console.print("[dim]Nenhum generator registrado.[/dim]")
        return

    table = Table(title=f"Output Generators ({len(generators)})")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Types")
    table.add_column("Risk")
    table.add_column("Status")

    for g in generators:
        status_style = "[green]active[/green]" if g.status.value == "active" else "[yellow]planned[/yellow]"
        types_str = ", ".join(g.output_types)
        table.add_row(g.generator_id, g.name, types_str, g.risk_level, status_style)

    console.print(table)


@output_generator_app.command(name="show")
def cmd_show(
    generator_id: str = typer.Argument(..., help="Generator ID"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
) -> None:
    """Mostra detalhes de um generator."""
    reg = OutputGeneratorRegistry()
    try:
        gen = reg.get(generator_id)
    except GeneratorNotFoundError:
        console.print(f"[red]Generator '{generator_id}' nao encontrado.[/red]")
        raise typer.Exit(1)

    if json_output:
        print(json.dumps({
            "generator_id": gen.generator_id,
            "name": gen.name,
            "output_types": gen.output_types,
            "mode": gen.mode,
            "risk_level": gen.risk_level,
            "status": gen.status.value,
            "description": gen.description,
        }, indent=2, ensure_ascii=False))
        return

    console.print(f"[bold]Generator:[/bold] {gen.generator_id}")
    console.print(f"  Name: {gen.name}")
    console.print(f"  Status: {gen.status.value}")
    console.print(f"  Mode: {gen.mode}")
    console.print(f"  Risk: {gen.risk_level}")
    console.print(f"  Output types: {', '.join(gen.output_types)}")
    console.print(f"  Description: {gen.description}")


@output_generator_app.command(name="select")
def cmd_select(
    output_type: str = typer.Argument(..., help="Output type (markdown, json, app_spec, etc)"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
) -> None:
    """Seleciona generator para um output type."""
    result = select_generator(output_type)

    if json_output:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        return

    status_map = {
        "selected": "[green]SELECTED[/green]",
        "no_generator": "[red]NO_GENERATOR[/red]",
        "planned_only": "[yellow]PLANNED_ONLY[/yellow]",
        "blocked": "[red]BLOCKED[/red]",
    }
    console.print(f"[bold]Output type:[/bold] {output_type}")
    console.print(f"  Status: {status_map.get(result.status, result.status)}")
    if result.selected_generator_id:
        console.print(f"  Generator: {result.selected_generator_id}")
    if result.warnings:
        for w in result.warnings:
            console.print(f"  [yellow]WARN: {w}[/yellow]")
    if result.blockers:
        for b in result.blockers:
            console.print(f"  [red]BLOCKED: {b}[/red]")


@output_generator_app.command(name="write-markdown")
def cmd_write_markdown(
    work_order_id: str = typer.Argument(..., help="Work Order ID"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
) -> None:
    """Gera output markdown deterministico para um work order."""
    try:
        service = OutputWriterService()
        result = service.write(work_order_id)
    except FileNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)

    status_map = {
        "generated": "[green]GENERATED[/green]",
        "blocked": "[red]BLOCKED[/red]",
        "failed": "[red]FAILED[/red]",
        "unsupported": "[yellow]UNSUPPORTED[/yellow]",
    }

    if json_output:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        return

    console.print(f"[bold]Markdown output[/bold] {status_map.get(result.status, result.status)}")
    console.print(f"  output_id:     {result.output_id}")
    console.print(f"  work_order_id: {result.work_order_id}")
    console.print(f"  generator_id:  {result.generator_id}")
    console.print(f"  file_path:     {result.file_path}")
    console.print(f"  fingerprint:   {result.fingerprint}")
    if result.warnings:
        for w in result.warnings:
            console.print(f"  [yellow]WARN: {w}[/yellow]")
    if result.blockers:
        for b in result.blockers:
            console.print(f"  [red]BLOCKED: {b}[/red]")
    console.print(f"  [dim]next_action: submit to work-order collector in P10.4[/dim]")
