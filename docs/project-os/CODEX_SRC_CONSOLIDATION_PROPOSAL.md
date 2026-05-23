# CODEX_SRC_CONSOLIDATION_PROPOSAL

Gerado: 2026-05-23  
Repo: `C:\Users\lucas\omnis-control`  
Branch observada: `feature/omnis-5waves-runtime-supreme`  
Modo: READ-FIRST / small changes only / no commit / no push  

## Autoridade usada

1. Código vivo + testes passando.
2. `docs/project-os/CURRENT_STATE.md` atualizado em 2026-05-23.
3. `docs/project-os/MODULES.md`.
4. `docs/project-os/CODEX_WAVE1_HANDOFF.md`.
5. Busca real com `rg` em `src`, `tests` e `docs/project-os`.

## Baseline desta sessão

- `src/api/`: existe, mas nao foi tocado.
- Suite completa inicial: `8383 passed, 4 skipped, 0 failed`.
- Suite focada das familias auditadas: `281 passed, 0 failed`.
- Familias auditadas: `src/reports/`, `src/memory/`, `src/agentic/`.

## Regra de classificacao aplicada

| Classe | Criterio aplicado nesta proposta |
|---|---|
| CORE | Usado por `src/cli.py`, por `src/api/`, por `execution_graph`, ou declarado como entrega recente em `CURRENT_STATE.md`, com testes verdes. |
| SUPPORT | Tem testes e suporta um fluxo core, mas nao deve mandar na arquitetura. |
| EXPERIMENTAL | Tem codigo/testes, mas nao aparece no caminho operacional principal observado. Preservar ate decisao explicita. |
| LEGADO | Funcional, mas fora do caminho atual e substituido por outro modulo. |
| FANTASMA | Sem codigo/teste/import real. |
| DUPLICADO | Sobrepoe responsabilidade com outro modulo dentro da mesma familia. |
| MORTO | Obsoleto por decisao explicita anterior. |
| UNKNOWN | Evidencia insuficiente. |

Nenhum modulo destas tres familias deve ser marcado como MORTO nesta rodada: todos os arquivos analisados tem teste, import real, entrega recente, ou funcao de suporte clara.

---

# 1. Familia `src/reports/`

## Resumo

`reports` e familia CORE do OMNIS. Evidencia: `src/cli.py` importa `status_report` e `briefing`; `src/api/routers/reports.py` tambem consome `status_report` e `briefing`; `src/cli.py` usa `ReportGenerator` no fluxo de missoes; `tests/reports/` cobre os geradores principais; `tests/agentic/test_report_generator.py` cobre o report do fluxo agentic.

## Classificacao por arquivo

| Arquivo | Classe | Evidencia | Decisao recomendada |
|---|---|---|---|
| `src/reports/status_report.py` | CORE | `src/cli.py:37`, `src/cli.py:583`; `src/api/routers/reports.py`; `tests/reports/test_status_report.py`; `MODULES.md` marca `reports` como CORE. | Manter como gerador canonico de status operacional. Nao consolidar outros reports dentro dele agora. |
| `src/reports/briefing.py` | CORE | `src/cli.py:43`, comando `briefing`; `src/api/routers/reports.py`; `tests/test_briefing.py`. | Manter como briefing operacional separado de status. |
| `src/reports/report_generator.py` | CORE | `src/cli.py:2102`; `tests/agentic/test_report_generator.py`; importa contratos de `src.agentic`. | Manter como gerador canonico de relatorio de missao agentic. |
| `src/reports/cockpit_generator.py` | SUPPORT | `tests/reports/test_cockpit_generator.py`; referencia em `src/cli_local.py`; gera HTML local. | Preservar; nao fundir com status_report. |
| `src/reports/output_viewer_data.py` | SUPPORT | `tests/reports/test_output_viewer_data.py`; gera dados para viewer de outputs. | Preservar; escopo diferente de status/briefing. |
| `src/reports/cockpit_data_all.py` | SUPPORT | Script de geracao `python -m src.reports.cockpit_data_all`; sem import externo detectado, mas gera datasets de cockpit. | Preservar como utilitario. Adicionar teste futuro antes de qualquer refactor. |
| `src/reports/__init__.py` | SUPPORT | Import publico via `from src.reports import status_report`; arquivo vazio funciona como package boundary. | Nao adicionar `__all__` agora; sem ganho e sem teste especifico de API publica. |

## Drift e duplicidade

