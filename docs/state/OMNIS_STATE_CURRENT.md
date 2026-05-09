# OMNIS State — Atual (P9 iniciado)

**Data:** 2026-05-09
**Branch:** master
**Fase concluida:** P8 Execution Graph Lite — todos os blocos
**Fase atual:** P9 Work Order System — Global Gate aberto
**Testes P8:** 137/137 PASS

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

## Pipeline P9 (em construcao)

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
src/work_order/          — [P9.0 — pending]
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
| P9.0 | Work Order Models + Builder | Alta |
| P9.1 | Local Execution Contracts | Alta |
| P9.2 | Output Collector | Media |
| P9.3 | Approval-to-Execution Bridge | Media |
| P9.4 | Execution Graph → Work Order Integration | Media |
| P9.5 | Mission Package Auto-Fill | Media |
| P9.6 | E2E Mission → Graph → Work Orders → Outputs | Media |
| P9.7 | Final Seal | Baixa |
