"""CLI commands for the CaptionDraftAgent — `omnis agent <cmd>`."""
from __future__ import annotations

import json
import os

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.agentic.agent_models import AgentRunRepository, AgentRunStatus, StepStatus
from src.agentic.batch_runner import BatchReport, BatchRunner, BatchVerdict
from src.agentic.caption_draft_agent import CaptionDraftAgent
from src.agentic.llm_adapter import LiteLLMAdapter
from src.agentic.scheduler import SchedulerService
from src.content_queue import Queue, QueueStatus
from src.memory.caption_memory import CaptionMemoryReader

agent_app = typer.Typer(name="agent", help="CaptionDraftAgent — loop completo de geração")
console = Console()

_ROOT = os.path.normpath(os.getenv("OMNIS_ROOT", os.path.expanduser("~/omnis-control")))


# ── run ───────────────────────────────────────────────────────────────────────

@agent_app.command(name="run")
def agent_run(
    queue_id: str = typer.Argument(..., help="ID do QueueItem a processar"),
    dry_run: bool = typer.Option(True, "--dry-run/--real", help="Simula sem persistir"),
    json_out: bool = typer.Option(False, "--json", help="Saída em JSON"),
) -> None:
    """Executa o loop completo para um item da fila."""
    agent = CaptionDraftAgent(dry_run=dry_run)
    run = agent.run(queue_id)

    if json_out:
        console.print_json(json.dumps(run.to_dict()))
        raise typer.Exit(0 if run.status != AgentRunStatus.FAILED else 1)

    _print_run(run)
    raise typer.Exit(0 if run.status != AgentRunStatus.FAILED else 1)


# ── runs (histórico) ──────────────────────────────────────────────────────────

@agent_app.command(name="runs")
def agent_runs(
    limit: int = typer.Option(10, "--limit", "-n", help="Número de runs a mostrar"),
    account: str | None = typer.Option(None, "--account", "-a", help="Filtrar por conta"),
    json_out: bool = typer.Option(False, "--json", help="Saída em JSON"),
) -> None:
    """Lista runs anteriores do agente."""
    repo = AgentRunRepository()
    runs = repo.list_all()
    if account:
        runs = [r for r in runs if r.account_handle == account]
    runs = list(reversed(runs))[:limit]

    if json_out:
        console.print_json(json.dumps([r.to_dict() for r in runs]))
        return

    if not runs:
        console.print("[yellow]Nenhum run encontrado.[/yellow]")
        return

    table = Table(title=f"Agent Runs (últimos {len(runs)})", show_lines=False)
    table.add_column("run_id", style="cyan", no_wrap=True)
    table.add_column("account", style="white")
    table.add_column("objective", style="white")
    table.add_column("status", style="bold")
    table.add_column("gate", style="white")
    table.add_column("steps", justify="right")
    table.add_column("started_at", style="dim")

    for r in runs:
        status_color = {
            AgentRunStatus.COMPLETED: "green",
            AgentRunStatus.DRY_RUN: "blue",
            AgentRunStatus.FAILED: "red",
            AgentRunStatus.RUNNING: "yellow",
        }.get(r.status, "white")
        gate = r.result.get("gate_verdict", "—") if r.result else "—"
        table.add_row(
            r.run_id,
            r.account_handle,
            r.objective,
            f"[{status_color}]{r.status}[/{status_color}]",
            str(gate),
            str(len(r.steps)),
            r.started_at[:19].replace("T", " "),
        )
    console.print(table)


# ── batch ─────────────────────────────────────────────────────────────────────

@agent_app.command(name="batch")
def agent_batch(
    limit: int = typer.Option(5, "--limit", "-n", help="Máx de itens a processar"),
    account: str | None = typer.Option(None, "--account", "-a", help="Filtrar por conta"),
    dry_run: bool = typer.Option(True, "--dry-run/--real", help="Simula sem persistir"),
    json_out: bool = typer.Option(False, "--json", help="Saída em JSON"),
) -> None:
    """Processa N itens planned/needs_caption da fila em sequência."""
    runner_obj = BatchRunner(dry_run=dry_run)
    report = runner_obj.run(limit=limit, account_filter=account)

    if json_out:
        console.print_json(json.dumps(report.to_dict()))
        raise typer.Exit(0)

    _print_batch_report(report)
    raise typer.Exit(0)


# ── schedule ──────────────────────────────────────────────────────────────────

