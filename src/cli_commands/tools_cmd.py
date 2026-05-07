"""CLI commands para Tool Registry — P0.8."""
from __future__ import annotations

import json
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.tool_registry.registry import ToolRegistry
from src.tool_registry.discovery import discover_known_tools
from src.tool_registry.errors import ToolRegistryError

tools_app = typer.Typer(
    name="tools",
    help="Tool Registry — catalogo de ferramentas e conectores do OMNIS",
    add_completion=False,
)
console = Console()


def _repo() -> ToolRegistry:
    return ToolRegistry()


def _status_style(status: str) -> str:
    return {
        "automatic": "[green]",
        "semi_automatic": "[green]",
        "dry_run": "[blue]",
        "read_only": "[cyan]",
        "manual": "[yellow]",
        "not_configured": "[dim]",
        "blocked": "[red]",
        "deprecated": "[red][dim]",
    }.get(status, "")


def _status_label(status: str) -> str:
    style = _status_style(status)
    return f"{style}{status}[/]"


# ── Commands ────────────────────────────────────────────────────────


@tools_app.command(name="discover")
def tools_discover(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Descobre ferramentas conhecidas e popula o registry.

    Read-only. Nao le .env, nao chama API externa.
    Ferramentas ja registradas sao puladas (sem duplicatas).
    """
    registry = _repo()
    discovered = discover_known_tools()
    added = 0
    skipped = 0
    results = []

    for tool in discovered:
        if registry.get_tool(tool.tool_id):
            skipped += 1
            results.append({"tool_id": tool.tool_id, "action": "skipped"})
        else:
            registry.add_tool(tool)
            added += 1
            results.append({"tool_id": tool.tool_id, "action": "added"})

    if json_output:
        print(json.dumps({
            "added": added,
            "skipped": skipped,
            "total_discovered": len(discovered),
            "results": results,
        }, indent=2, ensure_ascii=False))
    else:
        console.print(f"[green]Discovery concluido![/green]")
        console.print(f"  Adicionadas: {added}")
        console.print(f"  Puladas (ja existem): {skipped}")
        console.print(f"  Total descoberto: {len(discovered)}")


@tools_app.command(name="list")
def tools_list(
    status: Optional[str] = typer.Option(None, "--status", help="Filtrar por status"),
    category: Optional[str] = typer.Option(None, "--category", help="Filtrar por categoria"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Lista ferramentas registradas."""
    registry = _repo()
    tools = registry.list_tools(status=status, category=category)

    if json_output:
        data = [t.model_dump() for t in tools]
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    if not tools:
        console.print("Nenhuma ferramenta registrada. Execute 'tools discover' primeiro.")
        return

    title = "Ferramentas"
    if status:
        title += f" (status={status})"
    if category:
        title += f" (category={category})"

    table = Table(title=f"{title} — {len(tools)}")
    table.add_column("Tool ID", style="cyan", no_wrap=True)
    table.add_column("Nome")
    table.add_column("Cat.")
    table.add_column("Status")
    table.add_column("Risco")

    for t in tools:
        table.add_row(
            t.tool_id,
            t.name[:30],
            t.category[:10],
            _status_label(t.status),
            t.risk_level,
        )
    console.print(table)


@tools_app.command(name="show")
def tools_show(
    tool_id: str = typer.Argument(..., help="Tool ID"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Mostra detalhes de uma ferramenta."""
    registry = _repo()
    tool = registry.get_tool(tool_id)

    if tool is None:
        console.print(f"[red]Ferramenta '{tool_id}' nao encontrada.[/red]")
        raise typer.Exit(1)

    if json_output:
        print(tool.model_dump_json(indent=2))
        return

    console.print(f"[bold]Ferramenta: {tool.name}[/bold]")
    console.print(f"  Tool ID: [cyan]{tool.tool_id}[/cyan]")
    console.print(f"  Status: {_status_label(tool.status)}")
    console.print(f"  Categoria: {tool.category}")
    console.print(f"  Risco: {tool.risk_level}")
    console.print(f"  Descricao: {tool.description}")

    if tool.capabilities:
        console.print(f"\n  Capabilities:")
        for c in tool.capabilities:
            console.print(f"    - {c}")

    if tool.required_credentials:
        console.print(f"\n  Credenciais necessarias:")
        for c in tool.required_credentials:
            console.print(f"    - [yellow]{c}[/yellow]")

    if tool.available_commands:
        console.print(f"\n  Comandos disponiveis:")
        for c in tool.available_commands:
            console.print(f"    - {c}")

    if tool.used_by_modules:
        console.print(f"\n  Usado por modulos:")
        for m in tool.used_by_modules:
            console.print(f"    - [dim]{m}[/dim]")

    if tool.config_paths:
        console.print(f"\n  Config paths:")
        for p in tool.config_paths:
            console.print(f"    - [dim]{p}[/dim]")

    if tool.limitations:
        console.print(f"\n  [yellow]Limitacoes:[/yellow]")
        for l in tool.limitations:
            console.print(f"    - {l}")

    if tool.next_action:
        console.print(f"\n  [bold]Proximo passo:[/bold] {tool.next_action}")

    if tool.healthcheck:
        console.print(f"\n  Healthcheck: [dim]{tool.healthcheck}[/dim]")

    if tool.validation_status:
        console.print(f"\n  Validacao: {tool.validation_status}")


@tools_app.command(name="status")
def tools_status(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Resumo do Tool Registry — status e categorias."""
    registry = _repo()
    by_status = registry.tools_by_status()
    by_category = registry.tools_by_category()
    total = sum(by_status.values())

    if json_output:
        print(json.dumps({
            "total": total,
            "by_status": by_status,
            "by_category": by_category,
        }, indent=2, ensure_ascii=False))
        return

    if total == 0:
        console.print("Tool Registry vazio. Execute 'tools discover' primeiro.")
        return

    console.print(f"[bold]Tool Registry[/bold] — {total} ferramentas\n")

    console.print("[bold]Por status:[/bold]")
    for st in [ToolStatus.BLOCKED, ToolStatus.NOT_CONFIGURED, ToolStatus.MANUAL,
               ToolStatus.DRY_RUN, ToolStatus.READ_ONLY, ToolStatus.SEMI_AUTOMATIC,
               ToolStatus.AUTOMATIC, ToolStatus.DEPRECATED]:
        count = by_status.get(st, 0)
        if count > 0:
            console.print(f"  {_status_label(st):<35} {count}")

    console.print(f"\n[bold]Por categoria:[/bold]")
    for cat, count in sorted(by_category.items()):
        console.print(f"  {cat:<20} {count}")


@tools_app.command(name="update-status")
def tools_update_status(
    tool_id: str = typer.Argument(..., help="Tool ID"),
    new_status: str = typer.Argument(..., help="Novo status"),
    validation_status: Optional[str] = typer.Option(None, "--validation", help="Status de validacao"),
    notes: Optional[str] = typer.Option(None, "--notes", help="Notas sobre a mudanca"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Atualiza o status de uma ferramenta.

    Registra mudanca no validation_log.
    """
    registry = _repo()

    try:
        result = registry.update_status(
            tool_id,
            status=new_status,
            validation_status=validation_status,
            notes=notes,
        )
    except ToolRegistryError as e:
        console.print(f"[red]Erro: {e}[/red]")
        raise typer.Exit(1)

    if result is None:
        console.print(f"[red]Ferramenta '{tool_id}' nao encontrada.[/red]")
        raise typer.Exit(1)

    if json_output:
        print(result.model_dump_json(indent=2))
    else:
        console.print(f"[green]Status atualizado![/green]")
        console.print(f"  {tool_id}: {new_status}")


# Import ToolStatus for the status command ordering
from src.tool_registry.models import ToolStatus
