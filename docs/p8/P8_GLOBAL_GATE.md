# P8 Global Gate — Execution Graph Lite

**Data:** 2026-05-09
**Branch:** master
**Commit baseline:** ec215b9 (P7 Final Seal)
**Suite baseline:** 1723 collected, 121/121 P7 validated
**Tests acumulados:** ~1,341

---

## Estado da working tree

Arquivos sujos fora do escopo P8 (pré-existentes, NÃO commitar):
- `config/paths.yaml` (modificado, fora do escopo)
- `docs/ESTADO_ATUAL_RESUMIDO.md` (modificado, fora do escopo)
- `docs/disk_audit_report.json` (modificado, fora do escopo)
- `docs/RELATORIO_COMPLETO_2026.md` (untracked, fora do escopo)

---

## CLI P7 disponíveis

| Comando | Status |
|---|---|
| `jarvis.py orchestrator` | ativo |
| `jarvis.py sector-registry` | ativo |
| `jarvis.py skill-matcher` | ativo |
| `jarvis.py capability-gap` | ativo |
| `jarvis.py forge-lite` | ativo (P6) |
| `jarvis.py approvals-center` | ativo |
| `jarvis.py role-registry` | ativo (P7) |
| `jarvis.py squad` | ativo (P7) |
| `jarvis.py tasks-plan` | ativo (P7) |
| `jarvis.py squad-run` | ativo (P7) |

---

## Módulos P7 disponíveis para P8

- `src/role_registry/` — 12 roles YAML, loader, matcher
- `src/squad_composer/` — composição determinística de squads
- `src/task_decomposer/` — decomposição + cycle detection + topological sort
- `src/squad_execution/` — dry-run manifests, exporter, approval gate
- `src/sector_registry/` — 7 setores
- `src/skill_matcher/` — keyword matching
- `src/approval_center/` — state machine

---

## Objetivos P8 (7 blocos)

| Bloco | Objetivo |
|---|---|
| P8.0 | Execution Graph Models + Builder — DAG de nós com estados |
| P8.1 | Step Runner Dry-Run — simulação de execução por role |
| P8.2 | Replay / Resume — retomar runs interrompidos |
| P8.3 | Approval-Integrated Graph Run — bridge approval ↔ execution |
| P8.4 | Event Log + Metrics — JSONL append-only + métricas básicas |
| P8.5 | Mission → Squad → Graph Integration — conectar P3+P7+P8 |
| P8.6 | E2E Mission → Squad → Graph → Approval — validação completa |
| P8.7 | Final Seal — milestone documentation |

---

## Bloqueios ativos (herdados)

- **OAuth Meta** — congelado por decisão estratégica
- **Post real** — NO-GO até OAuth + revisão humana
- **CrewAI / LangGraph / OpenHands** — não usados, não permitidos

---

## Regras P8

- NÃO usar CrewAI, LangGraph, OpenHands
- NÃO chamar LLM
- NÃO executar agentes reais
- NÃO publicar
- NÃO chamar Meta/OAuth
- NÃO ler .env
- Pipeline: determinístico, local, testado
- Steps simulados: timestamps falsos, status fake, sem side effects