- Nao ha duplicidade obvia entre `status_report`, `briefing` e `report_generator`: cada um atende uma saida diferente.
- Ha sobreposicao leve entre `cockpit_generator`, `output_viewer_data` e `cockpit_data_all` no tema "cockpit/output", mas a evidencia aponta para artefatos diferentes: HTML, viewer data e datasets agregados.
- `cockpit_data_all.py` e o unico ponto com menor cobertura direta na familia; nao classificar como orfao porque e script executavel e esta dentro da familia declarada CORE.

## Type hints / modelos / funcoes longas

| Arquivo | Achado | Evidencia | Acao segura |
|---|---|---|---|
| `src/reports/cockpit_data_all.py` | `main()` sem retorno anotado. | AST: `main` sem return annotation. | Adicionar `-> None` em slice futuro, com teste/smoke. |
| `src/reports/cockpit_data_all.py` | `collect_missions()` tem 67 linhas. | AST: funcao publica >60 linhas. | Extrair helpers privados se for mexer em reports. |
| `src/reports/report_generator.py` | `MissionReport.to_markdown()` tem 73 linhas. | AST: metodo publico >60 linhas. | Refactor minimo possivel, preservando texto exato. Alto risco de snapshot textual. |
| `src/reports/output_viewer_data.py` | `generate()` tem 50 linhas. | Abaixo do limite de 60, mas denso. | Sem acao agora. |

---

# 2. Familia `src/memory/`

## Resumo

`memory` e CORE/SUPPORT misto. `CURRENT_STATE.md` declara `src/memory/interface.py` como entrega da Fase 4; `src/agentic/caption_draft_agent.py` usa `MemoryInterface`; `src/cli.py` usa `akasha_reader`; `briefing.py` consulta Akasha; `tests/memory/` cobre interface, context builder, embeddings, learning writer/reuse/writeback.

## Classificacao por arquivo

| Arquivo | Classe | Evidencia | Decisao recomendada |
|---|---|---|---|
| `src/memory/interface.py` | CORE | `CURRENT_STATE.md` Fase 4; `src/agentic/caption_draft_agent.py`; `tests/memory/test_memory_interface.py`; `tests/agentic/test_caption_draft_agent.py`. | Manter como fachada canonica de memoria para agentes. |
| `src/memory/akasha_reader.py` | CORE | `src/cli.py:716`, `src/cli.py:737`; `src/reports/briefing.py`; usado para ping/contexto Akasha. | Manter como reader operacional Akasha. |
| `src/memory/context_builder.py` | SUPPORT | `tests/memory/test_context_builder.py`; `tests/memory/test_e2e_dryrun.py`; usado por `MemoryInterface._real_query`. | Preservar; suporte para query real. |
| `src/memory/learning_reuse.py` | SUPPORT | `tests/memory/test_learning_reuse.py`; importado por `MemoryInterface._real_query`. | Preservar como componente de reuso. |
| `src/memory/learning_writer.py` | SUPPORT | `tests/memory/test_learning_writer.py`; chama `LearningWritebackService`. | Preservar como produtor de aprendizados. |
| `src/memory/writeback.py` | SUPPORT | `tests/memory/test_writeback.py`; `tests/memory/test_e2e_dryrun.py`; importado por `learning_writer`. | Preservar como ponte de writeback controlado. |
| `src/memory/embeddings.py` | SUPPORT | `tests/memory/test_embedding_strategy.py`; providers mock/deterministicos. | Preservar; util para testes e estrategia local. |
| `src/memory/learning_sources.py` | SUPPORT | `tests/memory/test_learning_reuse.py`; citacao/validacao de fonte. | Preservar; pequeno e coeso. |
| `src/memory/qdrant_indexer.py` | SUPPORT | `tests/test_qdrant_indexer.py`; `tool_registry/discovery.py`; integra Qdrant sem exigir servico real nos testes. | Preservar; nao promover a core authority ate reconciliar Qdrant vs Akasha. |

## Drift e duplicidade

- Dentro de `src/memory/`, `learning_reuse.py`, `learning_writer.py` e `writeback.py` nao parecem duplicados: reuse le, writer gera aprendizado, writeback persiste/ponteia.
- O drift real esta fora desta familia: `memory_intel`, `memory_pack` e `memory_unification` ainda coexistem como sistemas adjacentes. Esta proposta nao move nada, mas recomenda tratar isso numa reconciliacao propria de memoria.
- `MemoryInterface` deve continuar sendo a fachada; novos consumidores nao devem importar `context_builder`, `learning_reuse` ou backends diretamente sem motivo.

## Type hints / modelos / funcoes longas

