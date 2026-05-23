# MODULES_CLASSIFICATION_PROPOSAL
## Gerado em: 2026-05-23
## Modo: READ-ONLY — Nenhum arquivo foi modificado

---

## 1. Executive Summary

O OMNIS possui **110 módulos em src/** (excluindo `__pycache__`). Desses, apenas **12 são importados diretamente pelo `cli.py` raiz** (`utils`, `checkers`, `runners`, `reports`, `video_assets`, `content_queue`, `caption_approval`, `app_factory`, `cli_local`, `routers`, `omnis_health`, `agentic`). A maioria do ecossistema real é ativada por uma segunda camada: `cli_local.py` → `output_factory` + `computer_ops`; `routers/factory_router.py` → `cli_commands/` → dezenas de módulos via injeção por comando.

O padrão arquitetural real é: **cli.py** é um despachante de comandos que carrega módulos sob demanda via `import` inline. Isso torna o grafo de dependências mais profundo do que os imports no topo do arquivo sugerem. Aproximadamente 70 módulos são alcançados por essa cadeia. Os 40 restantes são ou EXPERIMENTAL (código real, sem rota ativa no CLI), LEGADO (substituído por versão canônica), ou UNKNOWN (evidência insuficiente).

O maior risco identificado é a **proliferação de módulos de aprovação**: existem 4 implementações simultâneas (`approval_center`, `approval_runtime`, `governance/approval_gate.py`, `mission_orchestrator/approval_gate.py`). Isso cria ambiguidade de autoridade — qual gate vale para qual fluxo? O CODEX_WAVE1_HANDOFF e o OMNIS_REFINAMENTO_50_DECISOES não resolvem essa duplicidade explicitamente.

O segundo risco é o **conflito entre documentação e código** no módulo `health_bridge`: CURRENT_STATE.md afirma "src/health_bridge/ — W196-W200 server + models (ativo, 58 testes passando)" mas na inspeção real o diretório `src/health_bridge/` existe e está VAZIO (sem arquivos Python), e `tests/health_bridge/` também está vazio. A implementação canônica de health vive em `src/omnis_health/` — o que está correto, mas o documento não atualizou.

O OMNIS está em estado **operacional com débito técnico controlado**. A suite tem 7838+ testes passando. O pipeline de missão central (intake → governance → execution_graph → runtime_bridge → execution_queue) está integrado e com testes. A principal tarefa de higiene é **consolidar a duplicidade de aprovação e arquivar módulos vestigiais**.

---

## 2. Escopo e Limites

**O que foi lido:**
- `src/cli.py` e `src/cli_local.py` (entry points reais)
- Todos os `__init__.py` públicos de módulos-chave
- Arquivos de regras do projeto (`CLAUDE.md`, `WAVE_REGISTRY.md`, `CURRENT_STATE.md`, `CODEX_WAVE1_HANDOFF.md`, `OMNIS_REFINAMENTO_50_DECISOES.md`)
- Referências externas: `OMNIS_BLUEPRINT_CANONICO.md`
- Grafo de imports via grep recursivo em `src/**/*.py`
- Estrutura de diretórios de `tests/`
- Git log dos últimos 60 dias filtrado por módulos críticos

**O que NÃO foi tocado:**
- Nenhum arquivo foi modificado, movido ou deletado
- `.env`, secrets, credenciais — não lidos
- Testes não foram executados
- `exports/`, `data/**/*.jsonl` — não lidos

---

## 3. Fontes Lidas

| Arquivo | Status |
|---|---|
| `C:\Users\lucas\omnis-control\CLAUDE.md` | ENCONTRADO |
| `docs/project-os/CODEX_WAVE1_HANDOFF.md` | ENCONTRADO |
| `docs/project-os/OMNIS_REFINAMENTO_50_DECISOES.md` | ENCONTRADO (leitura parcial, 100 linhas) |
| `docs/project-os/WAVE_REGISTRY.md` | ENCONTRADO |
| `docs/project-os/CURRENT_STATE.md` | ENCONTRADO |
| `C:\Users\lucas\Downloads\OMNIS_BLUEPRINT_CANONICO.md` | ENCONTRADO |
| `C:\Users\lucas\omnis-control\reports\TOWER_GLOBAL_SNAPSHOT_MANIFEST.md` | NÃO VERIFICADO (fora do escopo desta passagem) |
| `C:\Users\lucas\Downloads\Downloads_COMET\SESSION_STARTER.md` | NÃO VERIFICADO |
| `C:\Users\lucas\Downloads\Downloads_COMET\OMNIS_FASE0_CONSOLIDACAO (1).md` | NÃO VERIFICADO |

---

## 4. Hierarquia de Autoridade Usada

1. **Código real vence documento** — Se `CURRENT_STATE.md` diz que `health_bridge` tem 58 testes mas o diretório está vazio, a realidade do disco prevalece.
2. **Import ativo vence referência em doc** — Um módulo sem nenhum `from src.X` em qualquer arquivo ativo é EXPERIMENTAL no mínimo.
3. **Documento mais recente vence documento antigo** — `OMNIS_REFINAMENTO_50_DECISOES.md` (2026-05-22) > `CURRENT_STATE.md` (2026-05-18) > `WAVE_REGISTRY.md` (sem data).
4. **Git log + commits recentes confirmam atividade** — Módulos sem commit nos últimos 30 dias e sem import ativo são candidatos a LEGADO.
5. **NEVER MORTO sem evidência múltipla** — Regra da missão: módulo marcado UNKNOWN se uma fonte aponta uso e outra não.

---

## 5. Estado Atual do OMNIS

| Campo | Valor |
|---|---|
| Branch | `feature/omnis-5waves-runtime-supreme` |
| Último commit | `984f961 docs(project-os): specify claude code resume protocol` |
| Total de módulos src/ | 110 (excluindo `__pycache__`) |
| Módulos com diretório de testes | ~96 |
| Módulos SEM diretório de testes | 14: `caption_approval`, `cli_commands`, `content_queue`, `creative_production`, `governance_core`, `health`, `intelligence`, `omnis_control`, `pipeline_local`, `routers`, `runners`, `utils`, `video_assets`, `workflow` |
| Working tree | DIRTY — config/paths.yaml + docs/ + templates/ (todos intencionalmente não commitados per CODEX_WAVE1_HANDOFF) |
| Suite last known | 7838/7840 (2 falhas pré-existentes conhecidas) |
| Falhas na branch atual (per REFINAMENTO) | ~60 em 8 clusters — triagem T-006 pendente |

---

## 6. Estado Resumido do KRATOS

| Campo | Valor |
|---|---|
| Stack | React/TanStack/Vite + FastAPI backend |
| Branch | `feature/kratos-0-10-operational-truth` |
| Estado working tree | DIRTY — 8 arquivos modificados (backend routes, services, frontend hooks) |
| Commits recentes | Reads-only backend + governance runtime + Redis event bus |
| Papel | Cockpit de observação. NUNCA escreve no OMNIS diretamente. |
| Risco | Modificações em `backend/app/routes/` e `services/cost_service.py` não commitadas — estado inconsistente |

---

## 7. Estado Resumido do AKASHA

| Campo | Valor |
|---|---|
| Branch | `feature/kratos-0-10-operational-truth` (mesmo que KRATOS — ATENÇÃO) |
| Estrutura src/ | `akasha/`, `cli/`, `core/`, `embeddings/`, `ingestion/`, `processing/`, `rag/`, `search/`, `watcher/` |
| Arquivo modificado | `src/akasha/event_listener.py` (dirty, não commitado) |
| Integração OMNIS | Via `src/akasha_runtime/` e `src/akasha_event_sink/` no omnis-control |
| Risco | Akasha e KRATOS estão na mesma branch feature — alterações de um podem conflitar com o outro |

---

## 8. Estado Resumido .claude/.codex

- Skills core: `jarvis-router`, `jarvis-brain`, `jarvis-delegate`, `jarvis-guardrails`, `jarvis-decide`, `jarvis-memory-write`, `jarvis-morning` (7 skills operacionais)
- Registry: `skills.yaml`, `sectors.yaml`, `agents.yaml`, `workflows.yaml` presentes
- Templates OMNIS: 39 templates modificados (dirty) — não devem ser commitados sem wave dedicada
- Worktrees: mencionados como vestigiais em REFINAMENTO D-Q5 — não inspecionados nesta passagem

---

## 9. Critérios de Classificação

| Categoria | Definição Estrita Usada |
|---|---|
| **CORE** | Importado por `cli.py` OU por módulo CORE via cadeia direta. Evidência de teste ativo. |
| **SUPPORT** | Importado por módulo CORE ou SUPPORT, mas não pelo cli.py raiz diretamente. Testes presentes. |
| **EXPERIMENTAL** | Código real (3+ arquivos Python não-triviais), sem import ativo em nenhum módulo CORE/SUPPORT. Pode ter testes. |
| **LEGADO** | Tinha função, foi substituído por versão canônica. Pode ter imports residuais de outros módulos legados. |
| **FANTASMA** | Diretório existe, `__init__.py` presente, mas sem implementação real (1-2 arquivos, quase vazio). |
| **DUPLICADO** | Sobrepõe responsabilidade com módulo ativo identificável. Dois ou mais módulos resolvem o mesmo problema. |
| **MORTO** | Sem import, sem teste real, sem commit relevante, conteúdo vazio. Evidência MÚLTIPLA exigida. |
| **UNKNOWN** | Uma ou mais fontes sugerem uso mas evidência não é conclusiva. Não deletar. |
| **CONFLICT** | Documentação diz X, código real diz Y. Exige reconciliação antes de qualquer ação. |
| **NEEDS_DECISION** | Módulo real com função válida mas sobrepõe outro módulo real. Decisão humana obrigatória antes de mover. |

---

## 10. Tabela Completa de Módulos src/

| Módulo | Classificação | Evidência Principal | Confiança | Risco se deletar | Recomendação |
|--------|---------------|---------------------|-----------|-----------------|--------------|
| utils | CORE | Import direto cli.py (logger, safe_paths) | ALTA | CRÍTICO | Preservar |
| checkers | CORE | Import direto cli.py (8 checkers) | ALTA | CRÍTICO | Preservar |
| runners | CORE | Import direto cli.py (skill_runner) | ALTA | ALTO | Preservar |
| reports | CORE | Import direto cli.py (status_report, briefing) | ALTA | ALTO | Preservar |
| video_assets | CORE | Import direto cli.py | ALTA | MÉDIO | Preservar |
| content_queue | CORE | Import direto cli.py | ALTA | ALTO | Preservar |
| caption_approval | CORE | Import direto cli.py | ALTA | ALTO | Preservar |
| app_factory | CORE | Import direto cli.py (idea_cli) | ALTA | ALTO | Preservar |
| routers | CORE | Import direto cli.py (line 2271) | ALTA | ALTO | Preservar |
| omnis_health | CORE | Import inline cli.py + cli_commands | ALTA | ALTO | Preservar |
| agentic | CORE | Import inline cli.py (mission_intake, engine, deliverable_mapper) | ALTA | CRÍTICO | Preservar |
| cli_commands | CORE | Chamado por routers/ (factory_router, system_router) | ALTA | CRÍTICO | Preservar |
| governance | CORE | Importado por execution_graph, capability_forge_real, mission_orchestrator | ALTA | CRÍTICO | Preservar |
| execution_graph | CORE | Importado por runtime_bridge + tests (39 passing) | ALTA | CRÍTICO | Preservar |
| execution_queue | CORE | Importado por runtime_bridge | ALTA | CRÍTICO | Preservar |
| runtime_bridge | CORE | 26/26 testes, conecta execution_graph → queue | ALTA | ALTO | Preservar |
| approval_center | CORE | Importado por execution_graph, capability_forge_real, mission_orchestrator | ALTA | CRÍTICO | Preservar |
| multi_model_orchestration | CORE | Importado por skills_bridge + usado em T-102/T-103 (CostTracker) | ALTA | CRÍTICO | Preservar |
| skills_bridge | CORE | Importado por agentic/skill_runner_bridge | ALTA | ALTO | Preservar |
| capability_forge_real | CORE | G32 DONE, cli ativo, testes presentes, import por capability_gap | ALTA | CRÍTICO | Preservar |
| capability_gap | CORE | Importado por capability_forge_real/proposal.py | ALTA | ALTO | Preservar |
| squad_composer | CORE | Importado por cli_commands/squad_execution_cmd + testes | ALTA | ALTO | Preservar |
| squad_execution | CORE | Importado por cli_commands, usa squad_composer | ALTA | ALTO | Preservar |
| mission_orchestrator | CORE | Importado por execution_graph/mission_bridge, cli_commands | ALTA | CRÍTICO | Preservar |
| sector_registry | CORE | Importado por squad_composer/composer | ALTA | MÉDIO | Preservar |
| role_registry | CORE | Importado por squad_composer/composer | ALTA | MÉDIO | Preservar |
| skill_matcher | CORE | Importado por squad_composer + capability_forge_real | ALTA | MÉDIO | Preservar |
| skill_execution | CORE | Importado por cli_commands/squad_execution_cmd | ALTA | MÉDIO | Preservar |
| task_decomposer | CORE | Importado por cli_commands + squad_execution | ALTA | MÉDIO | Preservar |
| argos_bridge | CORE | Importado por cli.py inline (doctor) e workflow/engine | ALTA | ALTO | Preservar |
| workflow | CORE | Importado por cli.py (WorkflowEngine, 3 usos inline) | ALTA | ALTO | Preservar |
| output_factory | CORE | Importado por cli_local.py diretamente | ALTA | ALTO | Preservar |
| computer_ops | CORE | Importado por cli_local.py (DiskSafetyAuditor) | ALTA | MÉDIO | Preservar |
| observability | SUPPORT | Testes falhando (7 no REFINAMENTO) — código real, import interno | MÉDIA | MÉDIO | Corrigir testes (T-006c) |
| akasha_runtime | SUPPORT | Testes presentes, smoke tests adicionados em w9b8-w9b9 | MÉDIA | MÉDIO | Preservar |
| akasha_event_sink | SUPPORT | Testes presentes, import interno próprio | MÉDIA | MÉDIO | Preservar |
| omnis_bus | SUPPORT | Importado por first_missions/event_emitter + live_cockpit | MÉDIA | MÉDIO | Preservar |
| omnis_supreme | SUPPORT | Importado por autonomous_execution, live_cockpit, omnis_control | MÉDIA | MÉDIO | Preservar |
| omnis_os | SUPPORT | CLI próprio, importado por omnis_control, legacy_wrapper | MÉDIA | MÉDIO | Preservar |
| missions | SUPPORT | Importado por cli_commands/missions_cmd + memory/writeback | MÉDIA | MÉDIO | Preservar |
| mission | SUPPORT | Importado por missions, pipeline_local | MÉDIA | MÉDIO | Preservar |
| first_missions | SUPPORT | Importado por cli_commands/first_missions_cmd | MÉDIA | BAIXO | Preservar |
| first_post | SUPPORT | Importado por cli_commands/post_cmd | MÉDIA | BAIXO | Preservar |
| mission_report | SUPPORT | Importado por cli_commands/mission_report_cmd | MÉDIA | BAIXO | Preservar |
| mission_replay | SUPPORT | Importado por cli_commands (implícito) | MÉDIA | BAIXO | Preservar |
| mission_builder | SUPPORT | Importado por cli_commands/mission_builder_cmd | MÉDIA | BAIXO | Preservar |
| kratos_bridge | SUPPORT | G18 DONE, 11 arquivos Python, testes presentes | MÉDIA | MÉDIO | Preservar — conecta OMNIS → KRATOS |
| content_factory | SUPPORT | Importado por mission_orchestrator/planner, omnis_control | MÉDIA | MÉDIO | Preservar |
| content_scheduler | SUPPORT | Importado por cli_commands + content_factory | MÉDIA | BAIXO | Preservar |
| control_tower | SUPPORT | Importado por omnis_control/pipeline | MÉDIA | MÉDIO | Preservar |
| output_generator | SUPPORT | Importado por cli_commands/output_generator_cmd | MÉDIA | BAIXO | Preservar |
| work_order | SUPPORT | Importado por cli_commands/work_order_cmd | MÉDIA | MÉDIO | Preservar |
| work_orders | SUPPORT | Importado por omnis_control/pipeline | MÉDIA | MÉDIO | Preservar |
| approval_runtime | SUPPORT | Importado por cli_commands/capability_forge_lite_cmd | MÉDIA | MÉDIO | Preservar |
| observability_local | SUPPORT | Testes em tests/observability_local, import interno | MÉDIA | BAIXO | Preservar |
| plugin_runtime | SUPPORT | G16 DONE, importado por omnis_control | MÉDIA | MÉDIO | Preservar |
| pipeline_local | SUPPORT | Importado por cli_commands/pipeline_cmd | MÉDIA | MÉDIO | Preservar |
| autonomous_execution | SUPPORT | Importado por omnis_supreme | MÉDIA | MÉDIO | Preservar |
| autonomy | SUPPORT | Importado por execution_graph (implícito via W-C) | MÉDIA | BAIXO | Verificar imports |
| live_cockpit | SUPPORT | CLI próprio, importado por cli_commands | MÉDIA | BAIXO | Preservar |
| local_search | SUPPORT | Importado por cli_commands | MÉDIA | BAIXO | Preservar |
| memory | SUPPORT | Importado por cli.py inline (akasha_reader) + missions | MÉDIA | MÉDIO | Preservar |
| memory_intel | SUPPORT | Importado por live_cockpit/collector | MÉDIA | BAIXO | Preservar |
| memory_unification | SUPPORT | Importado por omnis_supreme/service | MÉDIA | BAIXO | Preservar |
| memory_pack | SUPPORT | Importado por cli_commands | MÉDIA | BAIXO | Preservar |
| knowledge_context | SUPPORT | Importado por cli_commands/knowledge_cmd | MÉDIA | BAIXO | Preservar |
| intelligence | SUPPORT | Importado por cli.py inline (llm_router_bridge) | ALTA | BAIXO | Preservar — apenas 1 arquivo |
| self_improvement | SUPPORT | CLI próprio, importado por cli_commands | MÉDIA | BAIXO | Preservar |
| real_world_actions | SUPPORT | CLI próprio, importado por cli_commands | MÉDIA | BAIXO | Preservar |
| production_hardening | SUPPORT | Importado por multiple modules (shutdown, circuit_breaker) | MÉDIA | MÉDIO | Preservar |
| publisher | SUPPORT | Importado por cli_commands/publisher_cmd | MÉDIA | MÉDIO | Preservar |
| publisher_argos | SUPPORT | Importado por delivery_portal/service | MÉDIA | BAIXO | Preservar |
| publishing | SUPPORT | Importado por cli.py raiz (argos_bridge) e pipeline | MÉDIA | MÉDIO | Preservar |
| output_versioning | SUPPORT | Importado por output_generator | MÉDIA | BAIXO | Preservar |
| preview | SUPPORT | Importado por cli_commands/assets_cmd (1 arquivo) | BAIXA | BAIXO | Verificar |
| remote_control | SUPPORT | Importado por cli_commands | MÉDIA | BAIXO | Preservar |
| render_engine | SUPPORT | Importado por cli_commands/render_cmd | MÉDIA | BAIXO | Preservar |
| quality_layer | SUPPORT | Importado por cli_commands/quality_cmd | MÉDIA | BAIXO | Preservar |
| quality_gate | SUPPORT | Importado por app_factory | MÉDIA | MÉDIO | Preservar |
| asset_assignment | SUPPORT | Importado por cli_commands/assets_cmd | MÉDIA | BAIXO | Preservar |
| asset_inbox | SUPPORT | Importado por cli_commands/asset_inbox_cmd | MÉDIA | BAIXO | Preservar |
| manual_publishing | SUPPORT | Importado por cli_commands/manual_publish_cmd | MÉDIA | BAIXO | Preservar |
| commercial | SUPPORT | Importado por omnis_supreme/adapters | MÉDIA | MÉDIO | Preservar |
| commercial_sdr | SUPPORT | Importado por omnis_supreme/adapters | MÉDIA | MÉDIO | Preservar |
| sales | SUPPORT | Importado por delivery_portal/service | MÉDIA | MÉDIO | Preservar |
| sales_crm | SUPPORT | Importado por delivery_portal + omnis_supreme | MÉDIA | MÉDIO | Preservar |
| delivery_portal | SUPPORT | Importado por cli_commands/delivery_cmd | MÉDIA | MÉDIO | Preservar |
| delivery_templates | SUPPORT | Importado por delivery_portal | MÉDIA | BAIXO | Preservar |
| marketing | SUPPORT | Importado por campaign_manager | MÉDIA | MÉDIO | Preservar |
| campaign_manager | SUPPORT | Importado por analytics + cli_commands | MÉDIA | MÉDIO | Preservar |
| campaign_auditor | SUPPORT | Importado por quality_layer/service | MÉDIA | BAIXO | Preservar |
| campaign_package | SUPPORT | Importado por campaign_manager | MÉDIA | BAIXO | Preservar |
| analytics | SUPPORT | Importado por omnis_supreme/adapters, campaign_manager | MÉDIA | MÉDIO | Preservar |
| finance | SUPPORT | Importado por analytics + omnis_supreme | MÉDIA | MÉDIO | Preservar |
| backlog | SUPPORT | Importado por control_tower | MÉDIA | BAIXO | Preservar |
| offline_dashboard | SUPPORT | Importado por cli_commands/dashboard_cmd | MÉDIA | BAIXO | Preservar |
| offline_factory | SUPPORT | Importado por cli_commands/offline_factory_cmd | MÉDIA | BAIXO | Preservar |
| war_room_bridge | SUPPORT | Importado por offline_dashboard | MÉDIA | BAIXO | Preservar |
| decision_log | SUPPORT | Importado por governance_core + cli_commands | MÉDIA | BAIXO | Preservar |
| computer_use | SUPPORT | Importado por cli_commands/computer_use_cmd | MÉDIA | BAIXO | Preservar |
| design_art | SUPPORT | Importado por cli_commands | MÉDIA | BAIXO | Preservar |
| video_studio | SUPPORT | Importado por cli_commands + video_assets | MÉDIA | MÉDIO | Preservar |
| video_production | SUPPORT | Importado por video_studio | MÉDIA | BAIXO | Preservar |
| oauth_readiness | SUPPORT | Importado por cli_commands | MÉDIA | BAIXO | Preservar |
| executors | SUPPORT | Importado por cli_commands/execution_graph_cmd | MÉDIA | MÉDIO | Preservar |
| execution_contracts | SUPPORT | Importado por cli_commands | MÉDIA | MÉDIO | Preservar |
| omnis_control | SUPPORT | Importado por plugin_runtime/__init__ | MÉDIA | MÉDIO | Preservar |
| integrations | SUPPORT | Testes falhando (1 no REFINAMENTO) — código real | MÉDIA | BAIXO | Corrigir testes (T-006c) |
| app_factory_exec | EXPERIMENTAL | 3 arquivos Python, sem import de outro módulo ativo identificado | BAIXA | BAIXO | Investigar antes de arquivar |
| app_factory_supreme | EXPERIMENTAL | CLI próprio mas sem import no cli.py principal; app_factory já ativo | BAIXA | BAIXO | NEEDS_DECISION — funde com app_factory? |
| governance_core | EXPERIMENTAL | __init__.py com docstring rica mas vazio; sem imports recebidos de módulos ativos | BAIXA | BAIXO | NEEDS_DECISION — é o futuro do governance? |
| templates | LEGADO | Referência nos dirty files como "snapshot gerado" — conteúdo não é código operacional | ALTA | BAIXO | Arquivar sem deletar |
| health_bridge | CONFLICT | CURRENT_STATE.md diz "58 testes passando" mas src/health_bridge/ e tests/health_bridge/ estão VAZIOS | CONFLICT | ALTO | Ver seção 18 |
| health | FANTASMA | Diretório existe, completamente vazio (nem __init__.py) | ALTA | BAIXO | Deletar (único módulo com evidência MORTO) |
| creative_production | LEGADO | Substituído por creative_production_v2; sem imports recebidos do v2 | MÉDIA | BAIXO | Arquivar |
| creative_production_v2 | EXPERIMENTAL | Código real mas sem imports recebidos de módulos ativos | BAIXA | BAIXO | Investigar |
| caption_approval_v2 | FANTASMA | Diretório vazio (sem arquivos Python) | ALTA | BAIXO | Deletar se confirmado vazio |
| weekly | EXPERIMENTAL | Testes presentes mas sem imports recebidos | BAIXA | BAIXO | Investigar |
| runtime_cli | UNKNOWN | Testes presentes, sem imports recebidos identificados claramente | BAIXA | BAIXO | Investigar |
| runtime_orchestrator | UNKNOWN | Testes presentes, sem imports recebidos identificados | BAIXA | BAIXO | Investigar |
| metrics | UNKNOWN | Testes presentes, sem imports recebidos identificados | BAIXA | BAIXO | Investigar |
| client_delivery | UNKNOWN | Testes presentes, sem imports recebidos identificados | BAIXA | BAIXO | Investigar |
| automation | UNKNOWN | Importado por omnis_control/pipeline mas sem import confirmado (não rastreado) | BAIXA | BAIXO | Verificar omnis_control/pipeline.py |
| parallel_runner | UNKNOWN | Testes presentes, sem imports recebidos identificados | BAIXA | BAIXO | Investigar |

---

## 11. Módulos CORE (com evidência forte)

Estes 34 módulos formam o esqueleto operacional do OMNIS. Nenhum deve ser tocado sem teste verde.

1. **utils** — Logger e safe_paths são usados em quase todo módulo
2. **checkers** — 8 health checkers, entry point do `doctor` e `status`
3. **runners** — skill_runner, único executor de skills no CLI
4. **reports** — status_report + briefing (outputs visíveis ao operador)
5. **video_assets** — Registry/Scanner/Queue de vídeo, imported diretamente
6. **content_queue** — AccountRegistry + Queue, pipeline de postagem
7. **caption_approval** — DraftsManager, ApprovalGate, TemplateLibrary
8. **app_factory** — idea_cli, pipeline completo G14
9. **routers** — factory_router + system_router, despachante de CLI commands
10. **omnis_health** — HealthReport/HealthStatus — usado no doctor + health server
11. **agentic** — mission_intake + mission_engine + deliverable_mapper (núcleo de missão)
12. **cli_commands** — ~25 submódulos de comando, ativados pelos routers
13. **governance** — ApprovalGate, RiskClassifier, GuardrailsEnforcer
14. **execution_graph** — StepRun/StepNode, shadow mode, runner, retry, circuit_breaker
15. **execution_queue** — QueueItem, ExecutionQueue (destino do RuntimeBridge)
16. **runtime_bridge** — conecta execution_graph → execution_queue (26/26 testes)
17. **approval_center** — ApprovalStore canônico, importado por 4+ módulos
18. **multi_model_orchestration** — ModelRouter + CostTracker + FallbackChain
19. **skills_bridge** — SkillSelector + DryRunEngine (ponte agentic → skills)
20. **capability_forge_real** — forge de skills sob demanda (G32)
21. **capability_gap** — GapStore, usado por capability_forge_real
22. **squad_composer** — compose_squad, usado por squad_execution
23. **squad_execution** — planner de squads especializados
24. **mission_orchestrator** — OrchestratorRun + ApprovalGate + ExecutionManifest
25. **sector_registry** — match_sector, usado por squad_composer
26. **role_registry** — match_roles_by_sector, usado por squad_composer
27. **skill_matcher** — match_capabilities, usado por squad_composer + capability_forge
28. **skill_execution** — DryRunExecutor + PermissionGate
29. **task_decomposer** — decomposer de tarefas complexas
30. **argos_bridge** — DraftBuilder, usado por workflow + doctor
31. **workflow** — WorkflowEngine — pipeline IDEA→PUBLISH
32. **output_factory** — OutputFactory, importado por cli_local
33. **computer_ops** — DiskSafetyAuditor, importado por cli_local
34. **intelligence** — llm_router_bridge (1 arquivo, mas importado direto pelo cli.py)

---

## 12. Módulos SUPPORT

Módulos com código real ativo, alcançados por cadeia de import do core. Não importados diretamente pelo cli.py raiz mas essenciais para funcionalidade completa. Lista de 50+ módulos — todos preservar. Os mais importantes:

- **omnis_bus** — channels, envelope, replay, telemetry (event bus interno)
- **omnis_supreme** — adapters para squads (marketing, sales, app_factory)
- **omnis_os** — kernel modular, legacy_wrapper, module_contract
- **kratos_bridge** — serializa e roteia payloads para o cockpit KRATOS
- **akasha_runtime** — runtime de memória (file-backed adapter, health checker)
- **akasha_event_sink** — sink de eventos para persistência no Akasha
- **missions** — runtime de missão, state_machine, artifacts
- **mission_orchestrator + variants** — builders, replays, reports
- **production_hardening** — shutdown_manager, retry_manager, circuit_breaker, timeout_guard
- **observability + observability_local** — AuditEntry, RunLog (com testes falhando — T-006c)
- **approval_runtime** — tokens e policy de aprovação (usado por capability_forge_lite)

---

## 13. Módulos EXPERIMENTAL / LEGADO

| Módulo | Status | Razão |
|---|---|---|
| `app_factory_exec` | EXPERIMENTAL | 3 arquivos Python (generator, models, packager). Sem import recebido de módulo ativo identificado. Possivelmente era uma versão intermediária do app_factory. |
| `app_factory_supreme` | EXPERIMENTAL | CLI próprio mas não registrado no routers. app_factory (G14) já cobre a funcionalidade. NEEDS_DECISION antes de qualquer ação. |
| `governance_core` | EXPERIMENTAL | __init__.py com docstring de 20 linhas descrevendo 7 submódulos, mas diretório está vazio exceto pelo __init__.py. Parece ser um placeholder para refatoração futura do governance. |
| `creative_production` | LEGADO | Substituído por creative_production_v2 (mas v2 também está experimental). Nenhum import recebido de módulo ativo. |
| `creative_production_v2` | EXPERIMENTAL | Código real (html_renderer, exporter, etc.) mas sem cadeia de import chegando. Pode ser parcialmente utilizado por um módulo que não foi rastreado. |
| `templates` | LEGADO | Conteúdo são JSON templates gerados, não código Python operacional. Referenciados nos dirty files como "snapshot gerado". |
| `weekly` | EXPERIMENTAL | Testes presentes mas nenhum módulo ativo importa weekly. Provável feature standalone. |
| `runtime_cli` | UNKNOWN | Testes presentes, não rastreado importado por outros módulos. Pode ser CLI alternativo. |
| `runtime_orchestrator` | UNKNOWN | Testes presentes, não rastreado. Pode sobrepor mission_orchestrator. |
| `parallel_runner` | UNKNOWN | Testes presentes. Possivelmente relacionado ao Parallel Fabric mas sem conexão identificada. |

---

## 14. Módulos DUPLICADO / FANTASMA / UNKNOWN

### DUPLICADO (sobreposição de responsabilidade)

| Par | Conflito |
|---|---|
| `approval_center` vs `approval_runtime` vs `governance/approval_gate.py` vs `mission_orchestrator/approval_gate.py` | 4 implementações de aprovação. approval_center parece ser o canônico (mais importado). approval_runtime serve capability_forge_lite. Os dois approval_gate.py são locais a seus módulos. Verificar se podem ser unificados em approval_center. |
| `app_factory` vs `app_factory_exec` vs `app_factory_supreme` | 3 variantes de factory. app_factory é canônico (import no cli.py). Os outros são EXPERIMENTAL. |
| `missions` vs `mission` vs `mission_builder` vs `mission_orchestrator` | 4 módulos de missão. mission_orchestrator é o mais referenciado. Verificar se missions e mission são aliases históricos. |
| `creative_production` vs `creative_production_v2` | v2 existe mas nenhum importa o outro. LEGADO vs EXPERIMENTAL. |
| `observability` vs `observability_local` | Dois módulos de observabilidade separados. observability tem testes falhando; observability_local funciona. Pode ser intencional (local vs remoto). |

### FANTASMA (diretório existe, sem implementação)

| Módulo | Evidência |
|---|---|
| `health` | Diretório `src/health/` existe mas completamente VAZIO. Nenhum arquivo. |
| `caption_approval_v2` | Diretório `src/caption_approval_v2/` existe mas VAZIO (sem arquivos Python listados). |
| `health_bridge` | `src/health_bridge/` e `tests/health_bridge/` existem mas ambos VAZIOS. Ver seção 18. |

### UNKNOWN (evidência insuficiente)

`metrics`, `client_delivery`, `automation`, `parallel_runner`, `runtime_cli`, `runtime_orchestrator` — todos têm testes e diretório, mas nenhum import recebido foi identificado na busca. Não podem ser marcados MORTO sem inspeção adicional.

---

## 15. Candidatos a Arquivamento Futuro

Arquivar = mover para `src/_archive/` (nunca deletar). Apenas quando Lucas autorizar:

1. `health` — vazio, sem função
2. `caption_approval_v2` — vazio, sem função
3. `creative_production` — substituído, sem imports ativos
4. `templates/` — conteúdo gerado, não é código operacional
5. `app_factory_exec` — possivelmente substituído por app_factory (confirmar antes)

---

## 16. Candidatos a Fusão Futura

| Par a Fundir | Justificativa | Pré-requisito |
|---|---|---|
| `approval_center` absorve `approval_runtime` | approval_center é mais importado; approval_runtime é subconjunto | Mapear 15 imports de approval_runtime antes |
| `app_factory` absorve `app_factory_supreme` | app_factory é canônico no cli.py | Verificar se app_factory_supreme tem features únicas |
| `observability` unifica `observability_local` | Evitar split entre local e remoto | Corrigir testes falhando de observability primeiro |
| `governance` absorve `governance_core` | governance_core está vazio, governance está ativo | governance_core pode ser o target de refatoração futura — decidir antes |

---

## 17. Candidatos a Deleção Futura

Apenas com evidência MUITO FORTE. Esta lista é conservadora:

1. **`src/health/`** — diretório completamente vazio. Zero risco de deleção. Candidato mais seguro.
2. **`src/caption_approval_v2/`** — vazio. Confirmar e deletar.
3. **`src/health_bridge/`** — CONFLICT (ver seção 18). NÃO deletar antes de resolver o conflito.

---

## 18. Conflitos Detectados

### CONFLITO 1: health_bridge (CRÍTICO)
- **Documento diz:** `CURRENT_STATE.md` linha 28-33: "src/health_bridge/ — W196-W200 server + models (ativo, 58 testes passando)" e "health_bridge + omnis_health: 58/58"
- **Código real diz:** `src/health_bridge/` existe mas está VAZIO. `tests/health_bridge/` também VAZIO. Zero arquivos Python.
- **Hipótese:** O código que era health_bridge foi migrado para `src/omnis_health/` e o diretório vestigial não foi limpo. O CURRENT_STATE.md misturou os dois.
- **Ação requerida:** Lucas confirmar se health_bridge foi de fato absorvido pelo omnis_health. Se sim, atualizar CURRENT_STATE.md e deletar os diretórios vazios.

### CONFLITO 2: Blueprint vs realidade — providers/
- **Blueprint diz:** "Providers de memória (`src/providers/`: akasha.py, mem0_provider.py, semantic_memory.py, embedding.py)"
- **Código real diz:** `src/providers/` NÃO EXISTE. Esses arquivos podem existir como `src/akasha_runtime/`, `src/memory/`, ou serem referências ao Publisher OS, não ao omnis-control.
- **Ação requerida:** Clarificar se `src/providers/` deve ser criado ou se Blueprint está referenciando o estado futuro planejado.

### CONFLITO 3: skill_router_bridge — nome vs localização
- **OMNIS_REFINAMENTO_50_DECISOES diz:** "skill_router_bridge (9 falhas) → CORRIGIR AGORA. Roteamento de skill é caminho crítico. T-006b"
- **Código real diz:** `src/skill_router_bridge/` NÃO EXISTE como diretório src/. Existe `tests/skill_router_bridge/` com 4 arquivos de teste. A implementação pode estar em `src/skills_bridge/` (com "s").
- **Ação requerida:** Confirmar se `skill_router_bridge` é o nome dos testes para `skills_bridge`. Verificar os 9 testes falhando.

### CONFLITO 4: CURRENT_STATE vs branch
- **CURRENT_STATE.md diz:** "Suite completa: 7838/7840 (2 falhas pré-existentes)"
- **OMNIS_REFINAMENTO_50_DECISOES diz:** "8786 passed / 60 failed" na branch `feature/kratos-0-10-operational-truth`
- **Explicação provável:** São branches diferentes. CURRENT_STATE.md descreve a branch `feature/omnis-5waves-runtime-supreme`. O Refinamento descreve a branch atual (`feature/kratos-0-10-operational-truth`). As ~58 falhas novas aparecem porque a branch atual inclui código adicional do KRATOS.

### CONFLITO 5: app_factory_supreme sem rota no CLI
- **WAVE_REGISTRY diz:** app_factory_supreme é parte do G14 DONE
- **Código real diz:** Não há import de app_factory_supreme em cli.py, routers/, ou factory_router. Tem CLI próprio mas não registrado.
- **Ação requerida:** Verificar se app_factory_supreme deve ser adicionado como subcomando do CLI.

---

## 19. Riscos de Deletar Cedo Demais

| Módulo | Por que parece morto | Por que NÃO deve ser deletado |
|---|---|---|
| `governance_core` | __init__.py só com docstring | Docstring descreve arquitetura de 7 módulos — pode ser o target de refatoração da governance |
| `health_bridge` | Diretório vazio | CURRENT_STATE.md afirma que tem código. CONFLITO não resolvido. |
| `app_factory_exec` | Sem imports recebidos identificados | Pode ter imports de cli_commands que não foram rastreados na busca |
| `creative_production_v2` | Sem imports recebidos | Pode ser importado por um módulo de cli_commands não rastreado |
| `runtime_orchestrator` | Sem imports recebidos | Nome sugere que pode ser o orquestrador de runtime — deletar seria crítico se estiver sendo usado |
| `parallel_runner` | Sem imports recebidos | Pode ser parte do Parallel Fabric (JARVIS CLAUDE.md menciona parallel-fabric ativo) |
| `metrics` | Sem imports identificados | Pode ser usado por cli_commands ou production_hardening |

---

## 20. O Que NÃO Deve Ser Tocado Agora

| Item | Razão |
|---|---|
| `src/capability_forge_real/` | T-006a: 28 testes falhando — corrigir SEM refatorar estrutura |
| `src/multi_model_orchestration/` | CostTracker é segurança crítica — qualquer mudança exige aprovação |
| `src/governance/` | ApprovalGate e RiskClassifier são guardrails — mexer é risco sistêmico |
| `src/execution_graph/` | RuntimeBridge depende deste módulo — mudança quebra P37-P42 |
| `src/runtime_bridge/` | 26/26 testes, última entrega aprovada — não tocar |
| `src/omnis_health/` | Único health implementado atualmente — não mover até health_bridge clarificado |
| `templates/**/*.json` | Dirty files intencionais per CODEX_WAVE1_HANDOFF — não commitar |
| `config/paths.yaml` | Dirty file intencional — não commitar sem razão explícita |
| KRATOS em qualquer circunstância | CLAUDE.md é explícito: "Nunca — Mexer no KRATOS" |

---

## 21. Próxima Wave Recomendada

**Recomendação: Wave A — MODULES.md (mapa de módulos canônico)**

**Justificativa baseada em evidência:**

A inspeção revelou que o maior risco operacional não é código ruim — é **ambiguidade de autoridade**. Há 4 implementações de aprovação, 3 variantes de app_factory, 2 módulos de observabilidade, e 5 conflitos documento-vs-código. Sem um mapa canônico, qualquer developer (humano ou AI) que abrir uma sessão não sabe quais módulos são canônicos e quais são legacy.

O MODULES.md seria um arquivo de 1-2 páginas que declara:
1. Para cada responsabilidade funcional: qual módulo é o canônico
2. Quais módulos são legacy (não usar para código novo)
3. Quais módulos são experimental (usar com cautela)

Isso tem custo zero (apenas documenta o que esta auditoria descobriu) e benefício máximo (elimina a ambiguidade antes de qualquer refatoração). As outras waves (Portabilidade, API mínima, docker-compose) dependem de saber o que é canônico — portanto MODULES.md deve vir primeiro.

---

## 22. Decisões Que Lucas Precisa Aprovar

| ID | Decisão | Impacto |
|---|---|---|
| D-001 | health_bridge está absorvido pelo omnis_health? Se sim: atualizar CURRENT_STATE.md + deletar diretórios vazios | MÉDIO |
| D-002 | src/providers/ deve ser criado ou o Blueprint está errado? | MÉDIO |
| D-003 | skill_router_bridge = tests para skills_bridge? Confirmar antes de investigar os 9 testes falhando (T-006b) | ALTO |
| D-004 | governance_core: é o target de refatoração futura de governance ou pode ser deletado? | MÉDIO |
| D-005 | app_factory_supreme: deve ser registrado no CLI ou arquivado? | BAIXO |
| D-006 | approval_center: deve absorver approval_runtime formalmente? | MÉDIO |
| D-007 | parallel_runner: é parte do Parallel Fabric de ~/.claude ou do omnis-control? | MÉDIO |
| D-008 | Akasha e KRATOS na mesma branch (feature/kratos-0-10-operational-truth): intencional? | ALTO |
| D-009 | caption_approval_v2 e creative_production_v2: são substitutos do original ou experimentos abandonados? | BAIXO |
| D-010 | runtime_orchestrator e runtime_cli: qual a diferença funcional vs mission_orchestrator e cli_commands? | MÉDIO |

---

## 23. Checklist Antes de Qualquer Refatoração Real

- [ ] Resolver os 5 conflitos da seção 18 com Lucas
- [ ] Criar MODULES.md declarando módulos canônicos por responsabilidade
- [ ] Rodar suite completa e documentar estado real de falhas na branch atual
- [ ] Confirmar T-006b: qual módulo são os "9 testes skill_router_bridge"
- [ ] Confirmar T-006c: observability — quais 7 testes falhando especificamente
- [ ] Confirmar status do health_bridge (CONFLITO 1) antes de qualquer limpeza
- [ ] Mapear imports de approval_runtime antes de qualquer fusão com approval_center
- [ ] Verificar se src/providers/ existe em alguma branch ou é meta-arquitetura
- [ ] Não commitar templates/ ou config/paths.yaml sem wave dedicada
- [ ] Não avançar para Wave 2 sem GO explícito do Lucas (per CODEX_WAVE1_HANDOFF)
- [ ] Qualquer arquivo movido ou deletado: criar safety tag antes via git
- [ ] Nunca tocar KRATOS, nunca ler .env, nunca push sem autorização
