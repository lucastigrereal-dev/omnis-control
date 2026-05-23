# MODULES.md — Classificação Canônica dos Módulos src/
**Gerado:** 2026-05-22  
**Branch:** feature/omnis-5waves-runtime-supreme  
**Suite de referência:** 8903 passed, 4 skipped, 0 failed  
**Base:** MODULES_CLASSIFICATION_PROPOSAL.md (confirmado no disco)

---

## Chave de Classificação

| Classe | Critério |
|---|---|
| **CORE** | Importado diretamente em `src/cli.py` ou cadeia principal; tem testes; é autoridade de seu domínio |
| **SUPPORT** | Suporta o CORE, tem testes ou é acionado via `cli_commands`; não deve mandar na arquitetura |
| **EXPERIMENTAL** | Código real + testes, mas sem import no caminho principal; não ativar sem GO explícito |
| **DUPLICADO** | Sobrepõe responsabilidades de um módulo mais canônico; congelar evolução até decisão |
| **LEGADO** | Código funcional + testes, mas fora do caminho ativo; candidato a arquivo futuro com GO |
| **FANTASMA** | Sem código Python ativo, sem testes reais, sem import detectado; arquivar com GO |
| **MORTO** | Confirmado obsoleto por decisão explícita anterior; aguardando cleanup |

---

## CORE (21 módulos)

| Módulo | Evidência |
|---|---|
| `agentic` | cli.py import; 161 testes passando |
| `app_factory` | cli.py via idea_app; tests/app_factory |
| `approval_center` | usado por execution_graph, mission_orchestrator; tests |
| `argos_bridge` | cli.py import; usado por reports/workflow; tests |
| `caption_approval` | cli.py import; usado por queue/assets/pipeline; tests |
| `checkers` | cli.py import; usado por omnis_health; tests |
| `content_queue` | cli.py import; 11 referências internas; tests |
| `execution_graph` | cli.py commands; runtime bridge; testes amplos |
| `governance` | enforcement/gate; tests; usado por omnis_supreme |
| `intelligence` | cli.py LLM router bridge; tests |
| `memory` | cli.py import; usado por reports; tests |
| `mission_orchestrator` | CLI commands e execution_graph; tests |
| `multi_model_orchestration` | provider fabric canônico; usado por skills_bridge; tests |
| `omnis_health` | cli.py import; substitui health_bridge; 49 tests |
| `reports` | cli.py import; gera status/briefing/cockpit data; tests |
| `routers` | cli.py factory/system router |
| `runners` | cli.py import; skill runner real; tests |
| `skills_bridge` | usado por agentic e execution_graph; tests |
| `utils` | cli.py import; usado por múltiplos módulos; tests |
| `video_assets` | cli.py import; usado por queue/assets/offline factory; tests |
| `workflow` | cli.py import; rota CLI ativa; sem tests próprios — criar antes de refatorar |

---

## SUPPORT (46 módulos)