| Arquivo | Achado | Evidencia | Acao segura |
|---|---|---|---|
| `src/memory/akasha_reader.py` | `_connect()` sem retorno anotado. | AST: funcao privada sem annotation. | Pode tipar futuramente, mas cuidado para nao expor driver/conn real. |
| `src/memory/embeddings.py` | `EmbeddingStrategy.mock_default(cls)` sem annotation em `cls`. | AST: classemethod acusa `cls` sem annotation. | Baixo valor; nao mexer agora. |
| `src/memory/writeback.py` | `writeback_from_journal()` tem 88 linhas. | AST: metodo publico >60 linhas. | Melhor alvo de slice futuro em memoria. Extrair leitura, criacao de record e persistencia. |
| `src/memory/context_builder.py` | `build()` tem 57 linhas. | Quase limite, mas abaixo de 60. | Sem acao agora. |
| Dataclasses | `ContextResult`, `MemoryContext`, `LearningEntry`, `LearningReport`, `WritebackResult` tem `to_dict`. | AST + testes. | `from_dict` nao e obrigatorio onde testes nao exigem round-trip. |

---

# 3. Familia `src/agentic/`

## Resumo

`agentic` e CORE recente e sensivel. `CURRENT_STATE.md` declara `agent_models.py` e `caption_draft_agent.py` como Fase 4; `src/cli.py` importa `MissionIntake`, `MissionEngine`, `DeliverableMapper` e `ReportGenerator`; `execution_graph` usa `SkillRunnerBridge`, `TaskDispatcher`, `DeliverableMapper`, `MissionIntake`, `SquadSelector` e `MissionEngine`; `tests/agentic/` cobre 10 arquivos.

## Classificacao por arquivo

| Arquivo | Classe | Evidencia | Decisao recomendada |
|---|---|---|---|
| `src/agentic/agent_models.py` | CORE | `CURRENT_STATE.md` Fase 4; `tests/agentic/test_agent_models.py`; usado por `CaptionDraftAgent`. | Manter como modelo canonico de AgentRun/AgentStep. |
| `src/agentic/caption_draft_agent.py` | CORE | `CURRENT_STATE.md` Fase 4; `tests/agentic/test_caption_draft_agent.py`; usa `MemoryInterface` e `AgentRunRepository`. | Manter; proxima evolucao deve seguir `FASE5_SPEC.md`, nao criar agente paralelo. |
| `src/agentic/mission_intake.py` | CORE | `src/cli.py:2099`; `tests/agentic/test_mission_intake.py`; usado por mapper/dispatcher/report tests. | Manter como entrada canonica de texto livre para missao. |
| `src/agentic/mission_engine.py` | CORE | `src/cli.py:2100`, `2198`, `2237`, `2268`; `tests/agentic/test_mission_engine.py`; usado por reports. | Manter como lifecycle canonico de missao agentic. |
| `src/agentic/deliverable_mapper.py` | CORE | `src/cli.py:2101`; `tests/agentic/test_deliverable_mapper.py`; `task_dispatcher` importa. | Manter como tradutor canonico intake -> deliverables. |
| `src/agentic/task_dispatcher.py` | CORE | `tests/agentic/test_task_dispatcher.py`; `skill_runner_bridge` importa; `execution_graph` e2e usa. | Manter como roteador deliverable -> executor. |
| `src/agentic/skill_runner_bridge.py` | CORE | `src/execution_graph/mission_bridge.py`; `tests/execution_graph/test_e2e_vertical_slice.py`; `tests/agentic/test_skill_runner_bridge.py`. | Manter como ponte entre agentic e execution_graph. |
| `src/agentic/squad_selector.py` | CORE | `tests/agentic/test_squad_selector.py`; `tests/execution_graph/test_e2e_vertical_slice.py`; recente fix `3d0d9be` em routing apps. | Manter; nao reabrir routing sem teste focado. |
| `src/agentic/forge_orchestrator.py` | EXPERIMENTAL | `tests/agentic/test_forge_orchestrator.py`; sem import externo operacional detectado em `src/cli.py`/`execution_graph`. | Preservar ate reconciliacao. Nao marcar morto porque tem testes e cobre gap->forge->register->rollback. |
| `src/agentic/__init__.py` | SUPPORT | Package boundary; arquivo minimo. | Nao adicionar `__all__` agora; sem teste de API publica do package. |

## Drift e duplicidade

- `forge_orchestrator.py`, `mission_engine.py` e `task_dispatcher.py` nao devem ser fundidos: engine gerencia lifecycle, dispatcher roteia deliverables, forge trata gap/registro/rollback.
- O maior risco nao e duplicidade interna: e ativar Forge/auto-criacao antes de governanca e rollback de runtime estarem provados.
- `CaptionDraftAgent` e o primeiro agente real recente; nao criar segundo agente antes de estabilizar esse fluxo.

