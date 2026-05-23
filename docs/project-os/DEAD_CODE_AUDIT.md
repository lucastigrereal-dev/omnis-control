# DEAD_CODE_AUDIT

Gerado: 2026-05-23  
Repo: `C:\Users\lucas\omnis-control`  
Branch: `feature/omnis-5waves-runtime-supreme`  
Modo: Grupo A / leitura e mapeamento / zero alteracao de codigo  

## Baseline

- Suite inicial desta rodada: `8512 passed, 4 skipped, 0 failed`.
- `src/` observado: 107 modulos/diretorios ativos.
- `src/_archive/` observado: 20 diretorios arquivados.
- `src/health_bridge/`: ausente no disco.
- `src/omnis_health/`: presente, com `server.py`, `models.py`, `__init__.py` e testes.

## Metodo

- Inventario de arquivos com `rg --files` e `Get-ChildItem`.
- Busca de imports com `rg "from src\\.|import src\\.|src\\."`.
- Busca LLM com `rg "openai|anthropic|litellm|localhost:4002|127\\.0\\.0\\.1:4002|:4002|chat\\.completions|completion\\(|acompletion|requests\\.(post|get|request)"`.
- Classificacao conservadora: nenhum modulo com teste real e import real foi marcado como morto.

---

# A1 - Mapa codigo vivo vs. suspeito vs. fantasma

## VIVO

Modulo com codigo Python ativo, teste e/ou referencia real fora do proprio modulo.

