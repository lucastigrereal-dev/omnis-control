# OMNIS Próximo Roadmap — P8+

**Data:** 2026-05-09 | **Base:** P7 completo, ~1,341 testes

> P7 ENTREGUE: Role Registry, Squad Composer Lite, Task Decomposition, Squad Execution Plan, Squad E2E Flow.
> Roadmap abaixo reflete P8+.

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

## Nao Implementar Nesta Fase

- LangGraph
- CrewAI
- OpenHands
- Meta API / Instagram
- OAuth
- Qualquer chamada de rede
- Agentes reais
- Execucao real de tarefas
