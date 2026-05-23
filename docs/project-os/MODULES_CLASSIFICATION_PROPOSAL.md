# MODULES_CLASSIFICATION_PROPOSAL

Gerado em: 2026-05-23  
Modo: auditoria estatica + proposta de classificacao.  
Escopo: `C:\Users\lucas\omnis-control` apenas.

Este documento atualiza a proposta anterior, que estava defasada: o estado atual possui 126 diretorios em `src/` e a Wave A ja removeu os fantasmas `health_bridge`. A suite validada nesta sessao esta verde: `8897 passed, 4 skipped`.

## 1. Autoridade Usada

Ordem de autoridade aplicada:

1. Codigo vivo, imports reais e testes passando.
2. `docs/project-os/CODEX_WAVE1_HANDOFF.md`.
3. `CLAUDE.md`.
4. Auditorias estrategicas antigas apenas como hipotese.

Regra de seguranca: nenhum modulo com teste existente, uso recente ou papel citado no handoff deve ser marcado como `MORTO`. Nesses casos, usar `SUPPORT`, `EXPERIMENTAL`, `LEGADO`, `DUPLICADO` ou `NEEDS_DECISION`.

## 2. Resumo Executivo

O OMNIS hoje e um runtime CLI local, file-backed, com execucao por comandos Typer, persistencia JSONL, dry-run por padrao em varias areas, e suite ampla. Ele nao e mais apenas um prototipo: ha muito codigo real e testado.

O risco principal nao e falta de codigo. O risco e ambiguidade de autoridade:

- varios modelos de missao;
- varios runtimes;
- varios sistemas de memoria;
- varios sistemas de output;
- varios sistemas de aprovacao;
- varios "cores" com nomes fortes.

Portanto, a proxima fase nao deve deletar nem mover. Deve congelar crescimento, declarar boundaries e escolher uma familia por vez para reconciliar.

## 3. Core Real Confirmado

Estes modulos sobrevivem como base operacional. Evidencia: import direto no `src/cli.py`, suite/testes, ou handoff operacional recente.

| Modulo | Classificacao | Evidencia | Decisao |
|---|---|---|---|
| `agentic` | CORE | Importado em `src/cli.py`; `tests/agentic`; 161 testes isolados passaram nesta sessao. | Manter. |
| `app_factory` | CORE | Importado em `src/cli.py` via `idea_app`; `tests/app_factory`. | Manter como App Factory canonico por enquanto. |
| `approval_center` | CORE | Usado por `execution_graph`, `mission_orchestrator`, `capability_gap`; `tests/approval_center`. | Manter como centro de aprovacao operacional. |
| `argos_bridge` | CORE | Importado em `src/cli.py`; usado por reports/workflow; testes adicionados nesta sessao. | Manter. |
| `caption_approval` | CORE | Importado em `src/cli.py`; usado por queue/assets/pipeline; testes passando. | Manter como captions canonico. |
| `checkers` | CORE | Importado em `src/cli.py`; usado por `omnis_health`; `tests/checkers`. | Manter. |
| `content_queue` | CORE | Importado em `src/cli.py`; 11 referencias internas; testes passando. | Manter. |
| `execution_graph` | CORE | Citado no handoff Wave 1; usado por CLI commands e runtime bridge; testes amplos. | Manter. |
| `governance` | CORE | Citado como enforcement/gate; `tests/governance`; usado por `omnis_supreme` e `real_world_actions`. | Manter, mas reconciliar com approval systems. |
| `intelligence` | CORE | Importado em `src/cli.py` para LLM router bridge; `tests/intelligence`. | Manter. |
| `memory` | CORE | Importado em `src/cli.py`; usado por reports; `tests/memory`. | Manter como fachada de memoria operacional. |
| `mission_orchestrator` | CORE | Usado por CLI commands e `execution_graph`; `tests/mission_orchestrator`. | Manter. |
| `multi_model_orchestration` | CORE | Citado no handoff; usado por `skills_bridge`; `tests/multi_model_orchestration`. | Manter como provider fabric canonico. |
| `omnis_health` | CORE | Importado em `src/cli.py`; `tests/omnis_health`; substitui antigo `health_bridge`. | Manter como health canonico. |
| `reports` | CORE | Importado em `src/cli.py`; gera status/briefing/cockpit data; `tests/reports`. | Manter. |
| `routers` | CORE | Importado em `src/cli.py` como factory/system router. | Manter, adicionar teste se virar alvo de mudanca. |
| `runners` | CORE | Importado em `src/cli.py`; `tests/runners`; skill runner real. | Manter. |
| `skills_bridge` | CORE | Citado no handoff; usado por `agentic` e `execution_graph`; `tests/skills_bridge`. | Manter como bridge canonica de skills. |
| `utils` | CORE | Importado em `src/cli.py`; usado por multiplos modulos; `tests/utils`. | Manter. |
| `video_assets` | CORE | Importado em `src/cli.py`; usado por queue/assets/offline factory; testes passando. | Manter. |
| `workflow` | CORE | Importado em `src/cli.py`; sem pasta propria em `tests/`, mas rota CLI ativa. | Manter; criar cobertura antes de refatorar. |