| modulo | caminho | motivo |
|---|---|---|
| `agentic` | `src/agentic` | 15 testes, 23 referencias externas, camada agentic recente das Fases 4-12. |
| `akasha_event_sink` | `src/akasha_event_sink` | 3 testes, 4 referencias externas; preservar ate reconciliacao de memoria. |
| `akasha_runtime` | `src/akasha_runtime` | 8 testes, 8 referencias externas; runtime Akasha testado. |
| `analytics` | `src/analytics` | 3 testes, 7 referencias externas. |
| `api` | `src/api` | 2 arquivos de teste diretos, 9 routers recentes; protegido, nao tocar. |
| `app_factory` | `src/app_factory` | 10 testes, 11 referencias externas. |
| `approval_center` | `src/approval_center` | 4 testes, 23 referencias externas; usado por execution/gates. |
| `argos_bridge` | `src/argos_bridge` | 4 testes, 8 referencias externas. |
| `asset_assignment` | `src/asset_assignment` | 2 testes, 3 referencias externas. |
| `asset_inbox` | `src/asset_inbox` | 9 testes, 11 referencias externas. |
| `automation` | `src/automation` | 9 testes, 9 referencias externas. |
| `autonomous_execution` | `src/autonomous_execution` | 6 testes, 7 referencias externas; vivo, mas alto risco operacional. |
| `campaign_auditor` | `src/campaign_auditor` | 1 teste, 3 referencias externas. |
| `campaign_manager` | `src/campaign_manager` | 3 testes, 5 referencias externas. |
| `campaign_package` | `src/campaign_package` | 4 testes, 7 referencias externas. |
| `capability_forge_real` | `src/capability_forge_real` | 9 testes, 21 referencias externas; forge real, nao duplicar. |
| `capability_gap` | `src/capability_gap` | 5 testes, 13 referencias externas; usado por mission_orchestrator. |
| `caption_approval` | `src/caption_approval` | 7 testes, 23 referencias externas; protegido. |
| `checkers` | `src/checkers` | 12 testes, 20 referencias externas. |
| `cli.py` | `src/cli.py` | 4 testes diretos, 44 referencias; entrada CLI historica. |
| `cli_agent.py` | `src/cli_agent.py` | CLI agentico recente; protegido pelo prompt. |
| `cli_commands` | `src/cli_commands` | 38 arquivos Python, 16 referencias externas. |
| `cli_local.py` | `src/cli_local.py` | 2 referencias externas; CLI local auxiliar. |
| `client_delivery` | `src/client_delivery` | 4 testes, 7 referencias externas. |
| `commercial` | `src/commercial` | 10 testes, 13 referencias externas. |
| `commercial_sdr` | `src/commercial_sdr` | 2 testes, 3 referencias externas. |
| `computer_ops` | `src/computer_ops` | 3 testes, 5 referencias externas. |
| `computer_use` | `src/computer_use` | 3 testes, 3 referencias externas. |
| `content_queue` | `src/content_queue` | 6 testes, 31 referencias externas; protegido. |
| `control_tower` | `src/control_tower` | 4 testes, 4 referencias externas. |
| `creative_production` | `src/creative_production` | 4 testes, 9 referencias externas. |
| `decision_log` | `src/decision_log` | 3 testes, 3 referencias externas. |
| `delivery_portal` | `src/delivery_portal` | 2 testes, 5 referencias externas. |
| `delivery_templates` | `src/delivery_templates` | 1 teste, 3 referencias externas. |
| `design_art` | `src/design_art` | 5 testes, 6 referencias externas. |
| `execution_contracts` | `src/execution_contracts` | 4 testes, 6 referencias externas; suporte da execution layer. |
| `execution_graph` | `src/execution_graph` | 14 testes, 26 referencias externas; autoridade de execution graph. |
| `execution_queue` | `src/execution_queue` | 4 testes, 7 referencias externas; queue de execucao ainda viva. |
| `finance` | `src/finance` | 2 testes, 3 referencias externas. |
| `first_missions` | `src/first_missions` | 9 testes, 10 referencias externas. |
| `first_post` | `src/first_post` | 3 testes, 3 referencias externas. |
| `governance` | `src/governance` | 4 testes, 12 referencias externas. |
| `integrations` | `src/integrations` | 2 testes, 3 referencias externas. |
| `intelligence` | `src/intelligence` | 2 testes, 3 referencias externas; bridge LLM legado/local. |
| `knowledge_context` | `src/knowledge_context` | 1 teste, 2 referencias externas. |
| `kratos_bridge` | `src/kratos_bridge` | 11 testes, 11 referencias externas; nao tocar KRATOS nesta rodada. |
| `live_cockpit` | `src/live_cockpit` | 5 testes, 6 referencias externas; vivo, mas boundary conflita com KRATOS. |
| `local_search` | `src/local_search` | 2 testes, 3 referencias externas. |
| `manual_publishing` | `src/manual_publishing` | 4 testes, 6 referencias externas. |
| `marketing` | `src/marketing` | 3 testes, 7 referencias externas. |
| `memory` | `src/memory` | 10 testes, 28 referencias externas; memoria canonica recente. |
| `memory_intel` | `src/memory_intel` | 5 testes, 8 referencias externas; vivo, mas deve ficar abaixo de `src/memory`. |
| `memory_pack` | `src/memory_pack` | 2 testes, 13 referencias externas; vivo, mas pack/suporte. |
| `metrics` | `src/metrics` | 5 testes, 10 referencias externas. |
| `mission` | `src/mission` | 3 testes, 54 referencias externas; vivo, mas nome/boundary compete com outras familias mission. |
| `mission_builder` | `src/mission_builder` | 6 testes, 14 referencias externas. |
| `mission_orchestrator` | `src/mission_orchestrator` | 8 testes, 16 referencias externas. |
| `mission_replay` | `src/mission_replay` | 2 testes, 3 referencias externas. |
| `mission_report` | `src/mission_report` | 3 testes, 6 referencias externas. |
| `missions` | `src/missions` | 12 testes, 25 referencias externas; runtime/repositorio de missoes vivo. |
| `multi_model_orchestration` | `src/multi_model_orchestration` | 7 testes, 11 referencias externas; provider fabric/router existente. |
| `oauth_readiness` | `src/oauth_readiness` | 9 testes, 9 referencias externas. |
| `observability` | `src/observability` | 8 testes, 15 referencias externas. |
| `observability_local` | `src/observability_local` | 2 testes, 6 referencias externas; possivel duplicidade, mas vivo. |
| `offline_dashboard` | `src/offline_dashboard` | 1 teste, 3 referencias externas. |
| `offline_factory` | `src/offline_factory` | 8 testes, 11 referencias externas. |
| `omnis_bus` | `src/omnis_bus` | 6 testes, 6 referencias externas. |
| `omnis_health` | `src/omnis_health` | 4 testes, 7 referencias externas; autoridade atual de health. |
| `omnis_os` | `src/omnis_os` | 10 testes, 14 referencias externas. |
| `omnis_supreme` | `src/omnis_supreme` | 5 testes, 10 referencias externas; vivo, mas aspiracional/legado em boundary. |
| `output_generator` | `src/output_generator` | 15 testes, 18 referencias externas. |
| `pipeline_local` | `src/pipeline_local` | 2 testes, 4 referencias externas. |
| `plugin_runtime` | `src/plugin_runtime` | 10 testes, 10 referencias externas. |
| `production_hardening` | `src/production_hardening` | 10 testes, 10 referencias externas. |
| `publisher` | `src/publisher` | 7 testes, 19 referencias externas. |
| `publisher_argos` | `src/publisher_argos` | 2 testes, 12 referencias externas. |
| `publishing` | `src/publishing` | 3 testes, 3 referencias externas. |
| `quality_layer` | `src/quality_layer` | 4 testes, 7 referencias externas. |
| `real_world_actions` | `src/real_world_actions` | 8 testes, 8 referencias externas; vivo, mas exige Human Slot para ativacao. |
| `remote_control` | `src/remote_control` | 14 testes, 22 referencias externas. |
| `render_engine` | `src/render_engine` | 4 testes, 6 referencias externas. |
| `reports` | `src/reports` | 5 testes, 9 referencias externas. |
| `role_registry` | `src/role_registry` | 4 testes, 5 referencias externas. |
| `runners` | `src/runners` | 2 testes, 3 referencias externas. |
| `sales` | `src/sales` | 10 testes, 28 referencias externas. |
| `sales_crm` | `src/sales_crm` | 2 testes, 7 referencias externas. |
| `sector_registry` | `src/sector_registry` | 4 testes, 7 referencias externas. |
| `self_improvement` | `src/self_improvement` | 8 testes, 8 referencias externas; vivo, mas nao ativar sem rollback/governanca. |
| `skill_matcher` | `src/skill_matcher` | 4 testes, 10 referencias externas. |
| `skills` | `src/skills` | 1 teste, 19 referencias externas. |
| `skills_bridge` | `src/skills_bridge` | 8 testes, 15 referencias externas; bridge canonica de skill execution. |
| `squad_composer` | `src/squad_composer` | 4 testes, 20 referencias externas. |
| `squad_execution` | `src/squad_execution` | 3 testes, 5 referencias externas. |
| `task_decomposer` | `src/task_decomposer` | 3 testes, 17 referencias externas. |
| `tool_registry` | `src/tool_registry` | 6 testes, 8 referencias externas. |
| `utils` | `src/utils` | 6 testes, 12 referencias externas. |
| `video_assets` | `src/video_assets` | 4 testes, 12 referencias externas. |
| `video_production` | `src/video_production` | 1 teste, 2 referencias externas. |
| `video_studio` | `src/video_studio` | 15 testes, 15 referencias externas. |
| `war_room_bridge` | `src/war_room_bridge` | 4 testes, 5 referencias externas. |
| `work_order` | `src/work_order` | 8 testes, 24 referencias externas. |
| `work_orders` | `src/work_orders` | 3 testes, 3 referencias externas. |

