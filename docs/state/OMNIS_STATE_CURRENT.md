# OMNIS State — Atual (P10 em andamento)

**Data:** 2026-05-12
**Branch:** master
**Fase concluida:** P8 Execution Graph Lite — todos os blocos
**Fase concluida:** P9 Work Order System — Final Seal (206/70 testes)
**Fase atual:** P10 — Output Generator Dry-Run (P10.1 concluido)

---

## Pipeline Execution Graph (P8)

```
request → intent → sector → squad → task plan → execution graph → step runner → approval gate → event log → metrics
```

### Comandos P8

```bash
python jarvis.py orchestrator plan|run|run-full|status|list "<request>"
python jarvis.py graph build|run|run-gated|run-resume|run-replay|show|list
```

---

## Pipeline P9 (concluido)

```
execution graph → work order → contract → approval bridge → output collector → mission package auto-fill → delivery report
```

---

## Decisao estrategica

**OAuth Meta congelado. Fabrica offline e prioridade.**

---

## Modulos

```
src/role_registry/       — Role, RoleMatch, loader, matcher, errors (P7)
src/sector_registry/     — Sector, matcher (P5)
src/skill_matcher/       — Capability, matcher (P5)
src/squad_composer/      — SquadPlan, SquadRoleAssignment, composer (P7)
src/task_decomposer/     — SquadTask, TaskPlan, decomposer, cycle detection (P7)
src/squad_execution/     — SquadExecutionPlan, planner, exporter, approval gate (P7)
src/execution_graph/     — GraphNode, GraphRun, builder (Kahn), runner, replay, approval_bridge, mission_bridge, events, metrics, store (P8)
src/approval_center/     — ApprovalRequest, service, models, errors (P6)
src/mission_orchestrator/ — OrchestratorRun, planner, executor, service, models, errors (P3)
src/work_order/          — WorkOrder, OutputContract, OutputEntry, builder, validator, collector, approval_bridge, graph_integration, package_autofill (P9 — 206 testes)
```

---

## Bloqueios ativos

- **OAuth Meta** — congelado por decisao estrategica
- **Post real** — bloqueado ate OAuth + revisao humana
- **CrewAI / LangGraph / OpenHands** — nao usados, nao permitidos

---

## Proximas fases

| Fase | Descricao | Prioridade |
|---|---|---|
| P10 | Sandbox Package Factory | Alta |
| P10.1 | Multi-profile Content Pipeline | Alta |
| P10.2 | Calendar Auto-Scheduling | Media |
| P10.3 | Analytics Dashboard Lite | Media |
