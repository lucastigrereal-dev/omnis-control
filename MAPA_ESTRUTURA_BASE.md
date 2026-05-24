# MAPA_ESTRUTURA_BASE — Esqueleto de Dependências OMNIS
**Gerado:** 2026-05-24 — análise AST estática de `src/` (~110 módulos)  
**Escopo:** fatos do código. Sem avaliação.

---

## 1. MAPA DE MÓDULOS — quem importa quem

### Módulos centrais (focados nos solicitados)

```
workflows          → agentic, akasha_event_sink, app_factory, commercial_sdr,
                     content_queue, interfaces, legos, metrics,
                     multi_model_orchestration, quality_gate, utils

agentic            → akasha_event_sink, caption_approval, content_queue,
                     legos, memory, skills_bridge, utils, workflows

execution_graph    → agentic, approval_center, mission_orchestrator,
                     skills_bridge, squad_composer, task_decomposer

runtime_bridge     → execution_graph, execution_queue

mission_orchestrator (src/agentic/) → agentic (agency, mission_engine),
                     workflows (workflow_registry), akasha_event_sink, utils

approval_center    ← importado por 41 módulos (hub de aprovação)

akasha_event_sink  ← importado por 56 módulos (hub de eventos — #1 do projeto)

legos              → computer_use, interfaces, video_studio

routers            → cli_commands

cli_commands       → approval_center, argos_bridge, asset_assignment,
                     capability_forge_real, caption_approval, checkers,
                     content_queue, execution_graph, mission_orchestrator,
                     offline_factory, omnis_health, pipeline_local,
                     squad_composer, task_decomposer, work_order
                     (+ ~30 outros módulos — fat leaf)
```

### Nota sobre `agentic` ↔ `workflows`
Importação cruzada controlada: `agentic/mission_orchestrator.py` importa
`workflows.workflow_registry`; vários `workflows/*.py` importam de `agentic`
(llm_adapter, agency, squad_selector). Não é ciclo de init — são imports
dentro de funções em alguns casos.

---

## 2. FLUXO DE DADOS — caminho real de uma missão

```
ENTRADA
  └── MissionBrief(setor, workflow_name, objetivo, workflow_kwargs)

MissionOrchestrator.orchestrate()           src/agentic/mission_orchestrator.py
  │
  ├─ 1. Cria MissionContract(mission_id, status="open", setor)
  │
  ├─ 2. AgencyRegistry.route_mission(contract)
  │       └── Agency.accept_mission(contract)
  │               └── SquadSelector.assign(sector) → SquadAssignment
  │               └── SinkEvent("mission_accepted") → akasha_event_sink
  │
  ├─ 3. WorkflowRegistry.run(workflow_name, **workflow_kwargs)
  │       └── WorkflowEntry.factory() → instancia o workflow
  │       └── workflow_instance.run(**kwargs) → resultado
  │               └── RunContext.new() → serviço(s) → SinkEvent → FileAkashaSink
  │
  ├─ 4. Agency.complete_mission(mission_id) → SinkEvent("mission_completed")
  │
  └─ 5. SinkEvent("orchestration_completed") → FileAkashaSink.write_event()

SAÍDA: OrchestrationResult(run_id, mission_id, success, setor, workflow_result)
```

**Caminho alternativo (execution_graph / runtime_bridge) — P37-P42:**
```
MissionBrief
  └── execution_graph/mission_bridge.py
        ├── task_decomposer → squad_composer → execution_graph/builder → StepRun[]
        ├── approval_center/gate.check_gate() → GATE_PASS | GATE_BLOCKED
        └── execution_graph/runner.run_graph_dry()
              └── runtime_bridge/bridge.RuntimeBridge
                    └── execution_queue/queue.ExecutionQueue.run(item)
```

**ATENÇÃO:** Pipeline B (execution_graph → runtime_bridge → execution_queue)
existe mas não está ligado ao `MissionOrchestrator` principal.
São dois pipelines paralelos sem handoff automático entre si.

---

## 3. PONTOS DE ENTRADA