## SUSPEITO

Modulo com codigo/testes, mas sem caminho CLI/API principal claro ou com boundary sobreposto. Nao apagar sem nova revisao.

| modulo | caminho | motivo |
|---|---|---|
| `autonomy` | `src/autonomy` | Supervisao isolada; testes existem, mas sem caminho CLI/API principal observado. |
| `memory_unification` | `src/memory_unification` | Pouca referencia externa; `src/memory/interface.py` e a fachada canonica recente. |
| `output_factory` | `src/output_factory` | Baixa referencia; parece sobrepor `output_generator`. |
| `preview` | `src/preview` | Ferramenta isolada; testes existem, mas sem caminho principal observado. |
| `quality_gate` | `src/quality_gate` | Sobrepoe `quality_layer`/`governance`; baixa referencia. |
| `runtime_bridge` | `src/runtime_bridge` | Vivo e testado, mas baixa referencia externa; precisa reconciliar com `execution_graph` e API atual antes de evoluir. |

## FANTASMA

Modulo ausente, sem codigo Python ativo, ou claramente superseded por autoridade mais nova.

| modulo | caminho | motivo |
|---|---|---|
| `event_listener` | `src/event_listener` | Zero arquivos Python ativos detectados; apenas referencia residual/teste. |
| `health_bridge` | `src/health_bridge` | Diretorio ausente; substituido por `src/omnis_health`. |
| `routers` | `src/routers` | Sem testes proprios; boundary antigo em comparacao a `src/api` e `src/cli_agent.py`. |
| `workflow` | `src/workflow` | Sem testes proprios e baixa referencia; verificar antes de evoluir. |

---

# A2 - health_bridge vs omnis_health

