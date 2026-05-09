"""Work Order Builder — transforms execution graph steps into work orders."""
from __future__ import annotations

from src.work_order.errors import WorkOrderBuildError
from src.work_order.models import (
    OutputContract,
    OutputType,
    WorkOrder,
    WorkOrderStatus,
    make_work_order_id,
)

# Role → default output contracts
_ROLE_CONTRACT_TEMPLATES: dict[str, list[tuple[str, str, bool]]] = {
    "copywriter": [
        ("markdown", "Texto final do post/collab", True),
        ("json", "Metadados do conteudo (hashtags, mentions, SEO)", True),
    ],
    "creative_director": [
        ("image_asset", "Imagem ou carrossel final", True),
        ("markdown", "Guia visual e referencias", False),
    ],
    "sales_strategist": [
        ("json", "Plano de precificacao e abordagem", True),
        ("mission_report", "Relatorio de prospeccao", False),
    ],
    "app_architect": [
        ("json", "Especificacao de sistema", True),
        ("delivery_package", "Pacote de implementacao", False),
    ],
    "analyst": [
        ("json", "Analise de dados e recomendacoes", True),
        ("markdown", "Resumo executivo", False),
    ],
    "community_manager": [
        ("markdown", "Roteiro de engajamento", True),
        ("json", "Calendario de interacoes", True),
    ],
    "seo_specialist": [
        ("json", "Relatorio de keywords e metadata", True),
        ("markdown", "Resumo de otimizacao", False),
    ],
    "metrics_tracker": [
        ("json", "Dashboard de metricas", True),
        ("mission_report", "Relatorio de desempenho", False),
    ],
    "traffic_manager": [
        ("json", "Plano de distribuicao", True),
        ("markdown", "Checklist de publicacao", True),
    ],
    "designer": [
        ("image_asset", "Asset visual final", True),
        ("markdown", "Especificacao de design", False),
    ],
    "video_editor": [
        ("video_plan", "Plano de video ou edicao", True),
        ("image_asset", "Thumbnail", False),
    ],
}


def _infer_contracts(role: str, expected_output: str) -> list[OutputContract]:
    """Generate output contracts for a role based on templates and expected output."""
    contracts: list[OutputContract] = []
    templates = _ROLE_CONTRACT_TEMPLATES.get(role, [
        ("unknown", "Output gerado pela role", True),
    ])

    for i, (output_type_str, description, required) in enumerate(templates):
        try:
            ot = OutputType(output_type_str)
        except ValueError:
            ot = OutputType.UNKNOWN

        contracts.append(OutputContract(
            contract_id=f"contract_{i:02d}",
            output_type=ot,
            description=f"[{role}] {description}",
            required=required,
            min_count=1 if required else 0,
            max_count=1,
        ))

    return contracts


def build_work_orders_from_graph(graph, graph_run) -> list[WorkOrder]:
    """Transform each StepNode in the ExecutionGraph into a WorkOrder.

    Args:
        graph: ExecutionGraph with nodes
        graph_run: StepRun with run metadata

    Returns:
        List of WorkOrder, one per StepNode (in topological order)
    """
    from src.execution_graph.models import ExecutionGraph, StepNode, StepRun

    node_map = graph.node_map
    work_orders: list[WorkOrder] = []

    ordered_ids = graph.topological_order if graph.topological_order else [n.step_id for n in graph.nodes]

    for step_id in ordered_ids:
        node = node_map.get(step_id)
        if node is None:
            raise WorkOrderBuildError(f"Step {step_id} referenced in order but not in nodes")

        role = node.assigned_role or node.role_id
        contracts = _infer_contracts(role, node.expected_output)

        wo = WorkOrder(
            work_order_id=make_work_order_id(),
            graph_step_id=node.step_id,
            graph_run_id=graph_run.graph_run_id,
            role=role,
            step_label=node.title,
            status=WorkOrderStatus.DRAFT,
            contracts=contracts,
            metadata={
                "task_id": node.task_id,
                "expected_output": node.expected_output,
                "depends_on": node.depends_on,
                "estimated_duration": node.estimated_duration,
                "role_id": node.role_id,
                "graph_id": graph.graph_id,
                "request": graph.request,
                "squad_id": graph.squad_id,
            },
        )
        work_orders.append(wo)

    return work_orders


def build_work_orders_from_step_run(step_run) -> list[WorkOrder]:
    """Rebuild work orders from a StepRun's graph_snapshot."""
    from src.execution_graph.models import ExecutionGraph

    if step_run.graph_snapshot is None:
        raise WorkOrderBuildError("StepRun has no graph_snapshot — cannot rebuild work orders")

    graph = ExecutionGraph.from_dict(step_run.graph_snapshot)
    return build_work_orders_from_graph(graph, step_run)
