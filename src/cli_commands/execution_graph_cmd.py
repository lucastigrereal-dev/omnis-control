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
