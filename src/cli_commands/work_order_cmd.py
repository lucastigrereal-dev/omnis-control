"""CLI for Work Order System."""
from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

work_order_app = typer.Typer(
    name="work-order",
    help="Work Order System — tracking de outputs por step.",
    add_completion=False,
)
console = Console()


@work_order_app.callback()
def _callback():
    """Work Order System — deterministico, sem LLM, sem agentes reais."""


@work_order_app.command(name="build")
def cmd_build(
    request: str = typer.Argument(..., help="Pedido em linguagem natural"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Constroi work orders a partir de um pedido (orchestrator → graph → work orders)."""
    from src.mission_orchestrator.planner import build_plan
    from src.mission_orchestrator.executor import execute
    from src.execution_graph.mission_bridge import build_graph_from_orchestrator
    from src.execution_graph.runner import run_graph_dry
    from src.work_order.builder import build_work_orders_from_graph
    from src.work_order.validator import validate_work_order

    orch_run = build_plan(request, allow_unknown=True)
    orch_run = execute(orch_run)
    graph = build_graph_from_orchestrator(orch_run)
    step_run = run_graph_dry(graph)
    work_orders = build_work_orders_from_graph(graph, step_run)

    if json_out:
        output = {
            "orchestrator_run_id": orch_run.run_id,
            "graph_run_id": step_run.graph_run_id,
            "work_orders": [wo.to_dict() for wo in work_orders],
            "validation": {},
        }
        for wo in work_orders:
            result = validate_work_order(wo)
            output["validation"][wo.work_order_id] = {
                "is_valid": result.is_valid,
                "errors": result.errors,
                "warnings": result.warnings,
            }
        console.print_json(json.dumps(output, ensure_ascii=False))
        return

    console.print(Panel(f"[bold]Work Orders[/bold] — {len(work_orders)} orders", expand=False))
    table = Table(title="Work Orders")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Step", style="white")
    table.add_column("Role", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Contracts", style="magenta")

    for wo in work_orders:
        result = validate_work_order(wo)
        status_icon = "✓" if result.is_valid else "✗"
        table.add_row(
            wo.work_order_id[:16] + "...",
            wo.step_label[:30],
            wo.role,
            f"{wo.status.value} {status_icon}",
            str(len(wo.contracts)),
        )

    console.print(table)


@work_order_app.command(name="show")
def cmd_show(
    work_order_id: str = typer.Argument(..., help="Work Order ID"),
) -> None:
    """Mostra detalhes de uma work order (busca em disco)."""
    from pathlib import Path
    import glob as glob_mod

    exports_root = Path("exports/work_orders")
    found = None
    for pattern in [str(exports_root / f"*{work_order_id}*" / "work_order.json"),
                    str(exports_root / f"*{work_order_id}*" / "manifest.json")]:
        matches = glob_mod.glob(pattern)
        if matches:
            with open(matches[0], "r", encoding="utf-8") as f:
                found = json.load(f)
            break

    if found is None:
        console.print(f"[red]Work order {work_order_id} not found[/red]")
        return

    from src.work_order.models import WorkOrder

    wo = WorkOrder.from_dict(found)

    console.print(Panel(f"[bold]Work Order[/bold] — {wo.work_order_id}", expand=False))
    console.print(f"  status          : {wo.status.value}")
    console.print(f"  role            : {wo.role}")
    console.print(f"  step_label      : {wo.step_label}")
    console.print(f"  graph_step_id   : {wo.graph_step_id}")
    console.print(f"  graph_run_id    : {wo.graph_run_id}")
    console.print(f"  approval_id     : {wo.approval_id or '—'}")
    console.print(f"  created_at      : {wo.created_at}")
    console.print(f"  updated_at      : {wo.updated_at}")

    if wo.contracts:
        contract_table = Table(title="Output Contracts")
        contract_table.add_column("ID", style="cyan")
        contract_table.add_column("Type", style="green")
        contract_table.add_column("Description", style="white")
        contract_table.add_column("Required", style="yellow")
        for c in wo.contracts:
            contract_table.add_row(c.contract_id, c.output_type.value, c.description[:60], str(c.required))
        console.print(contract_table)

    if wo.outputs:
        output_table = Table(title="Collected Outputs")
        output_table.add_column("ID", style="cyan")
        output_table.add_column("Type", style="green")
        output_table.add_column("Status", style="yellow")
        output_table.add_column("Contract", style="white")
        for o in wo.outputs:
            output_table.add_row(o.output_id[:16], o.output_type.value, o.status, o.contract_id)
        console.print(output_table)


@work_order_app.command(name="list")
def cmd_list(
    status: str = typer.Option("", "--status", "-s", help="Filtrar por status"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Lista work orders do disco."""
    from pathlib import Path
    import glob as glob_mod

    exports_root = Path("exports/work_orders")
    manifests = list(glob_mod.glob(str(exports_root / "*" / "work_order.json")))
    manifests += list(glob_mod.glob(str(exports_root / "*" / "manifest.json")))

    work_orders = []
    for path in manifests:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            from src.work_order.models import WorkOrder
            wo = WorkOrder.from_dict(data)
            if status and wo.status.value != status:
                continue
            work_orders.append(wo)
        except Exception:
            continue

    if json_out:
        console.print_json(json.dumps(
            [wo.to_dict() for wo in work_orders], ensure_ascii=False
        ))
        return

    if not work_orders:
        console.print("[yellow]Nenhuma work order encontrada[/yellow]")
        return

    table = Table(title=f"Work Orders ({len(work_orders)})")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Role", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Outputs", style="magenta")
    table.add_column("Created", style="white")

    for wo in sorted(work_orders, key=lambda w: w.updated_at, reverse=True):
        table.add_row(
            wo.work_order_id[:16] + "...",
            wo.role,
            wo.status.value,
            f"{len(wo.outputs)}/{len(wo.contracts)}",
            wo.created_at[:19],
        )
    console.print(table)