## 4. Support Operacional

Modulos que suportam o core, tem teste ou sao alcancados por `cli_commands`, mas nao devem mandar na arquitetura.

| Modulo | Classificacao | Evidencia | Decisao |
|---|---|---|---|
| `analytics` | SUPPORT | Usado por `campaign_manager`; `tests/analytics`. | Manter. |
| `asset_assignment` | SUPPORT | Usado por `cli_commands`; `tests/asset_assignment`. | Manter. |
| `asset_inbox` | SUPPORT | Usado por `cli_commands`; `tests/asset_inbox`. | Manter. |
| `campaign_auditor` | SUPPORT | Usado por `cli_commands`; `tests/campaign_auditor`. | Manter. |
| `campaign_manager` | SUPPORT | Usado por `omnis_supreme`; `tests/campaign_manager`. | Manter, nao tornar core ainda. |
| `campaign_package` | SUPPORT | Usado por `cli_commands`; `tests/campaign_package`. | Manter. |
| `capability_forge_real` | SUPPORT | Usado por `cli_commands`; `tests/capability_forge_real`. | Manter; nao duplicar Forge. |
| `capability_gap` | SUPPORT | Usado por Forge, CLI commands e mission orchestrator; `tests/capability_gap`. | Manter. |
| `cli_commands` | SUPPORT | 38 arquivos de comando Typer; rota indireta para muitos modulos. | Manter; e boundary de CLI modular. |
| `client_delivery` | SUPPORT | Usado por CLI commands; `tests/client_delivery`. | Manter. |
| `computer_ops` | SUPPORT | Usado por `cli_local.py`; `tests/computer_ops`. | Manter. |
| `control_tower` | SUPPORT | Usado por `omnis_control`; `tests/control_tower`. | Manter como apoio, nao autoridade sem decisao. |
| `decision_log` | SUPPORT | Usado por `omnis_control`; `tests/decision_log`. | Manter. |
| `delivery_portal` | SUPPORT | Usado por `omnis_supreme`; `tests/delivery_portal`. | Manter. |
| `delivery_templates` | SUPPORT | Usado por CLI commands; `tests/delivery_templates`. | Manter. |
| `first_missions` | SUPPORT | Usado por CLI commands; `tests/first_missions`. | Manter. |
| `first_post` | SUPPORT | Usado por CLI commands; `tests/first_post`. | Manter. |
| `integrations` | SUPPORT | Usado por `tool_registry`; `tests/integrations`. | Manter. |
| `knowledge_context` | SUPPORT | Usado por CLI commands; `tests/knowledge_context`. | Manter. |
| `manual_publishing` | SUPPORT | Usado por CLI commands; `tests/manual_publishing`. | Manter. |
| `marketing` | SUPPORT | Usado por campaign/supreme; `tests/marketing`. | Manter. |
| `metrics` | SUPPORT | Usado por CLI commands, missions, pipeline, tool registry; `tests/metrics`. | Manter. |
| `mission_builder` | SUPPORT | Usado por CLI commands, mission, mission_orchestrator; `tests/mission_builder`. | Manter. |
| `mission_report` | SUPPORT | Usado por CLI commands; `tests/mission_report`. | Manter. |
| `missions` | SUPPORT | Usado por CLI commands, memory, mission, pipeline; `tests/missions`. | Manter; reconciliar com `mission_orchestrator`. |
| `oauth_readiness` | SUPPORT | Usado por CLI commands/offline dashboard; `tests/oauth_readiness`. | Manter. |
| `offline_dashboard` | SUPPORT | Usado por CLI commands; `tests/offline_dashboard`. | Manter. |
| `offline_factory` | SUPPORT | Usado por CLI commands; `tests/offline_factory`. | Manter. |
| `output_factory` | SUPPORT | Usado por `cli_local.py`; `tests/output_factory`. | Manter. |
| `output_generator` | SUPPORT | Usado por CLI commands e mission; `tests/output_generator`. | Manter. |
| `pipeline_local` | SUPPORT | Usado por CLI commands; sem teste proprio detectado. | Manter com cautela; adicionar smoke antes de refatorar. |
| `publisher` | SUPPORT | Usado por CLI commands/pipeline; `tests/publisher`. | Manter. |
| `publisher_argos` | SUPPORT | Usado por campaign/delivery/supreme; `tests/publisher_argos`. | Manter. |
| `quality_layer` | SUPPORT | Usado por campaign auditor e CLI commands; `tests/quality_layer`. | Manter. |
| `remote_control` | SUPPORT | Usado por production hardening; `tests/remote_control`. | Manter, mas requer guardrails. |
| `render_engine` | SUPPORT | Usado por CLI commands; `tests/render_engine`. | Manter. |
| `role_registry` | SUPPORT | Usado por CLI commands e squad composer; `tests/role_registry`. | Manter. |
| `sales` | SUPPORT | Usado por commercial; `tests/sales`. | Manter. |
| `sales_crm` | SUPPORT | Usado por delivery portal; `tests/sales_crm`. | Manter. |
| `sector_registry` | SUPPORT | Usado por capability gap, CLI commands, mission orchestrator, squad composer; `tests/sector_registry`. | Manter. |
| `skill_matcher` | SUPPORT | Usado por Forge, gap, CLI commands, mission orchestrator, squad composer; `tests/skill_matcher`. | Manter. |
| `skills` | SUPPORT | Usado por publishing; `tests/skills`. | Manter. |
| `squad_composer` | SUPPORT | Usado por CLI commands, execution graph, squad execution; `tests/squad_composer`. | Manter. |
| `squad_execution` | SUPPORT | Usado por CLI commands; `tests/squad_execution`. | Manter. |
| `task_decomposer` | SUPPORT | Usado por CLI commands, execution graph, squad execution; `tests/task_decomposer`. | Manter. |
| `tool_registry` | SUPPORT | Usado por CLI commands/pipeline; `tests/tool_registry`. | Manter. |
| `video_production` | SUPPORT | Usado por CLI commands; `tests/video_production`. | Manter. |
| `work_order` | SUPPORT | Usado por CLI commands e output generator; `tests/work_order`. | Manter. |
| `work_orders` | SUPPORT | Usado por `omnis_control`; `tests/work_orders`. | Manter com decisao futura sobre singular/plural. |

