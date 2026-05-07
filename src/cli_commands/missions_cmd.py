"""CLI commands para MissionContract + TaskState."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.missions.models import (
    MissionContract,
    BudgetCaps,
    AcceptanceCriterion,
    RiskLevel,
    ApprovalPolicy,
    Sector,
)
from src.missions.repository import JsonlRepository
from src.missions.state_machine import MissionStatus

missions_app = typer.Typer(
    name="mission",
    help="Mission Contract + TaskState — P0.5",
    add_completion=False,
)
console = Console()


def _repo() -> JsonlRepository:
    return JsonlRepository()


def _default_acceptance() -> list[AcceptanceCriterion]:
    return [
        AcceptanceCriterion(
            id="AC-001",
            description="Revisão manual confirma que a missão atende ao objetivo definido.",
            check_type="manual_review",
            check_target="human",
            required=True,
        )
    ]


@missions_app.command(name="create")
def mission_create(
    title: str = typer.Option(..., "--title", help="Título da missão"),
    objective: str = typer.Option(..., "--objective", help="Objetivo da missão"),
    sector: str = typer.Option(..., "--sector", help="Setor (marketing, sales, etc.)"),
    request: Optional[str] = typer.Option(None, "--request", help="Raw user request"),
    risk_level: str = typer.Option("low", "--risk-level", help="low | medium | high | critical"),
    approval_policy: str = typer.Option("none", "--approval", help="none | auto | manual"),
    max_tokens: int = typer.Option(50000, "--max-tokens", help="Budget: max tokens"),
    max_cost: float = typer.Option(2.0, "--max-cost", help="Budget: max cost USD"),
    max_duration: int = typer.Option(600, "--max-duration", help="Budget: max duration (s)"),
    max_steps: int = typer.Option(50, "--max-steps", help="Budget: max steps"),
    tags: Optional[str] = typer.Option(None, "--tags", help="Tags separadas por vírgula"),
    parent: Optional[str] = typer.Option(None, "--parent", help="ID da missão pai"),
    deliverable: Optional[list[str]] = typer.Option(None, "--deliverable", help="Deliverables esperados"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Cria um Mission Contract imutável."""
    try:
        sec = Sector(sector)
    except ValueError:
        secs = [s.value for s in Sector]
        console.print(f"[red]Setor inválido: '{sector}'. Opções: {', '.join(secs)}[/red]")
        raise typer.Exit(1)

    try:
        rl = RiskLevel(risk_level)
    except ValueError:
        console.print(f"[red]Risk level inválido: '{risk_level}'[/red]")
        raise typer.Exit(1)

    try:
        ap = ApprovalPolicy(approval_policy)
    except ValueError:
        console.print(f"[red]Approval policy inválida: '{approval_policy}'[/red]")
        raise typer.Exit(1)

    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    deliverables = list(deliverable) if deliverable else [objective]

    contract = MissionContract(
        title=title,
        objective=objective,
        sector=sec,
        user_request=request or objective,
        risk_level=rl,
        approval_policy=ap,
        budget=BudgetCaps(
            max_tokens=max_tokens,
            max_cost_usd=max_cost,
            max_duration_seconds=max_duration,
            max_steps=max_steps,
        ),
        acceptance_criteria=_default_acceptance(),
        expected_deliverables=deliverables,
        tags=tag_list,
        parent_mission_id=parent,
    )

    repo = _repo()
    mission_id = repo.save_contract(contract)

    if json_output:
        print(json.dumps({
            "mission_id": mission_id,
            "title": contract.title,
            "sector": contract.sector.value,
            "created_at": contract.created_at.isoformat() if hasattr(contract.created_at, "isoformat") else str(contract.created_at),
            "content_hash": contract.content_hash(),
        }, indent=2, ensure_ascii=False))
    else:
        console.print(f"[green]Mission Contract criado![/green]")
        console.print(f"  ID: [cyan]{mission_id}[/cyan]")
        console.print(f"  Título: {title}")
        console.print(f"  Setor: {sector}")
        console.print(f"  Hash: {contract.content_hash()}")


