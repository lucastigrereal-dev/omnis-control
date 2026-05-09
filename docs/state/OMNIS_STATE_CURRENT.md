# OMNIS State — Atual (P8 em andamento)

**Data:** 2026-05-09
**Branch:** master
**Fase concluida:** P7 Squad Composer Lite — todos os blocos
**Fase atual:** P8 Execution Graph Lite — Global Gate aberto
**Testes P7:** 72 modulos + 19 E2E = 91/91 PASS

---

## Pipeline Squad Composer (P7)

```
request → sector → capabilities → roles → squad → task plan → squad run manifest → approval gate
```

### Comandos P7

```bash
python jarvis.py role-registry list|show|match
python jarvis.py squad compose "<request>"
python jarvis.py tasks-plan from-request "<request>"
python jarvis.py squad-run plan "<request>"
python jarvis.py squad-run show <run_id>
python jarvis.py squad-run list
```

---

## Pipeline P8 (em construcao)

```
request → sector → capabilities → roles → squad → task plan → execution graph → step runner → approval gate → event log
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
src/execution_graph/     — [P8.0 — pending]
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
| P8.0 | Execution Graph Models + Builder | Alta |
| P8.1 | Step Runner Dry-Run | Alta |
| P8.2 | Replay / Resume Squad Run | Media |
| P8.3 | Approval-Integrated Graph Run | Media |
| P8.4 | Event Log + Metrics | Media |
| P8.5 | Mission → Squad → Graph Integration | Media |
| P8.6 | E2E Mission → Squad → Graph → Approval | Media |
| P8.7 | Final Seal | Baixa |
