# OMNIS State — Atual (P7 concluido)

**Data:** 2026-05-09
**Branch:** master
**Fase concluida:** P7 Squad Composer Lite — todos os blocos
**Testes P7:** 72 modulos + 19 E2E = 91/91 PASS

---

## Pipeline Squad Composer (novo)

```
request → sector → capabilities → roles → squad → task plan → squad run manifest → approval gate
```

### Comandos novos

```bash
python jarvis.py role-registry list|show|match
python jarvis.py squad compose "<request>"
python jarvis.py tasks-plan from-request "<request>"
python jarvis.py squad-run plan "<request>"
python jarvis.py squad-run show <run_id>
python jarvis.py squad-run list
```

---

## Decisao estrategica

**OAuth Meta congelado. Fabrica offline e prioridade.**

---

## Modulos P7

```
src/role_registry/       — Role, RoleMatch, loader, matcher, errors
src/sector_registry/     — Sector, matcher (reusado por composer)
src/skill_matcher/       — Capability, matcher (reusado por composer)
src/squad_composer/      — SquadPlan, SquadRoleAssignment, composer
src/task_decomposer/     — SquadTask, TaskPlan, decomposer, cycle detection
src/squad_execution/     — SquadExecutionPlan, planner, exporter, approval gate
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
| P8.0 | Execution Graph Lite | Alta |
| P8.1 | Step Runner Dry-Run | Alta |
| P8.2 | Replay / Resume Squad Run | Media |
| P8.3 | Approval-Integrated Squad Run | Media |
| P8.4 | E2E Mission → Squad → Package | Media |
