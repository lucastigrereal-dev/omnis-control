# OMNIS Current State

**Atualizado:** 2026-05-22 — Fase 1: Portabilidade + MODULES.md + Arquivamento FANTASMA/LEGADO
**Branch:** feature/omnis-5waves-runtime-supreme
**Último commit:** 62cf55e — chore(fase-1): portabilidade + arquivamento de módulos FANTASMA/LEGADO

## Status Geral
Fase: OMNIS_LOCAL_SUPREME_COMPLETE — 11 fases (0-10) concluídas. 30/30 outputs reais gerados. Fábrica local autônoma operacional.

## Roadmap Ativo
G14 App Factory (Supreme 210) — CONCLUÍDO
Fase F (Cockpit HTML local) — CONCLUÍDO

## Entregas por Domínio

| Domínio | Waves | Status |
|---|---|---|
| G01-G13 | W001-W130 | DONE |
| AppFactory Inicial | W131-W132 | DONE |
| AppFactory Advanced | W133-W162 | DONE (em master, 06caa49) |
| Runtime Missions | W181-W195 | DONE |
| Health (canonical) | W196-W200 | DONE — omnis_health é o módulo canônico real |
| Maintenance | W201-W205 | MERGED |
| Templates + QA | W206-W215 | REDUNDANT_ARCHIVE_RECOMMENDED (0 commits únicos) |
| RuntimeBridge | P37-P42 | DONE — 26/26 testes passando |
| Project OS | Governança | DONE V2 |

## Health — Estado Canônico (Wave A corrigido 2026-05-22)
- `src/omnis_health/` — módulo REAL e canônico (modelos, HealthReport, HealthStatus)
- `src/health_bridge/` — DELETADO (estava vazio — W196-W200 nunca implementou o módulo)
- `tests/health_bridge/` — DELETADO (estava vazio — sem nenhum teste real)
- `tests/omnis_health/` — 49 testes passando (contagem anterior de 58 era incorreta)
- P1 health_bridge_superseded: FECHADO definitivo — diretórios fantasmas removidos.

## RuntimeBridge P37-P42
- `src/runtime_bridge/` — bridge.py + models.py + errors.py
- Conecta ExecutionGraph StepRun → ExecutionQueue
- 26/26 testes passando
- Status: DONE

## Suite (2026-05-22 — verdade do disco)
- runtime_bridge: 26/26
- omnis_health: 49/49 (health_bridge era fantasma — removido)
- skills_bridge: 36 testes (antes em dir mal nomeado `skill_router_bridge` — corrigido)
- Suite completa: **8830 passed, 3 skipped, 0 failed** (73 testes movidos para tests/_archive/)
- 18 novos arquivos de teste de caracterização criados pelo Codex (Wave Codex)

## Working Tree
- reports/ccos/*.log + *.md → ignorados via .gitignore (DONE)
- config/paths.yaml → timestamp update (commitado)
- docs/ESTADO_ATUAL_RESUMIDO.md → atualizado (commitado)
- docs/disk_audit_report.json → atualizado (commitado)

## Bloqueadores
- P0 LiteLLM: código ok, rotação de chave externa — AÇÃO HUMANA NECESSÁRIA
- P0 não bloqueia merge local

## Travas de Merge Ativas
- 🔴 `feature/kratos-0-10-operational-truth` — **BLOQUEADA** (60 falhas, T-006 pendente)
- Ver: `docs/project-os/MERGE_LOCKS.md`

## Fase 1 — Concluída (2026-05-22)
- PASSO 1: docs/project-os/MODULES.md gerado (21 CORE + 46 SUPPORT + 20 EXP + 25 DUP + 6 LEG + 2 FAN)
- PASSO 2: 23 arquivos src/ portabilizados (os.getenv OMNIS_ROOT + CLAUDE_DIR + 4 outros)
- PASSO 3: 6 módulos arquivados → src/_archive/ + tests/_archive/ (backlog, executors, omnis_control, parallel_runner, governance_core, health)

## Próxima Ação (aguardando GO do Lucas)
- Fase 2: decisão sobre famílias de drift (Mission, Execution, Provider, Memory, Approval)
- Quando Lucas der GO: reconciliar uma família por vez (começar por reports/status_report.py)