## 5. Duplicados e Needs Decision

Estes modulos tem teste ou codigo, mas sobrepoem responsabilidades com outro modulo mais canonico.

| Modulo | Classificacao | Evidencia | Decisao Segura |
|---|---|---|---|
| `app_factory_exec` | DUPLICADO | Familia `app_factory`; sem referencia interna detectada; tem testes. | Congelar; decidir se vira adapter do `app_factory`. |
| `app_factory_supreme` | DUPLICADO | Familia `app_factory`; sem referencia interna detectada; testes existem. | Congelar; nao evoluir antes de reconciliar com `app_factory`. |
| `approval_runtime` | DUPLICADO | Sobrepoe `approval_center`/`governance`; sem referencia interna detectada; testes existem. | Congelar; decidir autoridade de aprovacao. |
| `caption_approval_v2` | DUPLICADO | Sobrepoe `caption_approval`; sem arquivos Python ativos detectados; testes existem. | Candidato a arquivo depois de confirmar vazio/sem uso. |
| `commercial` | DUPLICADO | Sobrepoe `sales`/`commercial_sdr`; sem referencia interna detectada, mas `sales` importa `commercial` inversamente em partes. | Reconciliar familia comercial. |
| `commercial_sdr` | DUPLICADO | Sobrepoe `commercial` e `sales_crm`; testes existem. | Congelar ate decisao comercial. |
| `content_factory` | DUPLICADO | Sobrepoe `content_queue`, `caption_approval`, `creative_production`; testes existem. | Congelar; decidir se e gerador ou pacote. |
| `content_scheduler` | DUPLICADO | Sobrepoe queue/scheduler; sem referencia interna detectada; testes existem. | Congelar. |
| `creative_production` | DUPLICADO | Usado por CLI commands/offline/pipeline; sem testes proprios detectados. | Manter temporario; reconciliar com `creative_production_v2`. |
| `creative_production_v2` | DUPLICADO | Sem arquivos Python ativos detectados; testes existem. | Candidato a arquivo se confirmado vazio. |
| `memory_intel` | DUPLICADO | Usado por `live_cockpit` e `memory`; testes existem. | Manter como suporte ate memoria canonica ser definida. |
| `memory_pack` | DUPLICADO | Usado por `memory`, `memory_intel`, `omnis_supreme`; testes existem. | Manter como pack/artefato, nao core. |
| `memory_unification` | DUPLICADO | Sem referencia interna detectada; testes existem. | Candidato a spec/arquivo, nao runtime. |
| `mission` | DUPLICADO | Sem referencia interna detectada; mas importa/usa missions; testes existem. | Reconciliar com `missions` e `mission_orchestrator`. |
| `mission_replay` | DUPLICADO | Sem referencia interna detectada; testes existem. | Manter como ferramenta; nao core. |
| `observability` | DUPLICADO | Usado por `pipeline_local`; testes existem. | Reconciliar com `omnis_health`/`reports`/`metrics`. |
| `observability_local` | DUPLICADO | Usado por `live_cockpit` e `omnis_supreme`; testes existem. | Congelar; decidir se absorve em observability. |
| `output_versioning` | DUPLICADO | Sem referencia interna detectada; testes existem. | Congelar; reconciliar com `output_generator`. |
| `runtime_bridge` | DUPLICADO | Sem referencia externa detectada, mas testes existem e foi refinado nesta sessao. | Manter ate runtime authority ser decidida. |
| `runtime_cli` | DUPLICADO | Sem referencia interna detectada; testes existem. | Candidato a adapter/arquivo, nao core. |
| `runtime_orchestrator` | DUPLICADO | Sem referencia interna detectada; testes existem. | Congelar ate reconciliar com `execution_graph`. |
| `skill_execution` | DUPLICADO | Sem referencia interna detectada; testes existem. | Reconciliar com `skills_bridge` e `runners`. |
| `template_registry` | DUPLICADO | Sem referencia interna detectada; testes existem. | Congelar; decidir relacao com `templates/`. |
| `templates` | DUPLICADO | Diretório em `src` sem Python ativo; testes existem. | Candidato a arquivo se vazio confirmado. |
| `weekly` | DUPLICADO | Sem referencia interna detectada; testes existem. | Congelar; decidir se e report ou output. |

