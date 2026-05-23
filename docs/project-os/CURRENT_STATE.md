# OMNIS Current State

**Atualizado:** 2026-05-23 — Fases 1-14 completas: Consolidação + API HTTP + Agente + LLM real + Observabilidade
**Branch:** feature/omnis-5waves-runtime-supreme
**Último commit:** 93739d7 — docs(audit): Codex audit results — dead code map + consolidation proposal

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

## Suite (2026-05-23 — verdade do disco)
- runtime_bridge: 26/26
- omnis_health: 49/49
- skills_bridge: 36/36
- api (Fase 3 + 11 + 14): 56/56
- agent_models (Fase 4): 15/15
- caption_draft_agent (Fase 4 + 13-B): 34/34
- memory_interface (Fase 4): 8/8
- llm_adapter (Fase 5 + 13-B): 19/19
- scheduler (Fase 6-10): 62/62
- batch_runner (Fase 9): 28/28
- cli_agent (Fase 12 + 13-B + 14): 34/34
- Suite completa: **~8542 passed, 4 skipped, 0 failed**

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

## Fases Concluídas

### Fase 1 — Consolidação (2026-05-22, commit 62cf55e)
- PASSO 1: docs/project-os/MODULES.md gerado (21 CORE + 46 SUPPORT + 20 EXP + 25 DUP + 6 LEG + 2 FAN)
- PASSO 2: 23 arquivos src/ portabilizados (os.getenv OMNIS_ROOT + CLAUDE_DIR + 4 outros) + .env.example
- PASSO 3: 6 módulos FANTASMA/LEGADO arquivados → src/_archive/

### Fase 2 — Limpeza Cirúrgica (2026-05-22)
- 14 módulos DUPLICADO/FANTASMA arquivados → src/_archive/ + tests/_archive/
- 3 integration tests arquivados (importavam módulos removidos)

### Fase 3 — API HTTP mínima (2026-05-23, commit 4ab9f18)
- `src/api/main.py` — FastAPI read-only, CORS allow_methods=["GET"]
- 8 routers: health, queue, accounts, drafts, assets, missions, skills, reports
- 34 testes API passando

### Fase 4 — Agente mínimo real (2026-05-23, commit f7423a0)
- `src/agentic/agent_models.py` — AgentRun + AgentStep + AgentRunRepository (JSONL)
- `src/memory/interface.py` — MemoryInterface dry_run safe
- `src/agentic/caption_draft_agent.py` — loop QueueItem → memory → draft → AgentRun
- 37 testes novos passando

### Fases 5-10 — LLM + Scheduler + Batch (2026-05-23)
- Fase 5: `LiteLLMAdapter` + `MockLLMAdapter` + `CaptionLLMOutput`
- Fase 6: `BatchSchedule` + `ScheduleRepository` (JSONL)
- Fase 7: `ScheduleRunRepository` + histórico de execuções
- Fase 8: `SchedulerService.run_due()` — executa schedules vencidos
- Fase 9: `BatchRunner.run_batch()` — processa fila com CaptionDraftAgent
- Fase 10: `CaptionMemoryWriter/Reader` + memória de legendas aprovadas
- CLI: `omnis agent batch`, `schedule-add/list/run/history/remove`

### Fase 11 — API /agent/* (2026-05-23, commit 3c9c1c9)
- `src/api/routers/agent.py` — 6 endpoints GET-only para KRATOS
- GET /agent/runs, /agent/runs/{id}, /agent/schedules, /agent/schedules/{id}/history, /agent/memory, /agent/status
- 22 testes API passando

### Fase 12 — `omnis agent status` (2026-05-23, commit 69ec955)
- Dashboard one-shot: queue + runs + schedules + memory + litellm_available
- `--json` flag para integração KRATOS
- 12 testes CLI passando

### Fase 13-B — LiteLLM health_check + _parse_response + --real wire (2026-05-23, commit 097a836)
- `LiteLLMAdapter.health_check()` — ping :4002/health, 3s timeout, returns bool
- `LiteLLMAdapter._parse_response()` — static method, testável sem HTTP
- `CaptionDraftAgent` com LLM failure handling (URLError + socket.timeout)
- 9 novos testes adapter + 4 testes agent failure

### Fase 14 — --real guard + GET /agent/status litellm_available (2026-05-23, commit 3c9c1c9)
- `_require_litellm()` guard no CLI: bloqueia --real quando LiteLLM indisponível
- `GET /agent/status` inclui `litellm_available` bool
- 5 novos testes guard + 8 novos testes API status

### Codex Audit (2026-05-23, commit 93739d7)
- `docs/project-os/DEAD_CODE_AUDIT.md` — 107 VIVO, 6 SUSPEITO, 4 FANTASMA, 0 violações LLM
- `docs/project-os/CODEX_SRC_CONSOLIDATION_PROPOSAL.md` — fronteiras limpas confirmadas
- `docs/project-os/AGENT_FLOW.md` — fluxo end-to-end documentado

## Próxima Ação
- Wave seguinte do WAVE_REGISTRY — ver `docs/project-os/WAVE_REGISTRY.md`
- Candidatos: aprovação humana de rascunhos (ApprovalGate UI), pipeline multi-conta, ou scheduling cron real
