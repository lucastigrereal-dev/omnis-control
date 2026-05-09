"""CLI for Role Registry."""
from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

role_registry_app = typer.Typer(
    name="role-registry",
    help="Role Registry — lista e consulta papéis operacionais do OMNIS.",
    add_completion=False,
)
console = Console()


@role_registry_app.callback()
def _callback():
    """Role Registry — papéis de planejamento para squads locais."""


@role_registry_app.command(name="list")
def cmd_list(
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Lista todos os papéis registrados."""
    from src.role_registry import loader as loader_mod
    from src.role_registry.matcher import list_all_roles

    roles = list_all_roles(loader_mod.DEFAULT_ROLES_PATH)

    if json_out:
        data = [
            {"role_id": r.role_id, "name": r.name, "sectors": r.sectors,
             "risk_level": r.risk_level, "outputs": r.outputs}
            for r in roles
        ]
        console.print_json(json.dumps(data, ensure_ascii=False))
        return

    if not roles:
        console.print("[dim]Nenhum role encontrado.[/dim]")
        return

    table = Table(title="Role Registry")
    table.add_column("role_id", style="dim")
    table.add_column("name")
    table.add_column("sectors")
    table.add_column("risk")
    for r in roles:
        color = {"low": "white", "medium": "yellow", "high": "red"}.get(r.risk_level, "white")
        table.add_row(r.role_id, r.name, ", ".join(r.sectors), f"[{color}]{r.risk_level}[/{color}]")
    console.print(table)


@role_registry_app.command(name="show")
def cmd_show(
    role_id: str = typer.Argument(..., help="ID do role"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Mostra detalhes de um role."""
    from src.role_registry import loader as loader_mod
    from src.role_registry.matcher import get_role
    from src.role_registry.errors import RoleNotFoundError

    try:
        role = get_role(role_id, config_path=loader_mod.DEFAULT_ROLES_PATH)
    except RoleNotFoundError as e:
        console.print(f"[red]Erro: {e}[/red]")
        raise typer.Exit(1)

    if json_out:
        data = {
            "role_id": role.role_id, "name": role.name, "sectors": role.sectors,
            "responsibilities": role.responsibilities, "outputs": role.outputs,
            "risk_level": role.risk_level,
        }
        console.print_json(json.dumps(data, ensure_ascii=False))
        return

    console.print(Panel(f"[bold]Role[/bold] — {role.role_id}", expand=False))
    console.print(f"  name            : {role.name}")
    console.print(f"  sectors         : {', '.join(role.sectors)}")
    console.print(f"  risk            : {role.risk_level}")
    console.print(f"  outputs         : {', '.join(role.outputs)}")
    console.print(f"  responsibilities:")
    for r in role.responsibilities:
        console.print(f"    - {r}")


@role_registry_app.command(name="match")
def cmd_match(
    sector: str = typer.Option(None, "--sector", help="Filtrar por setor"),
    output: str = typer.Option(None, "--output", help="Filtrar por output"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Encontra roles por setor ou output esperado."""
    from src.role_registry import loader as loader_mod
    from src.role_registry.matcher import match_roles_by_sector, match_roles_by_output

    if not sector and not output:
        console.print("[yellow]Forneça --sector ou --output.[/yellow]")
        raise typer.Exit(1)

    if sector:
        results = match_roles_by_sector(sector, config_path=loader_mod.DEFAULT_ROLES_PATH)
        label = f"sector='{sector}'"
    else:
        results = match_roles_by_output(output, config_path=loader_mod.DEFAULT_ROLES_PATH)
        label = f"output='{output}'"

    if json_out:
        data = [
            {"role_id": r.role_id, "name": r.name, "reason": r.reason, "risk_level": r.risk_level}
            for r in results
        ]
        console.print_json(json.dumps(data, ensure_ascii=False))
        return

    if not results:
        console.print(f"[dim]Nenhum role para {label}.[/dim]")
        return

    table = Table(title=f"Roles — {label}")
    table.add_column("role_id", style="dim")
    table.add_column("name")
    table.add_column("risk")
    table.add_column("reason")
    for r in results:
        color = {"low": "white", "medium": "yellow", "high": "red"}.get(r.risk_level, "white")
        table.add_row(r.role_id, r.name, f"[{color}]{r.risk_level}[/{color}]", r.reason)
    console.print(table)
