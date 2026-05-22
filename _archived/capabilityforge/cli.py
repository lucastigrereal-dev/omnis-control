"""CLI da Capability Forge (typer — adaptado de click do source)."""
from __future__ import annotations
import asyncio
import json
import typer
from typing import Optional

from .orchestrator import CapabilityForge
from .registrymanager import RegistryManager

forge = CapabilityForge()
registry = RegistryManager()

forge_app = typer.Typer(
    name="forge",
    help="Capability Forge — fabrica governada de skills",
    add_completion=False,
)


@forge_app.command(name="propose")
def propose(
    gap: str = typer.Argument(..., help="Descricao da lacuna/necessidade"),
    sector: str = typer.Option(..., "--sector", help="Setor: marketing, sales, operations..."),
    name: str = typer.Option("", "--name", help="Nome sugerido para a skill"),
):
    """Detecta gap e propoe spec de nova skill."""
    result = asyncio.run(forge.propose_skill(gap, sector, name))
    typer.echo(json.dumps(result, indent=2, ensure_ascii=False))


@forge_app.command(name="approve")
def approve(
    name: str = typer.Argument(..., help="Nome da skill"),
    approver: str = typer.Option("lucas", "--approver", help="Identificacao do aprovador"),
):
    """Aprova uma skill gerada para status 'approved'."""
    result = asyncio.run(forge.approve_skill(name, approver))
    typer.echo(json.dumps(result, indent=2, ensure_ascii=False))


@forge_app.command(name="list")
def list_skills(
    status: Optional[str] = typer.Option(None, "--status", help="Filtrar por status"),
    sector: Optional[str] = typer.Option(None, "--sector", help="Filtrar por setor"),
):
    """Lista skills no registry."""
    if status:
        skills = registry.list_by_status(status)
    elif sector:
        skills = registry.list_by_sector(sector)
    else:
        skills = registry._load_all()
    typer.echo(json.dumps(skills, indent=2, ensure_ascii=False, default=str))


@forge_app.command(name="audit")
def audit(
    name: str = typer.Argument(..., help="Nome da skill"),
):
    """Executa policy check em uma skill do registry."""
    from pathlib import Path
    from .policy import PolicyEngine
    entry = registry.get(name)
    if not entry:
        typer.echo(f"Skill '{name}' nao encontrada.")
        return
    engine = PolicyEngine()
    report = engine.check_file(Path(entry["path"]) / "run.py") if entry.get("path") else None
    if report:
        typer.echo(report.summary())
    else:
        typer.echo("Sem arquivo run.py para auditar.")