| Módulo | Evidência |
|---|---|
| `analytics` | usado por campaign_manager; tests |
| `asset_assignment` | cli_commands; tests |
| `asset_inbox` | cli_commands; tests |
| `campaign_auditor` | cli_commands; tests |
| `campaign_manager` | omnis_supreme; tests |
| `campaign_package` | cli_commands; tests |
| `capability_forge_real` | cli_commands; tests — não duplicar Forge |
| `capability_gap` | Forge + CLI + mission_orchestrator; tests |
| `cli_commands` | 38 arquivos de comando Typer; boundary de CLI modular |
| `client_delivery` | cli_commands; tests |
| `computer_ops` | cli_local.py; tests |
| `control_tower` | omnis_control; tests — apoio, não autoridade |
| `decision_log` | omnis_control; tests |
| `delivery_portal` | omnis_supreme; tests |
| `delivery_templates` | cli_commands; tests |
| `first_missions` | cli_commands; tests |
| `first_post` | cli_commands; tests |
| `integrations` | tool_registry; tests |
| `knowledge_context` | cli_commands; tests |
| `manual_publishing` | cli_commands; tests |
| `marketing` | campaign/supreme; tests |
| `metrics` | CLI + missions + pipeline + tool_registry; tests |
| `mission_builder` | CLI + mission + mission_orchestrator; tests |
| `mission_report` | cli_commands; tests |
| `missions` | CLI + memory + mission + pipeline; tests — reconciliar com mission_orchestrator |
| `oauth_readiness` | CLI + offline dashboard; tests |
| `offline_dashboard` | cli_commands; tests |
| `offline_factory` | cli_commands; tests |
| `output_factory` | cli_local.py; tests |
| `output_generator` | CLI + mission; tests |
| `pipeline_local` | cli_commands; sem test próprio — adicionar smoke antes de refatorar |
| `publisher` | CLI + pipeline; tests |
| `publisher_argos` | campaign + delivery + supreme; tests |
| `quality_layer` | campaign_auditor + CLI; tests |
| `remote_control` | production_hardening; tests — requer guardrails |
| `render_engine` | cli_commands; tests |
| `role_registry` | CLI + squad_composer; tests |
| `sales` | commercial; tests |
| `sales_crm` | delivery_portal; tests |
| `sector_registry` | capability_gap + CLI + mission_orchestrator + squad_composer; tests |
| `skill_matcher` | Forge + gap + CLI + mission_orchestrator + squad_composer; tests |
| `skills` | publishing; tests |
| `squad_composer` | CLI + execution_graph + squad_execution; tests |
| `squad_execution` | cli_commands; tests |
| `task_decomposer` | CLI + execution_graph + squad_execution; tests |
| `tool_registry` | CLI + pipeline; tests |
| `video_production` | cli_commands; tests |
| `work_order` | CLI + output_generator; tests |
| `work_orders` | omnis_control; tests — decidir singular/plural |

---

## EXPERIMENTAL (20 módulos)
> Congelar. Não ativar sem GO explícito do Lucas.

| Módulo | Risco | Evidência |
|---|---|---|
| `akasha_event_sink` | Baixo | Sem import interno; tests existem |
| `akasha_runtime` | Baixo | Sem import interno; tests existem |
| `automation` | Médio | Sem import interno; tests existem |
| `autonomous_execution` | Alto | Importa omnis_supreme; sem gate; tests existem |
| `autonomy` | Alto | Sem import interno; tests existem |
| `computer_use` | Médio | Mock/dry-run; sem import interno; tests existem |
| `design_art` | Baixo | Sem import interno; tests existem |
| `finance` | Médio | Sem import interno; tests existem |
| `kratos_bridge` | Baixo | Adapter futuro; não ativar sem contrato KRATOS |
| `live_cockpit` | Alto | Compete com KRATOS; sem import interno; tests existem |
| `local_search` | Baixo | Sem import interno; tests existem |
| `omnis_bus` | Médio | Sem event bus canônico; tests existem |
| `plugin_runtime` | Médio | Sem import interno; tests existem |
| `preview` | Baixo | Ferramenta; não core; tests existem |
| `production_hardening` | Médio | Sem import interno; tests existem |
| `publishing` | Alto | Publicação real exige Human Slot; tests existem |
| `quality_gate` | Baixo | Reconciliar com quality_layer; tests existem |
| `real_world_actions` | **CRÍTICO** | Ação externa sensível; exige Human Slot para ativar |
| `self_improvement` | **CRÍTICO** | Alto risco sem rollback; congelar |
| `video_studio` | Baixo | Sem import interno; tests existem |
| `war_room_bridge` | Baixo | Sem import interno; tests existem |

---

## DUPLICADO (25 módulos)
> Congelar evolução. Reconciliar por família, nunca em lote.

| Módulo | Sobrepõe | Decisão Pendente |
|---|---|---|
| `app_factory_exec` | app_factory | Virar adapter ou mesclar |
| `app_factory_supreme` | app_factory | Não evoluir antes de reconciliar |
| `approval_runtime` | approval_center + governance | Decidir autoridade de aprovação |
| `caption_approval_v2` | caption_approval | Confirmar se vazio → arquivar |
| `commercial` | sales + commercial_sdr | Reconciliar família comercial |
| `commercial_sdr` | commercial + sales_crm | Congelar até decisão comercial |
| `content_factory` | content_queue + caption_approval + creative_production | Decidir papel |
| `content_scheduler` | queue + scheduler | Congelar |
| `creative_production` | creative_production_v2 | Manter temporário; reconciliar |
| `creative_production_v2` | creative_production | Confirmar se vazio → arquivar |
| `memory_intel` | memory | Manter como suporte até memória canônica |
| `memory_pack` | memory + memory_intel | Pack/artefato, não core |
| `memory_unification` | memory | Candidato a spec/arquivo |
| `mission` | missions + mission_orchestrator | Reconciliar família mission |
| `mission_replay` | missions | Manter como ferramenta; não core |
| `observability` | omnis_health + reports + metrics | Reconciliar |
| `observability_local` | observability | Congelar; decidir absorção |
| `output_versioning` | output_generator | Congelar; reconciliar |
| `runtime_bridge` | execution_graph | Manter até runtime authority definida |
| `runtime_cli` | cli.py + runners | Candidato a adapter/arquivo |
| `runtime_orchestrator` | execution_graph | Congelar até reconciliar |
| `skill_execution` | skills_bridge + runners | Reconciliar |
| `template_registry` | templates | Congelar; decidir relação |
| `templates` | caption_approval/templates | Confirmar se vazio → arquivar |
| `weekly` | reports + output | Decidir se é report ou output |

