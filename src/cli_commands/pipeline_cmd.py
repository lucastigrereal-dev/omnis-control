"""CLI do Pipeline Local Dry-Run + Mission-Aware Pipeline."""
import json as _json
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.pipeline_local.service import PipelineLocalService
from src.pipeline_local.dry_run import dry_run_pipeline

pipeline_app = typer.Typer(
    name="pipeline",
    help="Pipeline local dry-run + mission-aware — conecta queue → caption → creative → publisher",
    add_completion=False,
)
console = Console()


@pipeline_app.command(name="dry-run")
def cmd_dry_run(
    queue_id: str = typer.Argument(..., help="ID do item na Content Queue"),
):
    """Executa pipeline local dry-run para um queue item.

    Fluxo: Queue Item → Caption Aprovada → Creative Brief → Export Package
           → Publisher Local Draft → Publisher Dry-Run → Métrica/Trace
    """
    result = dry_run_pipeline(queue_id)

    console.print(f"\n[bold]Pipeline Local Dry-Run[/bold] — run [cyan]{result.run_id[:8]}[/cyan]")
    console.print(f"  Queue Item: {result.queue_item_id}")

    if result.status == "success":
        console.print("  Status: [green]SUCCESS[/green]")
    elif result.status == "success_with_warnings":
        console.print("  Status: [yellow]SUCCESS WITH WARNINGS[/yellow]")
    elif result.status == "blocked":
        console.print(f"  Status: [red]BLOCKED[/red] — {result.block_reason}")
    else:
        console.print(f"  Status: [red]FAILED[/red]")

    if result.caption_draft_id:
        console.print(f"  Caption Draft: {result.caption_draft_id}")
    if result.creative_brief_id:
        console.print(f"  Creative Brief: {result.creative_brief_id}")
    if result.export_package_path:
        console.print(f"  Export Package: {result.export_package_path}")
    if result.publisher_draft_id:
        console.print(f"  Publisher Draft: {result.publisher_draft_id}")

    if result.warnings:
        console.print(f"\n[yellow]Warnings ({len(result.warnings)}):[/yellow]")
        for w in result.warnings:
            console.print(f"  - {w}")

    if result.evidence_refs:
        console.print(f"\n[dim]Evidence refs: {len(result.evidence_refs)}[/dim]")

    console.print(f"\n  Started: {result.started_at}")
    console.print(f"  Finished: {result.finished_at}")


@pipeline_app.command(name="status")
def cmd_status():
    """Resumo de execuções do pipeline local."""
    service = PipelineLocalService()
    data = service.status()

    console.print("[bold]Pipeline Local — Status[/bold]")
    console.print(f"  Total runs: {data['total_runs']}")

    if data["by_status"]:
        console.print(f"\n  Por status:")
        for s, count in sorted(data["by_status"].items()):
            console.print(f"    {s}: {count}")

    if data["recent_runs"]:
        table = Table(title="Últimas execuções")
        table.add_column("Run ID", style="cyan")
        table.add_column("Queue ID")
        table.add_column("Status")
        table.add_column("Warnings")
        for r in data["recent_runs"]:
            w_count = len(r.get("warnings", []))
            table.add_row(r["run_id"], r["queue_item_id"], r["status"], str(w_count))
        console.print(table)


# ---------------------------------------------------------------------------
# MISSION-AWARE COMMANDS (P0.6)
# ---------------------------------------------------------------------------


