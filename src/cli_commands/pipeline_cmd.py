"""CLI do Pipeline Local Dry-Run."""
import typer
from rich.console import Console
from rich.table import Table

from src.pipeline_local.service import PipelineLocalService
from src.pipeline_local.dry_run import dry_run_pipeline

pipeline_app = typer.Typer(
    name="pipeline",
    help="Pipeline local dry-run — conecta queue → caption → creative → publisher",
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