## 6. Experimentais / Aspiracionais

Tem codigo/teste, mas nao devem virar autoridade sem decisao humana.

| Modulo | Classificacao | Evidencia | Decisao Segura |
|---|---|---|---|
| `akasha_event_sink` | EXPERIMENTAL | Sem referencia interna detectada; testes existem. | Preservar; reconciliar com `memory`/Akasha. |
| `akasha_runtime` | EXPERIMENTAL | Sem referencia interna detectada; testes existem. | Preservar; definir fronteira de memoria. |
| `automation` | EXPERIMENTAL | Sem referencia interna detectada; testes existem. | Congelar. |
| `autonomous_execution` | EXPERIMENTAL | Sem referencia interna detectada; importa `omnis_supreme`; testes existem. | Congelar; alto risco sem governance. |
| `autonomy` | EXPERIMENTAL | Sem referencia interna detectada; testes existem. | Congelar. |
| `computer_use` | EXPERIMENTAL | Sem referencia interna detectada; testes existem; usa mock/dry-run. | Congelar ate sandbox/guardrails. |
| `design_art` | EXPERIMENTAL | Sem referencia interna detectada; testes existem. | Congelar. |
| `finance` | EXPERIMENTAL | Sem referencia interna detectada; testes existem. | Congelar ate virar fluxo comercial real. |
| `kratos_bridge` | EXPERIMENTAL | Sem referencia interna detectada; testes existem. | Preservar como adapter futuro; nao ativar sem contrato. |
| `live_cockpit` | EXPERIMENTAL | Sem referencia interna detectada; testes existem; compete com KRATOS/cockpit. | Congelar; nao tornar UI canonica. |
| `local_search` | EXPERIMENTAL | Sem referencia interna detectada; testes existem. | Congelar. |
| `omnis_bus` | EXPERIMENTAL | Sem referencia interna detectada; testes existem. | Congelar ate event bus canonico. |
| `plugin_runtime` | EXPERIMENTAL | Sem referencia interna detectada; testes existem. | Congelar. |
| `preview` | EXPERIMENTAL | Sem referencia interna detectada; testes existem. | Manter como ferramenta, nao core. |
| `production_hardening` | EXPERIMENTAL | Sem referencia interna detectada; testes existem. | Congelar. |
| `publishing` | EXPERIMENTAL | Sem referencia interna detectada; testes existem. | Congelar; publicacao real exige approval. |
| `quality_gate` | EXPERIMENTAL | Sem referencia interna detectada; testes existem. | Congelar; reconciliar com `quality_layer`. |
| `real_world_actions` | EXPERIMENTAL | Sem referencia interna detectada; testes existem; acao externa sensivel. | Congelar; exige Human Slot para ativar. |
| `self_improvement` | EXPERIMENTAL | Sem referencia interna detectada; testes existem. | Congelar; alto risco sem rollback. |
| `video_studio` | EXPERIMENTAL | Sem referencia interna detectada; testes existem. | Congelar. |
| `war_room_bridge` | EXPERIMENTAL | Sem referencia interna detectada; testes existem. | Congelar. |

