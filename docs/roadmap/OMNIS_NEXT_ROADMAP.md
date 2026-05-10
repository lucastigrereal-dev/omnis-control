# OMNIS Próximo Roadmap — P9.6 concluido

**Data:** 2026-05-09 | **Base:** P9 Final Seal, 206 testes P9 + 137 P8 + ~1,723 outros

> P8 ENTREGUE: Execution Graph Lite (137 testes). P9 ENTREGUE: Work Order System completo (206 testes, Final Seal).
> Roadmap abaixo reflete P10+.

---

## P8.0 — Execution Graph Lite

**Objetivo:** DAG de tarefas com estados (pending → running → done → failed), sem agentes reais.

- Model: ExecutionGraph, StepNode, StepStatus
- Topological sort com paralelismo simulado
- CLI: `graph plan "<request>"` — gera DAG visual
- Testes: 15 minimo
- **Sem agentes reais. SemLangGraph. Sem CrewAI.**

---

## P8.1 — Step Runner Dry-Run

**Objetivo:** Simular execucao de cada step do DAG, registrando timestamps e status fake.

- Model: StepRun, StepRunLog
- Runner deterministico por role
- CLI: `graph run "<request>" --dry-run`
- Testes: 15 minimo

---

## P8.2 — Replay / Resume Squad Run

**Objetivo:** Retomar squad run interrompido, pulando steps ja concluidos.

- Model: SquadRunResumePoint
- Store: JSONL com estado de cada step
- CLI: `squad-run resume <run_id>`
- Testes: 12 minimo

---

## P8.3 — Approval-Integrated Squad Run

**Objetivo:** Conectar approval_center ao squad_run — so executa steps apos aprovacao.

- Bridge: approval_center ↔ squad_execution
- CLI: `squad-run request-approval <run_id>` + `squad-run approve <run_id>`
- Testes: 12 minimo

---

## P8.4 — E2E Mission → Squad → Package

**Objetivo:** Fluxo completo: mission builder → squad composer → task plan → execution → package delivery.

- E2E test integrando P3 (missions) + P7 (squads) + P2 (packages)
- Testes: 10 minimo

---

## P9 — Work Order System (CONCLUIDO — Final Seal)

**Objetivo:** Transformar graph nodes em work orders rastreaveis com contracts, outputs e mission package auto-fill.

| Bloco | Descricao | Testes | Status |
|---|---|---|---|
| P9.0 | Work Order Models + Builder | 61/10 | ✅ |
| P9.1 | Local Execution Contracts | 36/10 | ✅ |
| P9.2 | Output Collector | 23/10 | ✅ |
| P9.3 | Approval-to-Execution Bridge | 22/10 | ✅ |
| P9.4 | Graph → Work Order Integration | 17/10 | ✅ |
| P9.5 | Mission Package Auto-Fill | 16/10 | ✅ |
| P9.6 | E2E Work Order Flow | 31/10 | ✅ |
| P9.7 | Final Seal | — | ✅ |
| **Total** | | **206/70** | |

---

## Nao Implementar Nesta Fase

- LangGraph
- CrewAI
- OpenHands
- Meta API / Instagram
- OAuth
- Qualquer chamada de rede
- Agentes reais
- Execucao real de tarefas