| item | em health_bridge | em omnis_health | status | recomendacao |
|---|---|---|---|---|
| Diretorio fonte | Ausente no disco. | `src/omnis_health/` presente. | Superseded. | Manter `omnis_health`; nao recriar `health_bridge`. |
| Modelos | Ausente. | `src/omnis_health/models.py`. | Faltando em health_bridge. | `omnis_health` e autoridade. |
| Servidor/CLI health | Ausente. | `src/omnis_health/server.py`. | Faltando em health_bridge. | Manter server atual. |
| Testes | `tests/health_bridge/` ausente. | `tests/omnis_health/` com 4 arquivos de teste. | Superseded. | Nenhuma acao em health_bridge. |
| Boundary | Nome antigo indicava bridge. | Nome atual indica dominio health canonico. | Divergente resolvido. | Documentar como substituicao concluida. |

Recomendacao de uma linha: `health_bridge` deve permanecer ausente/arquivado; `omnis_health` deve continuar como modulo canonico de health.

---

# A3 - Chamadas LLM fora do router/adapters

Busca feita em `src/` por `openai`, `anthropic`, `litellm`, `:4002`, `chat.completions`, `completion(`, `acompletion`, `requests.post/get/request`.

| arquivo | funcao/area | linha | status | sugestao |
|---|---|---:|---|---|
| `src/agentic/llm_adapter.py` | `LiteLLMAdapter` / base URL `:4002` | 4, 87 | OK | Permitido pelo prompt; manter como adapter agentic. |
| `src/multi_model_orchestration/adapters/openai_adapter.py` | Adapter OpenAI | 1, 7, 32, 80 | OK | Adapter permitido; manter chamadas diretas confinadas aqui. |
| `src/multi_model_orchestration/adapters/anthropic_adapter.py` | Adapter Anthropic | 1, 7, 76 | OK | Adapter permitido; manter chamadas diretas confinadas aqui. |
| `src/multi_model_orchestration/registry.py` | Registro dos adapters OpenAI/Anthropic | 143-149 | OK | Registro, nao chamada direta. |
| `src/multi_model_orchestration/models.py` | Constantes de provider | 30-31 | OK | Constantes, nao chamada direta. |
| `src/cli.py` | Leitura de `litellm_params` em config | 773 | OK | Config/metadata, nao chamada direta. |
| `src/observability/telemetry/collector.py` | String provider `anthropic` | 32 | OK | Telemetria, nao chamada direta. |
| `src/observability/schemas/telemetry_schema.py` | Exemplo provider | 15 | OK | Schema/documentacao, nao chamada direta. |
| `src/tool_registry/healthcheck.py` | `openai_api` health item | 78 | OK | Registry/health metadata, nao chamada direta. |
| `src/tool_registry/discovery.py` | `openai_api` tool id | 297 | OK | Registry metadata, nao chamada direta. |

Violacoes confirmadas: nenhuma.

---

# Familias A-E - leitura rapida para execucao futura

## Grupo A - Execution layer

| familia | canonico observado | duplicado/superseded | refactor seguro local |
|---|---|---|---|
| `execution_graph` | Autoridade de graph/run/replay/rollback. | Sobrepoe parcialmente `runtime_bridge`, `execution_queue` e `execution_contracts`, mas todos ainda tem testes. | Nao mexer agora; ja houve refactor recente em `runner.py`. |
| `execution_queue` | Queue/runner/state testados. | Suporte mais baixo nivel que `execution_graph`. | Somente type hints/docstrings se necessario. |
| `execution_contracts` | Contratos/permissoes/outcomes testados. | Suporte de boundary, nao runtime authority. | Sem refactor agora. |
| `runtime_bridge` | Bridge testada. | Baixa referencia externa; possivel adapter legado entre graph e queue. | Classificar como suspeito; nao arquivar sem decisao. |
| `runners` | Skill runner real e pequeno. | Complementa `skills_bridge`, nao duplica integralmente. | Preservar. |

## Grupo B - Memory drift

| familia | canonico observado | duplicado/superseded | refactor seguro local |
|---|---|---|---|
| `memory` | Fachada canonica recente (`interface.py`, `caption_memory.py`). | Nenhum dentro da familia. | Preservar protegidos. |
| `memory_intel` | Inteligencia/similaridade usada por `memory/context_builder.py`. | Deve ficar subordinado a `memory`. | Nao fundir agora. |
| `memory_pack` | Pack/contexto usado por `memory_intel` e `context_builder`. | Suporte, nao fachada. | Nao fundir agora. |
| `memory_unification` | Router/contexto de pesquisa. | Baixa referencia; parece tentativa anterior de unificacao. | Suspeito para revisao futura. |

