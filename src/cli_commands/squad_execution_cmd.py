"""CLI for Squad Execution Plan (dry-run)."""
from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.panel import Panel

squad_execution_app = typer.Typer(
    name="squad-run",
    help="Squad Run — plano de execução dry-run de squads (sem agentes reais).",
    add_completion=False,
)
console = Console()


@squad_execution_app.callback()
def _callback():
    """Squad Run — nenhum agente é executado. Apenas planejamento."""


@squad_execution_app.command(name="plan")
def cmd_plan(
    request: str = typer.Argument(..., help="Pedido em linguagem natural"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Cria plano de execução dry-run para um pedido."""
    from src.squad_execution.planner import plan_squad_run
    from src.squad_composer.composer import compose_squad
    from src.task_decomposer.decomposer import decompose_squad
    from src.squad_execution.exporter import export_squad_run

    squad = compose_squad(request)
    task_plan = decompose_squad(squad)
    plan = plan_squad_run(request)
    export_squad_run(plan, squad_plan=squad, task_plan=task_plan)

    if json_out:
        console.print_json(json.dumps(plan.to_dict(), ensure_ascii=False))
        return

    status_color = "green" if plan.status == "planned_ready" else "yellow"
    console.print(Panel(f"[bold]Squad Run Plan[/bold] — {plan.squad_run_id}", expand=False))
    console.print(f"  request        : {plan.request[:60]}")
    console.print(f"  sector         : {plan.sector}")
    console.print(f"  status         : [{status_color}]{plan.status}[/{status_color}]")
    console.print(f"  risk           : {plan.risk_level}")
    console.print(f"  approval_req   : {plan.approval_required}")
    console.print(f"  roles          : {', '.join(plan.roles)}")
    if plan.next_actions:
        console.print(f"  next           : {plan.next_actions[0]}")


@squad_execution_app.command(name="show")
def cmd_show(
    squad_run_id: str = typer.Argument(..., help="ID do squad run (srun_...)"),
) -> None:
    """Mostra detalhes de um squad run exportado."""
    from src.squad_execution.exporter import DEFAULT_RUNS_ROOT
    import os

    run_dir = DEFAULT_RUNS_ROOT / squad_run_id
    manifest_path = run_dir / "squad_manifest.json"
    if not manifest_path.exists():
        console.print(f"[red]Squad run {squad_run_id} nao encontrado em {run_dir}[/red]")
        raise typer.Exit(1)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    console.print_json(json.dumps(manifest, ensure_ascii=False))


@squad_execution_app.command(name="list")
def cmd_list() -> None:
    """Lista squad runs exportados."""
    from src.squad_execution.exporter import DEFAULT_RUNS_ROOT

    if not DEFAULT_RUNS_ROOT.exists():
        console.print("[dim]Nenhum squad run encontrado.[/dim]")
        return

    runs = sorted(DEFAULT_RUNS_ROOT.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
    if not runs:
        console.print("[dim]Nenhum squad run encontrado.[/dim]")
        return

    for run_dir in runs[:10]:
        manifest_path = run_dir / "squad_manifest.json"
        if manifest_path.exists():
            m = json.loads(manifest_path.read_text(encoding="utf-8"))
            status = m.get("status", "?")
            sc = "green" if status == "planned_ready" else "yellow"
            console.print(f"  {run_dir.name}  [{sc}]{status}[/{sc}]  {m.get('sector', '?')}")