## Type hints / modelos / funcoes longas

| Arquivo | Achado | Evidencia | Acao segura |
|---|---|---|---|
| `src/agentic/caption_draft_agent.py` | `CaptionDraftAgent.run()` tem 72 linhas. | AST: metodo publico >60 linhas. | Bom alvo futuro: extrair `_load_queue_item`, `_build_context`, `_create_draft`, `_finalize_run` dentro do mesmo arquivo. |
| `src/agentic/agent_models.py` | `from_dict(cls, ...)` sem annotation em `cls`. | AST classmethod. | Baixo valor; nao mexer agora. |
| `src/agentic/deliverable_mapper.py` | `DeliverableSpec` nao tem `to_dict/from_dict`. | Dataclass sem metodo, mas `DeliverableManifest.to_dict/from_dict` cobre serializacao. | Nao adicionar metodo sem teste exigindo. |
| `src/agentic/forge_orchestrator.py` | Dataclasses `GapReport`, `ForgeResult`, `SkillVersion` tem `to_dict`, sem `from_dict`. | Testes nao exigem round-trip. | Nao mexer agora. |
| `src/agentic/squad_selector.py` | Dataclasses tem `to_dict`, sem `from_dict`. | Testes focam selecao/assign/capabilities. | Nao mexer agora. |

---

# 4. Resultado por pergunta da Phase 1

## Quais arquivos parecem canonicos

- Reports: `status_report.py`, `briefing.py`, `report_generator.py`.
- Memory: `interface.py`, `akasha_reader.py`, `context_builder.py`.
- Agentic: `agent_models.py`, `caption_draft_agent.py`, `mission_intake.py`, `mission_engine.py`, `deliverable_mapper.py`, `task_dispatcher.py`, `skill_runner_bridge.py`, `squad_selector.py`.

## Quais parecem suporte

- Reports: `cockpit_generator.py`, `output_viewer_data.py`, `cockpit_data_all.py`.
- Memory: `learning_reuse.py`, `learning_writer.py`, `writeback.py`, `embeddings.py`, `learning_sources.py`, `qdrant_indexer.py`.
- Agentic: `__init__.py`.

## Quais parecem duplicados

- Nenhum duplicado confirmado dentro destas tres familias.
- Possivel drift externo a tratar depois:
  - `src/memory/` vs `src/memory_intel/` vs `src/memory_pack/` vs `src/memory_unification/`.
  - `src/reports/` vs `src/observability/` em leitura de estado.
  - `src/agentic/forge_orchestrator.py` vs familias de `capability_forge*`, fora do escopo desta rodada.

## Quais parecem orfaos

Orfao operacional, mas nao morto:

- `src/reports/cockpit_data_all.py`: sem import externo detectado; script executavel por `python -m`.
- `src/agentic/forge_orchestrator.py`: sem import externo operacional detectado; tem testes reais.

Nenhum deve ser movido/deletado nesta fase.

## Quais tem testes

- `tests/reports/`: `test_status_report.py`, `test_output_viewer_data.py`, `test_cockpit_generator.py`.
- `tests/memory/`: `test_context_builder.py`, `test_memory_interface.py`, `test_learning_reuse.py`, `test_learning_writer.py`, `test_writeback.py`, `test_embedding_strategy.py`, `test_e2e_dryrun.py`.
- `tests/agentic/`: `test_agent_models.py`, `test_caption_draft_agent.py`, `test_deliverable_mapper.py`, `test_forge_orchestrator.py`, `test_mission_engine.py`, `test_mission_intake.py`, `test_report_generator.py`, `test_skill_runner_bridge.py`, `test_squad_selector.py`, `test_task_dispatcher.py`, `test_mission_cli.py`.
- Fora da pasta direta:
  - `tests/test_qdrant_indexer.py` cobre `src/memory/qdrant_indexer.py`.
  - `tests/test_briefing.py` cobre `src/reports/briefing.py`.
  - `tests/execution_graph/test_e2e_vertical_slice.py` cobre integracao com `agentic`.
  - `tests/api/test_api_routes.py` cobre reports via `src/api`, mas `src/api` nao foi tocado.

## Quais sao importados por outros modulos