| Entry point | Arquivo | Dispara |
|---|---|---|
| **CLI principal** | `src/cli.py` | Typer app com 40+ comandos: queue, captions, video-assets, missions, accounts, argos, sales, llm, reports, omnis |
| **Sub-routers CLI** | `src/routers/` | Sub-typers via cli_commands: assets, offline, render, quality, campaign, manual-publish, delivery, dashboard |
| **API REST** | `src/api/main.py` | FastAPI — importa apenas `src.api.routers` (único import src/) |
| **Daemon Redis** | `src/event_listener.py` | `OmnisEventListener.listen()` — subscribe Redis pub/sub, processa eventos. **Não importa nenhum módulo src/**. Standalone puro. |
| **CLI autônomo** | `src/autonomous_execution/cli.py` | Execução autônoma de missões — importa `omnis_supreme` |
| **CLI OS** | `src/omnis_os/cli.py` | Comandos OMNIS OS level |
| **CLI live cockpit** | `src/live_cockpit/cli.py` | Dashboard terminal — importa memory_intel, observability_local, omnis_supreme |

**Qual entry point aciona qual pipeline:**

```
cli.py → caption_approval, content_queue, video_assets, routers, runners.skill_runner,
         agentic (deliverable_mapper, mission_engine, mission_intake)
       → NÃO chama MissionOrchestrator diretamente na maioria dos comandos
       → chama via cli_commands → mission_orchestrator (indirect)

api/main.py → src.api.routers (único import src/)
            → NÃO chama MissionOrchestrator

event_listener.py → Redis subscribe → handler interno
                  → NÃO importa nada de src/
                  → receptor de eventos, não dispatcher de missões

autonomous_execution → omnis_supreme → campaign_manager, delivery_portal,
                        governance, marketing, memory_pack, observability_local,
                        publisher_argos
```

---

## 4. ÓRFÃOS — módulos que nenhum outro src/ importa

### Entry points (aparência de órfão — são tops da cadeia)
| Módulo | Tipo | Observação |
|---|---|---|
| `api` | Entry point REST | FastAPI app |
| `cli.py` | Entry point CLI | Typer app |
| `cli_agent.py` | Entry point CLI | Sub-CLI agents |
| `cli_lego.py` | Entry point CLI | Sub-CLI legos |
| `cli_local.py` | Entry point CLI | Sub-CLI local |
| `event_listener.py` | Entry point daemon | Redis standalone |
| `autonomous_execution` | Entry point CLI | Execução autônoma |
| `live_cockpit` | Entry point CLI | Dashboard terminal |
| `local_search` | Entry point | Tem `__main__` próprio |
| `mission_replay` | Entry point | Tem `__main__` próprio |

### Órfãos funcionais (sem importador, sem entry point reconhecido)
| Módulo | Imports externos | Observação |
|---|---|---|
| `akasha_runtime` | 0 | Módulo legado sem conexão ativa |
| `automation` | 0 | Templates n8n — sem importador Python |
| `autonomy` | 0 | Arquivos existem, zero conexões |
| `commercial` | `sales` | Importa sales mas ninguém importa commercial |
| `design_art` | 0 | Sem conexão |
| `finance` | 0 | Modelos financeiros isolados |
| `kratos_bridge` | 0 | Bridge para KRATOS — sem uso ativo em src/ |
| `memory_unification` | 0 | Sem importador |
| `mission` | `mission_builder, missions` | Importa outros mas ninguém importa mission |
| `omnis_bus` | 0 | `CanonicalEnvelope`, `Channel` — event_listener.py NÃO importa via src |
| `plugin_runtime` | 0 | Sem conexão |
| `preview` | 0 | Sem importador |
| `production_hardening` | `remote_control` | Sem importador |
| `publishing` | `skills` | Importa skills mas ninguém importa publishing |
| `real_world_actions` | `governance` | Sem importador |
| `runtime_bridge` | `execution_graph, execution_queue` | Ninguém importa runtime_bridge |
| `self_improvement` | 0 | Sem conexão |
| `war_room_bridge` | 0 | Sem conexão |

---

## 5. GRAFO DE ACOPLAMENTO

### HUBs — muita coisa depende deles

| Módulo | Importado por (# arquivos) | Papel |
|---|---|---|
| `akasha_event_sink` | **56x** | SinkEvent, FileAkashaSink, MockAkashaSink — barramento de eventos #1 |
| `approval_center` | **41x** | ApprovalRequest, check_gate — gate de aprovação |
| `utils` | **40x** | logger, run_context, safe_paths — base universal |
| `cli_commands` | **37x** | orquestrador de sub-comandos CLI |
| `content_queue` | **33x** | AccountRegistry, Queue, QueueItem — modelo de fila de conteúdo |
| `caption_approval` | **31x** | CaptionDraft, ApprovalGate, DraftsManager |
| `agentic` | **31x** | llm_adapter, agency, squad_selector, mission_engine |
| `capability_forge_real` | **26x** | ForgeEngine — pipeline de forja de capacidades |
| `execution_graph` | **25x** | StepRun, GraphBuilder — núcleo de execução paralela |
| `work_order` | **23x** | modelos de ordens de trabalho |
| `missions` | **20x** | modelos de missões |

### FOLHAS — importadas por poucos, importam muitos

| Módulo | Importado_por | Importa | Tipo |
|---|---|---|---|
| `cli_commands` | 2 (cli.py + routers) | **40+** | Fat leaf — orquestrador de UI |
| `workflows` | 2 (agentic + workflows interno) | 11 | Fat leaf — 20 capacidades finais |
| `execution_graph/mission_bridge` | ~1 | 7 | Fat leaf — pipeline P37 |
| `api` | 0 | `api.routers` | Fat leaf — entry point REST |
| `autonomous_execution` | 0 | `omnis_supreme` | Fat leaf — entry point CLI |

### ISOLADOS funcionais (imported_by=0, imports_src=0)

```
akasha_runtime   — legado sem conexão ativa
automation       — templates n8n, sem importador Python
autonomy         — sem conexão
design_art       — sem conexão
finance          — sem conexão
kratos_bridge    — bridge KRATOS, sem uso ativo
memory_unification — sem importador
omnis_bus        — CanonicalEnvelope/Channel sem uso confirmado em src/
self_improvement — sem conexão
war_room_bridge  — sem conexão
```

---

## RESUMO ESTRUTURAL

```
                    ┌──────────────────────────────────────┐
ENTRY POINTS        │  cli.py  api/  event_listener.py     │
                    └──────┬──────────┬────────────────────┘
                           │          │ (Redis, standalone — sem imports src/)
                    ┌──────▼──────────▼────────────────────┐
ORCHESTRATION       │   agentic/mission_orchestrator        │
                    │   Agency → SquadSelector              │
                    └──────┬───────────────────────────────┘
                           │
              ┌────────────▼──────────────────────────────┐
REGISTRY      │     workflows/workflow_registry             │
              │     WorkflowRegistry.default()             │
              │     (20 workflows registrados)             │
              └────────────┬──────────────────────────────┘
                           │
         ┌─────────────────┼──────────────────────────┐
WORKFLOWS │ content_calendar│ caption_generator         │
(ilhas)   │ sdr_pipeline   │ hotel_pitch               │
          │ content_brief  │ lead_scoring              │
          │ seogram        │ deep_research             │
          │ ...14 mais...  │                           │
         └────────┬────────┴──────────────────────────┘
                  │  (todos write-only)
         ┌────────▼──────────────────────────────────────┐
SINK      │  akasha_event_sink (FileAkashaSink)           │
          │  SinkEvent → data/akasha_events.jsonl         │
         └───────────────────────────────────────────────┘

PARALELO (não conectado ao orchestrator principal):
execution_graph → runtime_bridge → execution_queue
                ↑
         approval_center/gate
```

**Dois pipelines existem lado a lado sem se tocar:**
- Pipeline A: `MissionOrchestrator → Agency → WorkflowRegistry → Workflow → AkashaSink`
- Pipeline B: `execution_graph → runtime_bridge → execution_queue → ApprovalCenter`

**`runtime_bridge` é órfão de importador:** existe e funciona mas nenhum módulo src/ o chama.

**Akasha é write-only:** nenhum módulo lê do sink para alimentar o próximo passo.

**`omnis_bus` desconectado:** `CanonicalEnvelope`/`Channel` existem mas event_listener.py não os importa via src/.
