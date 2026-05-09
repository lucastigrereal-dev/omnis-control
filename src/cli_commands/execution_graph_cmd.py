"""CLI for Execution Graph."""
from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

execution_graph_app = typer.Typer(
    name="graph",
    help="Execution Graph — DAG de passos com estados simulados.",
    add_completion=False,
)
console = Console()


@execution_graph_app.callback()
def _callback():
    """Execution Graph — deterministico, sem LLM, sem agentes reais."""


@execution_graph_app.command(name="build")
def cmd_build(
    request: str = typer.Argument(..., help="Pedido em linguagem natural"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Constroi um grafo de execucao a partir de um pedido."""
    from src.squad_composer.composer import compose_squad
    from src.task_decomposer.decomposer import decompose_squad
    from src.execution_graph.builder import build_graph
    from src.execution_graph.validator import validate_graph

    squad = compose_squad(request)
    task_plan = decompose_squad(squad)
    graph = build_graph(squad, task_plan)
    issues = validate_graph(graph)

    if json_out:
        output = graph.to_dict()
        output["validation_issues"] = issues
        console.print_json(json.dumps(output, ensure_ascii=False))
        return

    console.print(Panel(f"[bold]Execution Graph[/bold] — {graph.graph_id}", expand=False))
    console.print(f"  request         : {graph.request[:60]}")
    console.print(f"  squad_id        : {graph.squad_id}")
    console.print(f"  task_plan_id    : {graph.task_plan_id}")
    console.print(f"  nodes           : {len(graph.nodes)}")
    console.print(f"  edges           : {len(graph.edges)}")

    if issues:
        console.print(f"\n  [red]validation issues ({len(issues)}):[/red]")
        for issue in issues:
            console.print(f"    [red]- {issue}[/red]")
    else:
        console.print(f"\n  [green]validation: PASS[/green]")

    # Tree view
    root = Tree(f"[bold]Execution Order[/bold] ({len(graph.topological_order)} steps)")
    for i, sid in enumerate(graph.topological_order):
        node = graph.node_map.get(sid)
        if node:
            label = f"[{i+1}] {node.title} [{node.role_id}] ({node.estimated_duration})"
            branch = root.add(label)
            if node.depends_on:
                branch.add(f"deps: {len(node.depends_on)} upstream step(s)")
    console.print(root)


@execution_graph_app.command(name="show")
def cmd_show(
    graph_id: str = typer.Argument(..., help="Graph ID to show (not persisted yet)"),
) -> None:
    """Mostra detalhes de um grafo (placeholder — grafos nao sao persistidos)."""
    console.print(f"[yellow]Graph persistence not implemented yet. graph_id={graph_id}[/yellow]")


@execution_graph_app.command(name="list")
def cmd_list() -> None:
    """Lista grafos (placeholder — grafos nao sao persistidos)."""
    console.print("[yellow]Graph persistence not implemented yet. 0 graphs stored.[/yellow]")


@execution_graph_app.command(name="run")
def cmd_run(
    request: str = typer.Argument(..., help="Pedido em linguagem natural"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Simula a execucao de um grafo (dry-run)."""
    from src.squad_composer.composer import compose_squad
    from src.task_decomposer.decomposer import decompose_squad
    from src.execution_graph.builder import build_graph
    from src.execution_graph.runner import run_graph_dry
    from src.execution_graph.store import write_manifest, DEFAULT_STORE_ROOT

    squad = compose_squad(request)
    task_plan = decompose_squad(squad)
    graph = build_graph(squad, task_plan)
    step_run = run_graph_dry(graph)

    # Persist to store
    run_dir = DEFAULT_STORE_ROOT / step_run.graph_run_id
    write_manifest(run_dir, step_run.to_dict())

    if json_out:
        console.print_json(json.dumps(step_run.to_dict(), ensure_ascii=False))
        return

    color = {"done": "green", "failed": "red"}.get(step_run.status, "yellow")
    console.print(Panel(f"[bold]Graph Run[/bold] — {step_run.graph_run_id}", expand=False))
    console.print(f"  request         : {step_run.request[:60]}")
    console.print(f"  graph_id        : {step_run.graph_id}")
    console.print(f"  status          : [{color}]{step_run.status}[/{color}]")
    console.print(f"  steps executed  : {len(step_run.step_states)}")

    table = Table(title="Step States")
    table.add_column("step_id", style="dim")
    table.add_column("status")
    for step_id, status in step_run.step_states.items():
        sc = {"done": "green", "failed": "red", "skipped": "yellow"}.get(status, "white")
        table.add_row(step_id, f"[{sc}]{status}[/{sc}]")
    console.print(table)


@execution_graph_app.command(name="run-show")
def cmd_run_show(
    run_id: str = typer.Argument(..., help="Run ID to show"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Mostra detalhes de um graph run."""
    from src.execution_graph.store import read_manifest, DEFAULT_STORE_ROOT

    run_dir = DEFAULT_STORE_ROOT / run_id
    manifest = read_manifest(run_dir)
    if manifest is None:
        console.print(f"[red]Run not found: {run_id}[/red]")
        return

    if json_out:
        console.print_json(json.dumps(manifest, ensure_ascii=False))
        return

    console.print(Panel(f"[bold]Graph Run[/bold] — {manifest.get('graph_run_id')}", expand=False))
    console.print(f"  status   : {manifest.get('status')}")
    console.print(f"  started  : {manifest.get('started_at')}")
    console.print(f"  finished : {manifest.get('finished_at')}")

    if manifest.get("logs"):
        console.print(f"\n  [bold]Logs ({len(manifest['logs'])}):[/bold]")
        for log in manifest["logs"]:
            icon = {"done": "+", "failed": "X", "skipped": "~", "running": ">"}.get(
                log.get("status", ""), " "
            )
            console.print(f"    {icon} {log['message']}")


@execution_graph_app.command(name="run-list")
def cmd_run_list(
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Lista todos os graph runs."""
    from src.execution_graph.store import DEFAULT_STORE_ROOT

    runs: list[dict] = []
    if DEFAULT_STORE_ROOT.exists():
        for d in sorted(DEFAULT_STORE_ROOT.iterdir(), reverse=True):
            if d.is_dir():
                manifest_file = d / "manifest.json"
                if manifest_file.exists():
                    import json as _json
                    with open(manifest_file, "r", encoding="utf-8") as f:
                        m = _json.load(f)
                    runs.append({
                        "run_id": d.name,
                        "status": m.get("status"),
                        "request": m.get("request", "")[:60],
                        "steps": len(m.get("step_states", {})),
                    })

    if json_out:
        console.print_json(json.dumps(runs, ensure_ascii=False))
        return

    if not runs:
        console.print("[yellow]No graph runs found.[/yellow]")
        return

    table = Table(title="Graph Runs")
    table.add_column("run_id", style="dim")
    table.add_column("status")
    table.add_column("steps")
    table.add_column("request")
    for r in runs:
        sc = {"done": "green", "failed": "red"}.get(r.get("status", ""), "white")
        table.add_row(
            r["run_id"],
            f"[{sc}]{r['status']}[/{sc}]",
            str(r["steps"]),
            r["request"],
        )
    console.print(table)