@agent_app.command(name="schedule-add")
def schedule_add(
    every: float = typer.Option(..., "--every", "-e", help="Intervalo em horas (ex: 6, 0.5)"),
    account: str | None = typer.Option(None, "--account", "-a"),
    limit: int = typer.Option(5, "--limit", "-n"),
    dry_run: bool = typer.Option(True, "--dry-run/--real"),
    run_now: bool = typer.Option(False, "--run-now", help="Agenda para executar imediatamente"),
) -> None:
    """Adiciona um schedule de batch recorrente."""
    svc = SchedulerService()
    schedule = svc.add(
        interval_hours=every,
        account_filter=account,
        limit=limit,
        dry_run=dry_run,
        run_now=run_now,
    )
    console.print(f"[green]Schedule criado:[/green] [cyan]{schedule.schedule_id}[/cyan]")
    console.print(f"  Intervalo:  {every}h")
    console.print(f"  Conta:      {account or 'todas'}")
    console.print(f"  Limit:      {limit}")
    console.print(f"  Mode:       {'dry_run' if dry_run else 'real'}")
    console.print(f"  Próximo:    {schedule.next_run_at}")


@agent_app.command(name="schedule-list")
def schedule_list(
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Lista schedules cadastrados."""
    svc = SchedulerService()
    schedules = svc.list_schedules()

    if json_out:
        console.print_json(json.dumps([s.to_dict() for s in schedules]))
        return

    if not schedules:
        console.print("[yellow]Nenhum schedule cadastrado.[/yellow]")
        return

    table = Table(title="Schedules", show_lines=False)
    table.add_column("id", style="cyan", no_wrap=True)
    table.add_column("account")
    table.add_column("every", justify="right")
    table.add_column("limit", justify="right")
    table.add_column("mode")
    table.add_column("runs", justify="right")
    table.add_column("next_run", style="dim")
    table.add_column("enabled")

    for s in schedules:
        table.add_row(
            s.schedule_id,
            s.account_filter or "todas",
            f"{s.interval_hours}h",
            str(s.limit),
            "dry" if s.dry_run else "real",
            str(s.run_count),
            s.next_run_at[:16].replace("T", " "),
            "[green]✓[/green]" if s.enabled else "[red]✗[/red]",
        )
    console.print(table)


@agent_app.command(name="schedule-run")
def schedule_run(
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Executa todos os schedules vencidos. Chamar via cron ou Task Scheduler."""
    svc = SchedulerService()
    executed = svc.run_due()

    if json_out:
        console.print_json(json.dumps([r.to_dict() for r in executed]))
        return

    if not executed:
        console.print("[dim]Nenhum schedule vencido.[/dim]")
        return

    for r in executed:
        console.print(
            f"[cyan]{r.schedule_id}[/cyan]  "
            f"processed={r.total_processed}  "
            f"[green]approved={r.approved}[/green]  "
            f"[yellow]review={r.needs_review}[/yellow]  "
            f"[red]failed={r.failed}[/red]"
        )


@agent_app.command(name="schedule-remove")
def schedule_remove(
    schedule_id: str = typer.Argument(..., help="ID do schedule a remover"),
) -> None:
    """Remove um schedule pelo ID."""
    svc = SchedulerService()
    removed = svc.remove(schedule_id)
    if removed:
        console.print(f"[green]Removido:[/green] {schedule_id}")
    else:
        console.print(f"[red]Não encontrado:[/red] {schedule_id}")
        raise typer.Exit(1)


@agent_app.command(name="schedule-history")
def schedule_history(
    schedule_id: str | None = typer.Option(None, "--schedule", "-s"),
    limit: int = typer.Option(10, "--limit", "-n"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Histórico de execuções de schedules."""
    svc = SchedulerService()
    runs = list(reversed(svc.history(schedule_id)))[:limit]

    if json_out:
        console.print_json(json.dumps([r.to_dict() for r in runs]))
        return

    if not runs:
        console.print("[yellow]Nenhuma execução registrada.[/yellow]")
        return

    table = Table(title="Schedule History", show_lines=False)
    table.add_column("run_id", style="cyan", no_wrap=True)
    table.add_column("schedule_id", style="dim")
    table.add_column("processed", justify="right")
    table.add_column("approved", justify="right", style="green")
    table.add_column("review", justify="right", style="yellow")
    table.add_column("failed", justify="right", style="red")
    table.add_column("executed_at", style="dim")

    for r in runs:
        table.add_row(
            r.run_id, r.schedule_id[:10],
            str(r.total_processed), str(r.approved),
            str(r.needs_review), str(r.failed),
            r.executed_at[:16].replace("T", " "),
        )
    console.print(table)


# ── status ───────────────────────────────────────────────────────────────────

@agent_app.command(name="status")
def agent_status(
    json_out: bool = typer.Option(False, "--json", help="Saída em JSON"),
) -> None:
    """Painel de observabilidade da camada agentic (read-only)."""
    # Queue
    q = Queue()
    all_items = q.list_all()
    pending = [i for i in all_items if i.status in (QueueStatus.PLANNED, QueueStatus.NEEDS_CAPTION)]
    caption_ready = [i for i in all_items if i.status == "caption_ready"]

    # Runs
    repo = AgentRunRepository()
    all_runs = list(reversed(repo.list_all()))
    recent_runs = all_runs[:5]
    run_counts = {
        AgentRunStatus.COMPLETED: sum(1 for r in all_runs if r.status == AgentRunStatus.COMPLETED),
        AgentRunStatus.DRY_RUN: sum(1 for r in all_runs if r.status == AgentRunStatus.DRY_RUN),
        AgentRunStatus.FAILED: sum(1 for r in all_runs if r.status == AgentRunStatus.FAILED),
    }

    # Schedules
    svc = SchedulerService()
    schedules = svc.list_schedules()
    active_schedules = [s for s in schedules if s.enabled]
    due_schedules = [s for s in active_schedules if s.is_due]

    # Memory
    reader = CaptionMemoryReader()
    memory_total = reader.count()

    # LiteLLM health (non-blocking)
    litellm_available = LiteLLMAdapter().health_check()

    if json_out:
        console.print_json(json.dumps({
            "queue": {
                "total": len(all_items),
                "pending": len(pending),
                "caption_ready": len(caption_ready),
            },
            "runs": {
                "total": len(all_runs),
                "completed": run_counts[AgentRunStatus.COMPLETED],
                "dry_run": run_counts[AgentRunStatus.DRY_RUN],
                "failed": run_counts[AgentRunStatus.FAILED],
            },
            "schedules": {
                "total": len(schedules),
                "active": len(active_schedules),
                "due_now": len(due_schedules),
            },
            "memory": {"total_entries": memory_total},
            "litellm_available": litellm_available,
        }))
        return

    # ── Rich dashboard ────────────────────────────────────────────────────────
    console.print("\n[bold cyan]OMNIS Agent Status[/bold cyan]\n")

    # Queue panel
    q_color = "green" if not pending else "yellow"
    console.print(
        f"  [bold]Fila:[/bold]  "
        f"total=[white]{len(all_items)}[/white]  "
        f"[{q_color}]pendente={len(pending)}[/{q_color}]  "
        f"[green]caption_ready={len(caption_ready)}[/green]"
    )

    # Schedules panel
    sched_color = "red" if due_schedules else "green"
    console.print(
        f"  [bold]Schedules:[/bold]  "
        f"ativos=[white]{len(active_schedules)}[/white]  "
        f"[{sched_color}]vencidos={len(due_schedules)}[/{sched_color}]"
    )
    if due_schedules:
        console.print(f"  [red]  ↳ {len(due_schedules)} schedule(s) aguardando `omnis agent schedule-run`[/red]")

    # Memory
    console.print(f"  [bold]Memória:[/bold]  [cyan]{memory_total}[/cyan] legendas aprovadas")

    # LiteLLM
    llm_color = "green" if litellm_available else "red"
    llm_label = "disponível" if litellm_available else "indisponível (use --dry-run)"
    console.print(f"  [bold]LiteLLM:[/bold]  [{llm_color}]{llm_label}[/{llm_color}]")

    # Recent runs table
    if recent_runs:
        console.print()
        table = Table(title="Últimos 5 Runs", show_lines=False, box=None, padding=(0, 1))
        table.add_column("run_id", style="cyan", width=14)
        table.add_column("account", width=20)
        table.add_column("status", width=12)
        table.add_column("gate", width=14)
        table.add_column("started_at", style="dim")
        for r in recent_runs:
            s_color = {
                AgentRunStatus.COMPLETED: "green",
                AgentRunStatus.DRY_RUN: "blue",
                AgentRunStatus.FAILED: "red",
            }.get(r.status, "white")
            gate = r.result.get("gate_verdict", "—") if r.result else "—"
            table.add_row(
                r.run_id[:12],
                r.account_handle,
                f"[{s_color}]{r.status}[/{s_color}]",
                str(gate),
                r.started_at[:16].replace("T", " "),
            )
        console.print(table)
    else:
        console.print("\n  [dim]Nenhum run registrado.[/dim]")

    console.print()


# ── memory ────────────────────────────────────────────────────────────────────

@agent_app.command(name="memory")
def agent_memory(
    account: str | None = typer.Option(None, "--account", "-a", help="Filtrar por conta"),
    objective: str | None = typer.Option(None, "--objective", "-o", help="Filtrar por objetivo"),
    limit: int = typer.Option(5, "--limit", "-n"),
) -> None:
    """Mostra legendas aprovadas gravadas na memória do agente."""
    reader = CaptionMemoryReader()

    if account and objective:
        captions = reader.find_similar(account, objective, top_k=limit)
        if not captions:
            console.print(f"[yellow]Nenhuma legenda na memória para {account}/{objective}[/yellow]")
            return
        console.print(f"[bold]Memória:[/bold] {account} / {objective} ({len(captions)} entradas)")
        for i, text in enumerate(captions, 1):
            console.print(Panel(text, title=f"#{i}", expand=False))
        return

    total = reader.count(account)
    label = account or "todas as contas"
    console.print(f"[bold]Legendas na memória[/bold] — {label}: [cyan]{total}[/cyan] entradas")


# ── internals ─────────────────────────────────────────────────────────────────

def _print_run(run) -> None:  # type: ignore[no-untyped-def]
    status_color = {
        AgentRunStatus.COMPLETED: "green",
        AgentRunStatus.DRY_RUN: "blue",
        AgentRunStatus.FAILED: "red",
    }.get(run.status, "white")

    console.print(f"\n[bold]Run[/bold] [cyan]{run.run_id}[/cyan]  "
                  f"[{status_color}]{run.status}[/{status_color}]")
    console.print(f"  Conta:    {run.account_handle}")
    console.print(f"  Objetivo: {run.objective}")

    table = Table(show_header=True, show_lines=False, box=None, padding=(0, 1))
    table.add_column("step", style="dim", width=20)
    table.add_column("status", width=10)
    table.add_column("output", style="white")

    for step in run.steps:
        s_color = {
            StepStatus.OK: "green",
            StepStatus.ERROR: "red",
            StepStatus.SKIPPED: "yellow",
        }.get(step.status, "white")
        summary = step.output_summary or step.error or ""
        table.add_row(step.name, f"[{s_color}]{step.status}[/{s_color}]", summary[:80])
    console.print(table)

    if run.result:
        console.print(f"\n  gate:    {run.result.get('gate_verdict', '—')}")
        console.print(f"  draft:   {run.result.get('draft_id', '—')}")
        console.print(f"  memory:  {'✓' if run.result.get('memory_written') else '—'}")
        console.print(f"  model:   {run.result.get('model_used', '—')}")

    if run.error:
        console.print(f"\n[red]Erro:[/red] {run.error}")


def _print_batch_report(report: BatchReport) -> None:
    mode = "[blue]dry_run[/blue]" if report.dry_run else "[green]real[/green]"
    console.print(
        f"\n[bold]Batch[/bold] [cyan]{report.batch_id}[/cyan]  {mode}"
        f"  candidates={report.total_candidates}"
        f"  processed={report.total_processed}"
    )

    table = Table(show_header=True, show_lines=False, box=None, padding=(0, 1))
    table.add_column("queue_id", style="cyan", no_wrap=True, width=14)
    table.add_column("account", width=20)
    table.add_column("objective", width=14)
    table.add_column("verdict", width=14)
    table.add_column("draft_id", style="dim")

    verdict_colors = {
        BatchVerdict.APPROVED: "green",
        BatchVerdict.APPROVED_DRY: "blue",
        BatchVerdict.NEEDS_REVIEW: "yellow",
        BatchVerdict.FAILED: "red",
        BatchVerdict.SKIPPED: "dim",
    }

    for r in report.results:
        color = verdict_colors.get(r.verdict, "white")
        table.add_row(
            r.queue_id[:12],
            r.account_handle,
            r.objective,
            f"[{color}]{r.verdict}[/{color}]",
            r.draft_id[:12] if r.draft_id else r.error[:30],
        )
    console.print(table)

    console.print(
        f"\n  [green]approved[/green] {report.approved}"
        f"  [yellow]needs_review[/yellow] {report.needs_review}"
        f"  [red]failed[/red] {report.failed}"
        f"  [dim]skipped[/dim] {report.skipped}"
    )