@missions_app.command(name="list")
def mission_list(
    status: Optional[str] = typer.Option(None, "--status", help="Filtrar por status"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Lista todas as missions registradas."""
    repo = _repo()
    missions = repo.list_missions(status=status)

    if json_output:
        data = [
            {
                "mission_id": m.mission_id,
                "title": m.contract_title,
                "sector": m.sector,
                "status": m.status.value,
                "last_updated": m.last_updated.isoformat() if hasattr(m.last_updated, "isoformat") else str(m.last_updated),
            }
            for m in missions
        ]
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    if not missions:
        console.print("Nenhuma mission encontrada.")
        return

    table = Table(title=f"Missions ({len(missions)})")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Título")
    table.add_column("Setor")
    table.add_column("Status")
    table.add_column("Atualizado")

    status_icons = {
        MissionStatus.DRAFT: "[dim][DRAFT][/dim]",
        MissionStatus.RUNNING: "[yellow][RUNNING][/yellow]",
        MissionStatus.WAITING_APPROVAL: "[yellow][WAIT][/yellow]",
        MissionStatus.PAUSED: "[yellow][PAUSED][/yellow]",
        MissionStatus.COMPLETED: "[green][DONE][/green]",
        MissionStatus.FAILED: "[red][FAIL][/red]",
        MissionStatus.CANCELLED: "[red][CANCEL][/red]",
    }

    for m in missions:
        icon = status_icons.get(m.status, "❓")
        table.add_row(
            m.mission_id[:12] + "...",
            m.contract_title[:35],
            m.sector[:15],
            f"{icon} {m.status.value}",
            m.last_updated.isoformat()[:16] if hasattr(m.last_updated, "isoformat") else str(m.last_updated)[:16],
        )
    console.print(table)


@missions_app.command(name="show")
def mission_show(
    mission_id: str = typer.Argument(..., help="ID da mission (hash ou prefixo)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Mostra os detalhes completos de um Mission Contract."""
    repo = _repo()

    # Prefix matching
    actual_id = _resolve_id(repo, mission_id)
    if actual_id is None:
        console.print(f"[red]Mission não encontrada: {mission_id}[/red]")
        raise typer.Exit(1)

    try:
        contract = repo.get_contract(actual_id)
    except Exception as e:
        console.print(f"[red]Erro ao carregar contract: {e}[/red]")
        raise typer.Exit(1)

    if json_output:
        print(contract.model_dump_json(indent=2))
        return

    console.print(f"[bold]Mission Contract[/bold]")
    console.print(f"  ID: [cyan]{actual_id}[/cyan]")
    console.print(f"  Título: {contract.title}")
    console.print(f"  Objetivo: {contract.objective}")
    console.print(f"  Setor: {contract.sector.value}")
    console.print(f"  Risk Level: {contract.risk_level.value}")
    console.print(f"  Approval Policy: {contract.approval_policy.value}")
    console.print(f"  User Request: {contract.user_request[:100] if contract.user_request else '-'}")
    console.print(f"\n  Budget:")
    console.print(f"    Max Tokens: {contract.budget.max_tokens}")
    console.print(f"    Max Cost: ${contract.budget.max_cost_usd:.2f}")
    console.print(f"    Max Duration: {contract.budget.max_duration_seconds}s")
    console.print(f"    Max Steps: {contract.budget.max_steps}")

    if contract.expected_deliverables:
        console.print(f"\n  Deliverables esperados:")
        for d in contract.expected_deliverables:
            console.print(f"    - {d}")

    if contract.acceptance_criteria:
        console.print(f"\n  Acceptance Criteria:")
        for ac in contract.acceptance_criteria:
            console.print(f"    [{ac.id}] {ac.description[:60]}")

    if contract.tags:
        console.print(f"\n  Tags: {', '.join(contract.tags)}")

    if contract.parent_mission_id:
        console.print(f"\n  Parent Mission: {contract.parent_mission_id}")

    console.print(f"\n  Hash: {contract.content_hash()}")
    console.print(f"  Criado: {contract.created_at}")


@missions_app.command(name="state")
def mission_state(
    mission_id: str = typer.Argument(..., help="ID da mission (hash ou prefixo)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Mostra o TaskState projetado de uma mission."""
    repo = _repo()

    actual_id = _resolve_id(repo, mission_id)
    if actual_id is None:
        console.print(f"[red]Mission não encontrada: {mission_id}[/red]")
        raise typer.Exit(1)

    try:
        state = repo.project(actual_id)
    except Exception as e:
        console.print(f"[red]Erro ao projetar estado: {e}[/red]")
        raise typer.Exit(1)

    if json_output:
        print(state.model_dump_json(indent=2))
        return

    status_icons = {
        MissionStatus.DRAFT: "[dim]DRAFT[/dim]",
        MissionStatus.RUNNING: "[yellow]RUNNING[/yellow]",
        MissionStatus.WAITING_APPROVAL: "[yellow]WAITING_APPROVAL[/yellow]",
        MissionStatus.PAUSED: "[yellow]PAUSED[/yellow]",
        MissionStatus.COMPLETED: "[green]COMPLETED[/green]",
        MissionStatus.FAILED: "[red]FAILED[/red]",
        MissionStatus.CANCELLED: "[red]CANCELLED[/red]",
    }

    console.print(f"[bold]TaskState — {state.contract_title}[/bold]")
    console.print(f"  Mission ID: [cyan]{state.mission_id[:16]}...[/cyan]")
    console.print(f"  Status: {status_icons.get(state.status, str(state.status))}")
    console.print(f"  Setor: {state.sector}")
    console.print(f"  Tokens Acumulados: {state.cumulative_tokens}")
    console.print(f"  Custo Acumulado: ${state.cumulative_cost_usd:.4f}")
    console.print(f"  Último Evento: seq {state.last_event_sequence}")

    if state.current_step:
        console.print(f"  Step Atual: {state.current_step}")

    if state.completed_steps:
        console.print(f"  Steps Completados: {', '.join(state.completed_steps)}")

    if state.retry_count > 0:
        console.print(f"  Retries: {state.retry_count}")

    if state.budget_exceeded:
        console.print(f"  [red]BUDGET EXCEEDED[/red]")

    if state.approval_pending:
        console.print(f"  [yellow]Aprovação pendente[/yellow]")

    if state.artifacts:
        console.print(f"\n  Artifacts ({len(state.artifacts)}):")
        for a in state.artifacts[:10]:
            console.print(f"    - {a}")

    if state.errors:
        console.print(f"\n  Errors ({len(state.errors)}):")
        for e in state.errors[-5:]:
            console.print(f"    [{e.get('stage', '?')}] {e.get('error', '')[:80]}")

    console.print(f"\n  Última atualização: {state.last_updated}")


def _resolve_id(repo: JsonlRepository, id_fragment: str) -> Optional[str]:
    """Resolve ID por prefixo ou hash exato."""
    # Se o arquivo existe com o id exato
    if (repo.contracts_dir / f"{id_fragment}.json").exists():
        return id_fragment

    # Prefix matching
    candidates = []
    for f in repo.contracts_dir.glob("*.json"):
        if f.stem.startswith(id_fragment):
            candidates.append(f.stem)

    if len(candidates) == 1:
        return candidates[0]
    elif len(candidates) > 1:
        return None  # ambíguo

    return None