## 7. Legado / Orfaos / Candidatos a Arquivo Futuro

Estes nao devem ser apagados agora. Sao candidatos a arquivo/deprecacao depois de uma rodada dedicada com `rg`, testes focados e decisao humana.

| Modulo | Classificacao | Evidencia | Decisao Segura |
|---|---|---|---|
| `backlog` | LEGADO | Sem referencia interna detectada; testes existem. | Candidato a arquivo. |
| `executors` | LEGADO | Sem referencia interna detectada; 1 arquivo; testes existem. | Candidato a arquivo. |
| `governance_core` | ORFAO | Sem testes e sem referencias internas detectadas. | Forte candidato a arquivo/delecao futura. |
| `health` | ORFAO | Diretório sem Python ativo detectado; sem testes; sem referencias. | Forte candidato a arquivo/delecao futura. |
| `omnis_control` | ORFAO | Sem testes e sem referencias internas detectadas; nome conflita com repo. | Forte candidato a arquivo/delecao futura. |
| `omnis_os` | LEGADO | Usado por `app_factory` e `first_missions`; testes existem; possui wrapper legacy. | Preservar ate migracao explicita. |
| `omnis_supreme` | LEGADO | Usado por `autonomous_execution` e `live_cockpit`; testes existem; nome aspiracional. | Congelar como camada historica. |
| `parallel_runner` | LEGADO | Sem referencia interna detectada; testes existem. | Candidato a arquivo se substituido por execution graph. |

## 8. Familias de Drift

### 8.1 Mission

Modulos: `mission`, `missions`, `mission_builder`, `mission_orchestrator`, `mission_replay`, `mission_report`.

Decisao proposta:

- `mission_orchestrator`: autoridade de orquestracao.
- `mission_builder`: construtor de pacote/planos.
- `mission_report`: fechamento/relatorio.
- `missions`: estado/repositorio.
- `mission` e `mission_replay`: support/legado ate reconciliar.