@pipeline_app.command(name="mission-run")
def cmd_mission_run(
    mission_id: str = typer.Argument(..., help="ID da mission (hash completo)"),
    queue_id: Optional[str] = typer.Option(None, "--queue-id", help="ID do item na Content Queue"),
    caption_draft_id: Optional[str] = typer.Option(None, "--caption-draft-id", help="ID do draft de legenda"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Executa pipeline local com eventos de missão.

    Conecta MissionContract ao pipeline local existente:
    Queue → Caption → Creative → Publisher Dry-Run.
    Emite EventEnvelope durante toda a execução.
    """
    from src.pipeline_local.mission_pipeline import run_mission_content_pipeline
    from src.pipeline_local.mission_models import (
        MissionPipelineStatus,
    )

    result = run_mission_content_pipeline(
        mission_id=mission_id,
        queue_item_id=queue_id,
        caption_draft_id=caption_draft_id,
    )

    if json_output:
        data = {
            "run_id": result.run_id,
            "mission_id": result.mission_id,
            "status": result.status,
            "block_reason": result.block_reason,
            "queue_item_id": result.queue_item_id,
            "caption_draft_id": result.caption_draft_id,
            "creative_brief_id": result.creative_brief_id,
            "export_package_path": result.export_package_path,
            "publisher_draft_id": result.publisher_draft_id,
            "warnings": result.warnings,
            "events_emitted": len(result.events_emitted),
            "evidence_refs": result.evidence_refs,
            "started_at": result.started_at,
            "finished_at": result.finished_at,
        }
        console.print(_json.dumps(data, indent=2, ensure_ascii=False))
        return

    console.print(f"\n[bold]Mission-Aware Pipeline[/bold] — run [cyan]{result.run_id[:8]}[/cyan]")
    console.print(f"  Mission ID: {result.mission_id[:16]}...")

    status_map = {
        MissionPipelineStatus.SUCCESS: "[green]SUCCESS[/green]",
        MissionPipelineStatus.WAITING_APPROVAL: "[yellow]WAITING_APPROVAL[/yellow]",
        MissionPipelineStatus.BLOCKED: "[red]BLOCKED[/red]",
        MissionPipelineStatus.FAILED: "[red]FAILED[/red]",
        MissionPipelineStatus.ALREADY_COMPLETED: "[green]ALREADY_COMPLETED[/green]",
    }
    console.print(f"  Status: {status_map.get(result.status, result.status)}")
    if result.block_reason:
        console.print(f"  Block reason: [red]{result.block_reason}[/red]")

    if result.queue_item_id:
        console.print(f"  Queue Item: {result.queue_item_id}")
    if result.caption_draft_id:
        console.print(f"  Caption Draft: {result.caption_draft_id}")
    if result.creative_brief_id:
        console.print(f"  Creative Brief: {result.creative_brief_id}")
    if result.export_package_path:
        console.print(f"  Export Package: {result.export_package_path}")
    if result.publisher_draft_id:
        console.print(f"  Publisher Draft: {result.publisher_draft_id}")

    console.print(f"  Events Emitted: {len(result.events_emitted)}")

    if result.warnings:
        console.print(f"\n[yellow]Warnings ({len(result.warnings)}):[/yellow]")
        for w in result.warnings[:8]:
            console.print(f"  - {w}")

    if result.evidence_refs:
        console.print(f"\n[dim]Evidence refs: {len(result.evidence_refs)}[/dim]")
        for e in result.evidence_refs[:5]:
            console.print(f"  [{e.get('type', '?')}] {e.get('ref', '')[:50]}")

    console.print(f"\n  Started: {result.started_at}")
    console.print(f"  Finished: {result.finished_at}")

    # Next action suggestion
    if result.status == MissionPipelineStatus.WAITING_APPROVAL:
        console.print(f"\n[yellow]Ação:[/yellow] Aprove a legenda e reexecute:")
        if result.caption_draft_id:
            console.print(f"  python jarvis.py approvals approve {result.caption_draft_id}")
        console.print(f"  python jarvis.py pipeline mission-run {mission_id[:16]}")


@pipeline_app.command(name="mission-status")
def cmd_mission_status(
    mission_id: str = typer.Argument(..., help="ID da mission (hash completo)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Mostra estado atual da missão + próximo passo sugerido."""
    from src.pipeline_local.mission_pipeline import get_mission_pipeline_status

    status_data = get_mission_pipeline_status(mission_id)

    if json_output:
        console.print(_json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    if status_data.get("status") == "not_found":
        console.print(f"[red]Mission não encontrada: {mission_id}[/red]")
        return

    status_map = {
        "draft": "[dim]DRAFT[/dim]",
        "running": "[yellow]RUNNING[/yellow]",
        "waiting_approval": "[yellow]WAITING_APPROVAL[/yellow]",
        "paused": "[yellow]PAUSED[/yellow]",
        "completed": "[green]COMPLETED[/green]",
        "failed": "[red]FAILED[/red]",
        "cancelled": "[red]CANCELLED[/red]",
    }

    console.print(f"[bold]Mission Status[/bold]")
    console.print(f"  ID: [cyan]{status_data['mission_id'][:16]}...[/cyan]")
    console.print(f"  Título: {status_data.get('title', '?')}")
    console.print(f"  Setor: {status_data.get('sector', '?')}")
    console.print(f"  Status: {status_map.get(status_data['status'], status_data['status'])}")
    console.print(f"  Tokens: {status_data['cumulative_tokens']}")
    console.print(f"  Custo: ${status_data['cumulative_cost_usd']:.4f}")
    console.print(f"  Último evento: seq {status_data['last_event_sequence']}")

    if status_data.get("pending_approval"):
        console.print(f"  [yellow]Aprovação pendente[/yellow]")

    if status_data.get("errors"):
        console.print(f"\n  [red]Últimos erros:[/red]")
        for e in status_data["errors"]:
            console.print(f"    [{e.get('stage', '?')}] {e.get('error', '')[:80]}")

    if status_data.get("next_action"):
        console.print(f"\n[bold]Próximo passo:[/bold] [yellow]{status_data['next_action']}[/yellow]")