---

## LEGADO (7 módulos)
> Código funcional ou com testes, mas fora do caminho ativo.
> Candidatos a `src/_archive/` com GO explícito do Lucas.

| Módulo | Evidência | Risco de Arquivar |
|---|---|---|
| `backlog` | Sem import interno; tests existem | Baixo |
| `executors` | 1 arquivo; sem import interno; tests existem | Baixo |
| `omnis_os` | Usado por app_factory e first_missions; tests | Médio — verificar antes |
| `omnis_supreme` | Usado por autonomous_execution e live_cockpit; tests | Médio — experimental depende |
| `parallel_runner` | Sem import interno; tests existem | Baixo — substituído por execution_graph |
| `governance_core` | Tem decision_log.py e human_slot.py; sem tests; zero imports externos | Baixo — porém contém Decision Log e HumanSlot que podem ser úteis futuramente |

---

## FANTASMA (3 módulos)
> Sem código Python ativo, sem testes, sem import real.
> Prontos para `src/_archive/` — GO explícito necessário.

| Módulo | Disco | Motivo |
|---|---|---|
| `health` | Tem pipeline.py, sem tests, zero imports externos | Nunca integrado; health real está em omnis_health |
| `omnis_control` | Tem cli.py/models.py/queue.py; sem tests; omnis_control/__init__.py tem import quebrado | Órfão confirmado; nome conflita com repo |

---

## MORTO (0 módulos)
> Nenhum módulo declarado MORTO por decisão explícita até esta data.
> `health_bridge` e `tests/health_bridge` foram removidos na Wave A (2026-05-22).

---

## Famílias de Drift (Decisão Pendente do Lucas)

| Família | Módulos | Autoridade Canônica |
|---|---|---|
| Mission | mission, missions, mission_builder, mission_orchestrator, mission_replay, mission_report | `mission_orchestrator` |
| Execution | execution_graph, runners, workflow, runtime_bridge, runtime_cli, runtime_orchestrator, parallel_runner | `execution_graph` |
| Provider | multi_model_orchestration, intelligence, skills_bridge | `multi_model_orchestration` |
| Memory | memory, memory_intel, memory_pack, memory_unification, akasha_runtime, akasha_event_sink | `memory` (fachada) |
| Approval | approval_center, approval_runtime, governance | `approval_center` + `governance` |

---

## Funções Longas (Alvos para Refatoração Cirúrgica)

| Arquivo | Função | Linhas | Prioridade |
|---|---|---|---|
| `src/execution_graph/runner.py:23` | `run_graph_dry` | 189 | Alta |
| `src/execution_graph/runner.py:214` | `run_graph_real` | 172 | Alta |
| `src/cli.py:393` | `doctor` | 166 | Média |
| `src/mission_orchestrator/planner.py:19` | `build_plan` | 107 | Média |

*Já refatorados pelo Codex (Wave Codex, 2026-05-22):* `status_report.generate`, `skill_runner.run_skill`, `video_pipeline_check.check`, `context_builder._build_markdown`.

---

## Regras para Próxima Wave

1. Não deletar módulos com testes sem GO explícito
2. Não mover famílias inteiras em lote
3. Não criar novo "core"
4. Não ativar `real_world_actions`, `self_improvement` ou `autonomous_execution`
5. Não tocar KRATOS
6. Arquivar = `git mv src/X src/_archive/X` + entrada em `src/_archive/README.md`