### 8.2 Execution / Runtime

Modulos: `execution_graph`, `execution_queue`, `runtime_bridge`, `runtime_cli`, `runtime_orchestrator`, `runners`, `workflow`, `parallel_runner`.

Decisao proposta:

- `execution_graph`: autoridade de grafo.
- `runners`: execucao de skill simples.
- `workflow`: CLI/fluxo legado ativo, nao expandir.
- `runtime_bridge`, `execution_queue`: adapters/filas.
- `runtime_cli`, `runtime_orchestrator`, `parallel_runner`: congelar ate reconciliar.

### 8.3 Provider Fabric

Modulos: `multi_model_orchestration`, `intelligence`, `skills_bridge`.

Decisao proposta:

- `multi_model_orchestration`: autoridade de provider/model routing.
- `intelligence`: bridge local/LLM router existente.
- `skills_bridge`: consumo do provider fabric por skills.

### 8.4 Memory

Modulos: `memory`, `memory_intel`, `memory_pack`, `memory_unification`, `akasha_runtime`, `akasha_event_sink`.

Decisao proposta:

- `memory`: fachada operacional atual.
- `akasha_runtime` e `akasha_event_sink`: preservar como camada Akasha futura.
- `memory_intel`, `memory_pack`, `memory_unification`: support/experimento ate contrato unico.

### 8.5 Approval / Governance

Modulos: `approval_center`, `approval_runtime`, `governance`, `mission_orchestrator/approval_gate.py`, `execution_graph/approval_bridge.py`.

Decisao proposta:

- `approval_center`: store/API operacional de requests.
- `governance`: classificacao de risco e politica.
- bridges especificos so traduzem contexto; nao decidem politica sozinhos.
- `approval_runtime`: congelar ate reconciliar.

## 9. Funcoes Longas Que Bloqueiam Clareza

Primeiros alvos seguros para Tarefa 2, em ordem:

| Arquivo | Funcao | Linhas | Risco | Proposta |
|---|---:|---:|---|---|
| `src/reports/status_report.py:44` | `generate` | 278 | Medio | Extrair coletores pequenos sem mudar output. |
| `src/execution_graph/runner.py:23` | `run_graph_dry` | 189 | Alto | Separar validacao, eventos, execucao de step. |
| `src/execution_graph/runner.py:214` | `run_graph_real` | 172 | Alto | Refatorar depois do dry-run. |
| `src/cli.py:393` | `doctor` | 166 | Medio | Extrair builders de health por dominio. |
| `src/checkers/video_pipeline_check.py:191` | `check` | 165 | Baixo/medio | Separar scan, classify, summary. |
| `src/mission_orchestrator/planner.py:19` | `build_plan` | 107 | Medio | Separar intent/capability/steps. |
| `src/runners/skill_runner.py:39` | `run_skill` | 89 | Medio | Separar resolve path, validate, dry-run payload. |

Nao refatorar tudo em lote. Um arquivo por vez, teste focado, commit seletivo.

## 10. Proibicoes Para Proxima Wave

- Nao deletar modulos com testes.
- Nao mover familias inteiras.
- Nao criar novo `core`.
- Nao ativar `real_world_actions`, `self_improvement` ou `autonomous_execution`.
- Nao tocar KRATOS.
- Nao mexer em `.env`, secrets, deploy, Docker ou migrations.
- Nao commitar `templates/**/*.json` nem snapshots sem decisao dedicada.

## 11. Proxima Sequencia Recomendada

1. Aceitar este documento como proposta, nao como ordem de delecao.
2. Rodar suite completa antes de qualquer nova mudanca.
3. Escolher uma familia: recomenda-se `reports/status_report.py`.
4. Refatorar uma funcao longa sem mudar contrato.
5. Rodar teste focado e depois suite completa.
6. Commit seletivo apenas dos arquivos tocados nessa tarefa.

## 12. Resultado Final

O OMNIS atual e operacional, testado e grande demais para continuar crescendo sem mapa. O core real existe. O problema e excesso de camadas paralelas competindo por autoridade.

Decisao mais segura: manter core e support, congelar experimental/legado, e executar consolidacao por familia, nunca por big-bang.