## Grupo C - Agentic/orchestration overflow

| familia | canonico observado | duplicado/superseded | refactor seguro local |
|---|---|---|---|
| `agentic` | Canonico recente para agent run/caption/batch/scheduler. | Protegido, nao mover. | Apenas docstrings/type hints nos alvos autorizados. |
| `mission_orchestrator` | Orquestrador classico usado por execution_graph. | Coexiste com `agentic/mission_engine.py`. | Preservar boundary: orchestration legacy/runtime vs agentic mission lifecycle. |
| `mission` | Adapter/builder/modelos com muitas referencias. | Nome colide com `missions` e `mission_orchestrator`. | Nao mexer sem decisao. |
| `missions` | Runtime/repositorio/state machine de missoes. | Sobrepoe parcialmente `agentic` e `mission_orchestrator`. | Nao mexer sem decisao. |
| `mission_builder` | Intent/planner/package usado por orchestrator. | Suporte do orquestrador. | Preservar. |
| `mission_report` | Fechamento/report service. | Relacionado, nao substituido. | Preservar. |
| `mission_replay` | Replay separado. | Pode sobrepor `execution_graph/replay.py`. | Candidato a reconciliacao futura. |

## Grupo D - Skills overflow

| familia | canonico observado | duplicado/superseded | refactor seguro local |
|---|---|---|---|
| `skills_bridge` | Bridge canonica entre agentic/execution e skill catalog/adapter. | Deve mandar em execucao de skills. | Preservar. |
| `skills` | Implementacoes de skills concretas. | Nao e bridge. | Preservar como payload/skill concrete. |
| `skill_matcher` | Matching/loader usado por mission_orchestrator e capability gap. | Sobrepoe selecao do bridge parcialmente. | Reconciliar depois; nao remover. |
| `tool_registry` | Registro/descoberta/health de ferramentas. | Nao duplica skills_bridge; cataloga ferramentas. | Preservar. |

## Grupo E - Autonomy/intelligence

| familia | canonico observado | duplicado/superseded | refactor seguro local |
|---|---|---|---|
| `intelligence` | Bridge LLM antigo/local. | Coexiste com `agentic/llm_adapter.py` e `multi_model_orchestration`. | Nao ativar como novo provider; documentar como legado/suporte. |
| `autonomous_execution` | Executor/checkpoint/recovery testados. | Alto risco; nao e caminho agentic recente. | Preservar congelado. |
| `autonomy` | Supervisor pequeno e isolado. | Suspeito; pode ser anterior a governance recente. | Nao mexer. |
| `self_improvement` | Pipeline completo testado. | Alto risco sem Human Slot/rollback. | Preservar congelado. |
| `capability_forge_real` | Forge real testado. | Relacionado a `agentic/forge_orchestrator.py`, mas mais completo. | Preservar; nao ativar automatico. |
| `capability_gap` | Detector/store/workflow usado por planner/orchestrator. | Suporte do forge/orchestrator. | Preservar. |

---

# Candidatos a archive/fusao

## Archive futuro somente com GO explicito

| candidato | evidencia | risco |
|---|---|---|
| `src/health_bridge` | Ausente no disco; superseded por `omnis_health`. | Baixo; ja removido. |
| `src/event_listener` | Zero arquivos Python ativos. | Baixo, validar teste residual antes. |
| `src/routers` | Sem testes proprios; `src/api` e `src/cli_agent.py` sao caminhos recentes. | Medio; validar referencias antes. |
| `src/workflow` | Sem testes proprios e baixa referencia. | Medio; pode haver CLI/workflow legado. |

## Fusao/reconciliacao futura

| familia | decisao sugerida |
|---|---|
| Memory | `src/memory` deve continuar fachada; `memory_intel`, `memory_pack`, `memory_unification` devem virar subcamadas ou ser documentados como suporte. |
| Mission | Separar claramente `agentic/mission_engine.py`, `mission_orchestrator`, `missions`, `mission`, `mission_builder`, `mission_report`, `mission_replay`. Nao fundir em lote. |
| Skills | `skills_bridge` como boundary de execucao; `skills` como implementacao; `skill_matcher` como matcher legado/suporte; `tool_registry` como catalogo. |
| Autonomy | `autonomous_execution`, `autonomy`, `self_improvement` vivos, mas congelados ate Human Slot. |