- `src/reports/status_report.py`: `src/cli.py`, `src/api/routers/reports.py`, `tests/test_cli.py`.
- `src/reports/briefing.py`: `src/cli.py`, `src/api/routers/reports.py`, `tests/test_briefing.py`.
- `src/reports/report_generator.py`: `src/cli.py`, `tests/agentic/test_report_generator.py`.
- `src/memory/akasha_reader.py`: `src/cli.py`, `src/reports/briefing.py`, `src/tool_registry/discovery.py`.
- `src/memory/interface.py`: `src/agentic/caption_draft_agent.py`, `tests/agentic/test_caption_draft_agent.py`.
- `src/memory/context_builder.py` e `learning_reuse.py`: usados por `MemoryInterface._real_query`.
- `src/memory/writeback.py`: usado por `learning_writer.py`.
- `src/agentic/mission_*`, `deliverable_mapper.py`: usados por `src/cli.py` e reports.
- `src/agentic/task_dispatcher.py` e `skill_runner_bridge.py`: usados por `execution_graph` e testes e2e.
- `src/agentic/squad_selector.py`: usado por testes e2e; fix recente de routing.

## Funcoes publicas sem type hints

Quase todas as funcoes publicas relevantes tem parametros e retornos anotados. Achados pequenos:

- `src/reports/cockpit_data_all.py::main` sem `-> None`.
- Classmethods `from_dict(cls, ...)` e `mock_default(cls)` aparecem sem annotation em `cls`, mas isso e padrao toleravel e nao vale uma mudanca isolada sem teste.
- Funcoes privadas de conexao, como `src/memory/akasha_reader.py::_connect`, nao foram tratadas como API publica.

## Modelos/dataclasses sem `to_dict/from_dict`

Nao ha lacuna que bloqueie testes atuais:

- Modelos que precisam serializar de volta tem `to_dict`.
- Modelos com round-trip testado tem `from_dict`.
- `DeliverableSpec` e dataclasses de squad/forge nao tem `from_dict`, mas sao serializados por containers ou nao possuem teste/contrato exigindo round-trip.

---

# 5. Proposta de slices executaveis futuros

## Slice 1 recomendado: Reports

Escopo: `src/reports/` + `tests/reports/` + `tests/test_briefing.py` se necessario.

Alteracoes seguras:

1. Adicionar `-> None` em `cockpit_data_all.main`.
2. Criar teste basico para `cockpit_data_all.generate_all(quiet=True)` com `tmp_path`/monkeypatch se for simples.
3. Refatorar `collect_missions()` em helpers privados, preservando output.

Gate:

```powershell
python -m pytest tests/reports/ tests/test_briefing.py --import-mode=importlib -p no:warnings -q
```

## Slice 2 recomendado: Memory

Escopo: `src/memory/` + `tests/memory/` + `tests/test_qdrant_indexer.py`.

Alteracoes seguras:

1. Refatorar `LearningWritebackService.writeback_from_journal()` em helpers privados dentro do mesmo arquivo.
2. Manter `MemoryInterface` como fachada; nao trocar imports externos.
3. Nao unificar `memory_intel`/`memory_pack` nesta slice.

Gate:

```powershell
python -m pytest tests/memory/ tests/test_qdrant_indexer.py --import-mode=importlib -p no:warnings -q
```

## Slice 3 recomendado: Agentic

Escopo: `src/agentic/` + `tests/agentic/` + `tests/execution_graph/test_e2e_vertical_slice.py`.

Alteracoes seguras:

1. Refatorar `CaptionDraftAgent.run()` em helpers privados no mesmo arquivo.
2. Nao mexer em `ForgeOrchestrator` ate decisao de ativacao/rollback.
3. Nao criar novo agente; evoluir apenas o agente minimo real.

Gate:

```powershell
python -m pytest tests/agentic/ tests/execution_graph/test_e2e_vertical_slice.py --import-mode=importlib -p no:warnings -q
```

---

# 6. Decisao de execucao desta rodada

Esta rodada deve parar em Phase 1 por seguranca.

Motivo:

- `src/api/` existe e esta em evolucao paralela pelo Claude Code.
- As tres familias estao verdes e com commits recentes.
- A mudanca mais valiosa agora e alinhar mapa/autoridade antes de mexer em codigo.
- Nenhum achado exige correcao imediata para manter a suite verde.

## Status final da proposta

| Area | Status |
|---|---|
| Reports | Preservar. Pequeno refactor futuro possivel em `cockpit_data_all.py`. |
| Memory | Preservar. `MemoryInterface` e fachada canonica; writeback e alvo futuro. |
| Agentic | Preservar. Fase 4 recente; `CaptionDraftAgent.run` e alvo futuro. |
| Arquivamento/delecao | Nenhum nesta rodada. |
| Risco P0 | Nenhum detectado dentro dessas tres familias. |
| Risco P1 | Ativar Forge antes de governanca/rollback; mexer em API paralela; consolidar memoria fora de ordem. |

