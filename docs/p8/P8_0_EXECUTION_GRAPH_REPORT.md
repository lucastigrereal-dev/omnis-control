# P8.0 Execution Graph Models + Builder — Report

**Data:** 2026-05-09 | **Status:** DONE

---

## Arquivos criados

```
src/execution_graph/__init__.py
src/execution_graph/models.py      — StepStatus, StepNode, ExecutionGraph
src/execution_graph/builder.py     — build_graph() from SquadPlan + TaskPlan
src/execution_graph/validator.py   — validate_graph() structural checks
src/execution_graph/errors.py      — ExecutionGraphError hierarchy
src/cli_commands/execution_graph_cmd.py — CLI: graph build|show|list
src/routers/system_router.py       — +execution_graph_app registration
tests/execution_graph/__init__.py
tests/execution_graph/test_execution_graph.py — 16 testes
```

---

## Modelos

### StepStatus (Enum)
`pending → ready → running → done | failed | skipped`

### StepNode (dataclass)
- step_id, task_id, role_id, title, description, expected_output
- depends_on: list[step_id]
- status: StepStatus
- estimated_duration: str (derivado de _DURATION_BY_ROLE)
- assigned_role: str

### ExecutionGraph (dataclass)
- graph_id, request, squad_id, task_plan_id
- nodes: list[StepNode]
- edges: list[(from_step_id, to_step_id)]
- topological_order: list[step_id] (Kahn's algorithm)
- node_map: property → dict[step_id, StepNode]

---

## Builder

`build_graph(squad_plan, task_plan) → ExecutionGraph`
- Converte cada SquadTask → StepNode
- Resolve dependências de task_id → step_id
- Kahn's algorithm para ordenação topológica
- Cycle detection via GraphBuildError

---

## Validator

`validate_graph(graph) → list[str]`
- Checa: nodes vazios, edge endpoints válidos, deps válidas
- Checa: topological order respeita edges
- Checa: sem step_ids duplicados
- Checa: topological order contém todos os nodes

---

## CLI

```bash
python jarvis.py graph build "<request>"        # constroi DAG
python jarvis.py graph build "<request>" --json  # output JSON
python jarvis.py graph show <graph_id>           # placeholder
python jarvis.py graph list                      # placeholder
```

---

## Testes

```
tests/execution_graph/test_execution_graph.py: 16/16 PASS
  - 5 unit (status, node, serialization, properties, ids)
  - 3 integration (marketing, app, empty raises)
  - 3 validator (valid graph, no nodes, duplicate, order mismatch)
  - 2 CLI smoke (build, build --json)
  - 2 edge cases (all statuses, single node no deps)
```
