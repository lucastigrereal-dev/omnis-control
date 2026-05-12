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
from src.output_generator.json_writer import write_json_output, write_spec_output
from src.output_generator.manifest_registry import ManifestRegistry
from src.output_generator.validator import validate_package
from src.output_generator.approval_bridge import prepare_submission

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


@output_generator_app.command(name="write-json")
def cmd_write_json(
    work_order_id: str = typer.Argument(..., help="Work Order ID"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
) -> None:
    """Gera output JSON deterministico para um work order."""
    try:
        service = OutputWriterService()
        result = service.write_json(work_order_id)
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

    console.print(f"[bold]JSON output[/bold] {status_map.get(result.status, result.status)}")
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
    console.print(f"  [dim]next_action: package in P10.4[/dim]")


@output_generator_app.command(name="write-csv")
def cmd_write_csv(
    work_order_id: str = typer.Argument(..., help="Work Order ID"),
    table_type: str = typer.Option("list", "--type", "-t", help="Tipo de tabela: list, calendar, queue"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
) -> None:
    """Gera output CSV deterministico para um work order."""
    try:
        service = OutputWriterService()
        result = service.write_csv(work_order_id, table_type=table_type)
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

    console.print(f"[bold]CSV output ({table_type})[/bold] {status_map.get(result.status, result.status)}")
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
    console.print(f"  [dim]next_action: package in P10.4[/dim]")


@output_generator_app.command(name="package")
def cmd_package(
    work_order_id: str = typer.Argument(..., help="Work Order ID"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
) -> None:
    """Gera pacote multi-file para um work order (md + json + csv + manifest)."""
    try:
        service = OutputWriterService()
        pkg_dir, outputs, blockers = service.package(work_order_id)
    except FileNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)

    if json_output:
        result = {
            "package_dir": str(pkg_dir),
            "work_order_id": work_order_id,
            "file_count": len(outputs),
            "outputs": [o.to_dict() for o in outputs],
            "blockers": blockers,
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    console.print(f"[bold]Package[/bold] [green]GENERATED[/green]")
    console.print(f"  package_dir:   {pkg_dir}")
    console.print(f"  work_order_id: {work_order_id}")
    console.print(f"  files:         {len(outputs)}")
    for o in outputs:
        status_icon = "[green]OK[/green]" if o.status.value == "generated" else f"[red]{o.status.value.upper()}[/red]"
        console.print(f"    [{o.output_type}] {o.file_path} {status_icon}")
    if blockers:
        for b in blockers:
            console.print(f"  [red]BLOCKED: {b}[/red]")


@output_generator_app.command(name="registry")
def cmd_registry(
    action: str = typer.Argument(..., help="Acao: list, show"),
    output_id: str = typer.Argument(None, help="Output ID (para show)"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
) -> None:
    """Gerencia o registry local de outputs (JSONL)."""
    reg = ManifestRegistry()

    if action == "list":
        entries = reg.list_all()
        if json_output:
            print(json.dumps(entries, indent=2, ensure_ascii=False))
            return
        console.print(f"[bold]Output Registry[/bold] ({len(entries)} entries)")
        for e in entries:
            console.print(f"  {e['output_id']}  [{e['output_type']}]  {e['work_order_id']}  {e['registered_at']}")

    elif action == "show":
        if not output_id:
            console.print("[red]output_id requerido para 'show'[/red]")
            raise typer.Exit(1)
        entry = reg.show(output_id)
        if entry is None:
            console.print(f"[red]Output '{output_id}' nao encontrado no registry.[/red]")
            raise typer.Exit(1)
        if json_output:
            print(json.dumps(entry, indent=2, ensure_ascii=False))
            return
        console.print(f"[bold]Output:[/bold] {entry['output_id']}")
        for k, v in entry.items():
            console.print(f"  {k}: {v}")

    else:
        console.print(f"[red]Acao desconhecida: {action}. Use: list, show[/red]")
        raise typer.Exit(1)


@output_generator_app.command(name="write-spec")
def cmd_write_spec(
    work_order_id: str = typer.Argument(..., help="Work Order ID"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
) -> None:
    """Gera output spec deterministico (technical_spec, app_spec, data_model)."""
    try:
        service = OutputWriterService()
        result = service.write_spec(work_order_id)
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

    console.print(f"[bold]Spec output[/bold] {status_map.get(result.status, result.status)}")
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
    console.print(f"  [dim]next_action: package in P10.4[/dim]")


@output_generator_app.command(name="validate")
def cmd_validate(
    work_order_id: str = typer.Argument(..., help="Work Order ID"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
) -> None:
    """Valida integridade do pacote de output: schema, arquivos, fingerprints."""
    result = validate_package(work_order_id)

    if json_output:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        if not result.valid:
            raise typer.Exit(1)
        return

    if result.valid:
        console.print(f"[bold]Validation[/bold] [green]PASS[/green] for {work_order_id}")
    else:
        console.print(f"[bold]Validation[/bold] [red]FAIL[/red] for {work_order_id}")

    for check in result.checks:
        icon = {"pass": "[green]PASS[/green]", "fail": "[red]FAIL[/red]", "warn": "[yellow]WARN[/yellow]"}.get(check["status"], "?")
        console.print(f"  {icon} {check['name']}: {check['message']}")

    if result.issues:
        for issue in result.issues:
            console.print(f"  [red]ISSUE: {issue}[/red]")
    if result.warnings:
        for warn in result.warnings:
            console.print(f"  [yellow]WARN: {warn}[/yellow]")

    if not result.valid:
        raise typer.Exit(1)


@output_generator_app.command(name="submit-approval")
def cmd_submit_approval(
    work_order_id: str = typer.Argument(..., help="Work Order ID"),
    no_dry_run: bool = typer.Option(False, "--no-dry-run", help="Realmente submeter ao approval_center (default: dry-run)"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
) -> None:
    """Prepara submissao do pacote para o approval_center (dry-run por default)."""
    submission = prepare_submission(work_order_id, dry_run=not no_dry_run)

    if json_output:
        print(json.dumps(submission, indent=2, ensure_ascii=False))
        return

    mode = "[yellow]DRY-RUN[/yellow]" if submission["dry_run"] else "[green]SUBMITTED[/green]"
    valid_icon = "[green]PASS[/green]" if submission["valid"] else "[red]FAIL[/red]"

    console.print(f"[bold]Approval Submission[/bold] {mode}")
    console.print(f"  Validation:   {valid_icon}")
    console.print(f"  Work Order:   {submission['work_order_id']}")
    console.print(f"  Files:        {submission['file_count']}")
    console.print(f"  Output types: {', '.join(submission['output_types'])}")

    if submission["approval_request"]:
        ar = submission["approval_request"]
        console.print(f"  Approval ID:  {ar['request_id']}")
        console.print(f"  Status:       {ar['status']}")
        console.print(f"  Requested at: {ar['requested_at']}")

    if submission["issues"]:
        for issue in submission["issues"]:
            console.print(f"  [red]ISSUE: {issue}[/red]")
    if submission["warnings"]:
        for warn in submission["warnings"]:
            console.print(f"  [yellow]WARN: {warn}[/yellow]")

    if not submission["valid"]:
        raise typer.Exit(1)
