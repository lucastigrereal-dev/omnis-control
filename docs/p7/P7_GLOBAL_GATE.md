# P7 Global Gate — Squad Composer Lite

**Data:** 2026-05-09
**Branch:** master
**Commit baseline:** a5a585b (P6 Seal)
**Suite baseline:** 1628 passed, 4 skipped, 0 failures
**Tests collected:** 1632

---

## Estado da working tree

Arquivos sujos fora do escopo P7 (pré-existentes, NÃO commitar):
- `config/paths.yaml` (modificado, fora do escopo)
- `docs/ESTADO_ATUAL_RESUMIDO.md` (modificado, fora do escopo)
- `docs/disk_audit_report.json` (modificado, fora do escopo)
- `docs/RELATORIO_COMPLETO_2026.md` (untracked, fora do escopo)

---

## CLI P6 disponíveis

| Comando | Status |
|---|---|
| `jarvis.py orchestrator` | ativo |
| `jarvis.py sector-registry` | ativo |
| `jarvis.py skill-matcher` | ativo |
| `jarvis.py capability-gap` | ativo |
| `jarvis.py forge-lite` | ativo (P6) |
| `jarvis.py approvals-center` | ativo |

---

## Módulos P6 disponíveis para P7

- `src/capability_forge_lite/` — proposal → spec → approval → register
- `src/capability_gap/` — gap detection
- `src/skill_matcher/` — keyword matching (com include_planned)
- `src/sector_registry/` — 7 setores
- `src/approval_center/` — state machine pending/approved/rejected
- `src/mission_orchestrator/` — planner + executor + approval gate

---

## Objetivos P7 (5 blocos)

| Bloco | Objetivo |
|---|---|
| P7.0 | Role Registry — catálogo declarativo de papéis operacionais |
| P7.1 | Squad Composer Lite — composição local de squads por pedido |
| P7.2 | Task Decomposition Lite — decomposição determinística de tarefas |
| P7.3 | Squad Execution Plan Dry-Run — manifesto de execução sem agentes reais |
| P7.4 | Squad E2E Flow — validação end-to-end completa |

---

## Bloqueios ativos (herdados)

- **OAuth Meta** — congelado por decisão estratégica
- **Post real** — NO-GO até OAuth + revisão humana

---

## Regras P7

- NÃO usar CrewAI, LangGraph, OpenHands
- NÃO chamar LLM
- NÃO executar agentes reais
- NÃO publicar
- NÃO chamar Meta/OAuth
- Pipeline: determinístico, local, testado
