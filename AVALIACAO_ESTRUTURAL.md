# AVALIACAO_ESTRUTURAL — OMNIS (estado real)

Data: 2026-05-24  
Escopo: mapeamento estrutural somente (sem correção)  
Fonte de verdade: código em `src/` + comandos de busca de uso/import

---

## CAMADA 1 — Workflows

### Leitura objetiva
- O registry atual declara **19 workflows ativos** em `src/workflows/workflow_registry.py` (não 16).
- Existe um segundo stack de workflow em `src/workflow/engine.py` (pipeline IDEA→PLAN→BRIEF→PRODUCE→DRAFT), paralelo ao registry novo.
- Acoplamento entre workflows é baixo: composição explícita principalmente em `src/workflows/daily_briefing_workflow.py`.
- O sink de eventos (`akasha_event_sink`) é amplamente usado para **escrita**; leitura quase não aparece no fluxo dos workflows.

### Veredito por workflow do registry

| Workflow | Estado real | Evidência | Veredito | Risco |
|---|---|---|---|---|
| `deep_research` | Executa Lego de pesquisa + escreve evento | `src/workflows/deep_research_workflow.py` | 🟡 | Dependência externa + write-heavy |
| `video_edit` | Executa pipeline de vídeo + escreve evento | `src/workflows/video_edit_workflow.py` | 🟡 | Depende de FFmpeg/Whisper; sem loop de aprendizado acoplado |
| `app_factory` | Determinístico com gate de aprovação | `src/workflows/app_factory_workflow.py` | 🟡 | Fluxo válido, mas majoritariamente dry-run |
| `code_run` | Usa `CodeExecutorLego` + sink | `src/workflows/code_run_workflow.py` | 🟡 | Forte dependência de sandbox/serviço |
| `system_health` | Snapshot de saúde | `src/workflows/system_health_workflow.py` | 🟢 | Estruturado e previsível |
| `lead_scoring` | Scoring determinístico | `src/workflows/lead_scoring_workflow.py` | 🟢 | Fluxo local claro |
| `content_calendar` | Gera calendário/fila | `src/workflows/content_calendar_workflow.py` | 🟢 | Bom fluxo local |
| `sdr_pipeline` | Consolida modos execute/plan | `src/workflows/sdr_pipeline_workflow.py` | 🟡 | Composição interna ok, mas ainda sem forte real-world feedback |
| `daily_briefing` | Orquestra health+leads+calendar | `src/workflows/daily_briefing_workflow.py` | 🟢 | Única composição clara entre workflows |
| `content_quality` | Instancia adapter abstrato por default | `src/workflows/content_quality_workflow.py` + `src/akasha_event_sink/adapter.py` | 🔴 | Risco de quebra em runtime |
| `metrics_snapshot` | Instancia adapter abstrato por default | `src/workflows/metrics_snapshot_workflow.py` + `src/akasha_event_sink/adapter.py` | 🔴 | Risco de quebra em runtime |
| `squad_assignment` | Instancia adapter abstrato por default | `src/workflows/squad_assignment_workflow.py` + `src/akasha_event_sink/adapter.py` | 🔴 | Risco de quebra em runtime |
| `deliverable_mapping` | Instancia adapter abstrato por default | `src/workflows/deliverable_mapping_workflow.py` + `src/akasha_event_sink/adapter.py` | 🔴 | Risco de quebra em runtime |
| `task_dispatch` | Instancia adapter abstrato por default | `src/workflows/task_dispatch_workflow.py` + `src/akasha_event_sink/adapter.py` | 🔴 | Risco de quebra em runtime |
| `capability_forge` | Instancia adapter abstrato por default | `src/workflows/capability_forge_workflow.py` + `src/akasha_event_sink/adapter.py` | 🔴 | Risco de quebra em runtime |
| `skill_execution` | Usa `MockAkashaSink` por default | `src/workflows/skill_execution_workflow.py` | 🟡 | Funciona, mas default simulado |
| `content_brief` | Sink default sem `target_dir` | `src/workflows/content_brief_workflow.py` + `src/akasha_event_sink/adapter.py` | 🔴 | Construtor incompatível |
| `hotel_pitch` | Sink default sem `target_dir` | `src/workflows/hotel_pitch_workflow.py` + `src/akasha_event_sink/adapter.py` | 🔴 | Construtor incompatível |
| `caption_generator` | Sink default sem `target_dir` | `src/workflows/caption_generator_workflow.py` + `src/akasha_event_sink/adapter.py` | 🔴 | Construtor incompatível |

### Ilhas e encadeamento
- **Ilhas (predominante):** vários workflows só escrevem evento de saída sem consumir memória/saída de outros.
- **Encadeamento real visível:** `daily_briefing` chama outros workflows (`system_health`, `lead_scoring`, `content_calendar`).
- **Stack paralelo:** `src/workflow/engine.py` é outro orquestrador funcional e não o mesmo da família `src/workflows/*`.

**Resumo da camada:** há capacidade real, mas com fragmentação e múltiplos pontos de runtime frágil em construtores/sinks.

---

## CAMADA 2 — Orquestração (agency, squad_selector, mission_orchestrator)

### O que funciona de verdade
- `src/agentic/mission_orchestrator.py` tem caminho claro: brief → agency → workflow registry → evento.
- `src/agentic/agency.py` e `src/agentic/squad_selector.py` têm lógica determinística e tipada.

### Onde o elo está quebrado/desalinhado
- A CLI principal de orquestração usa **outro pacote**: `src/cli_commands/mission_orchestrator_cmd.py` chama `src/mission_orchestrator/service.py`.
- `src/mission_orchestrator/executor.py` executa sequência de steps (`s01`, `s02`) e `mission_builder`, não o `WorkflowRegistry` da camada agentic.
- Resultado: coexistem dois caminhos de orquestração com papéis parecidos, sem unificação completa de execução.

| Componente | Estado | Veredito | Risco |
|---|---|---|---|
| `src/agentic/mission_orchestrator.py` | Orquestração real de workflow registry | 🟡 | Pode ficar subutilizado no fluxo CLI |
| `src/mission_orchestrator/service.py` + `executor.py` | Fluxo operacional de CLI (step-based) | 🟡 | Paralelismo de arquitetura |
| `src/agentic/agency.py` / `squad_selector.py` | Coordenação determinística | 🟢 | Baixo, desde que bem acoplado ao fluxo oficial |

**Resumo da camada:** existe coordenação real, mas em dois trilhos que ainda não convergiram totalmente.

---

## CAMADA 3 — Memória (Akasha)

### O que funciona de verdade
- `src/akasha_event_sink/adapter.py` implementa interface e persistência por arquivo (`FileAkashaSink`) e mock (`MockAkashaSink`).
- `src/memory/caption_memory.py` implementa write/read com lock (`jsonl_write_lock`), com consumo em `src/memory/interface.py` (via `CaptionMemoryReader`).
- Há leitura de banco em `src/memory/akasha_reader.py`.

### Write-only vs read path
- `write_event(...)` é amplamente usado pelos workflows.
- `query_events(...)` praticamente não aparece sendo consumido no fluxo principal (busca mostrou uso concentrado na própria implementação).
- Isso confirma uma tendência **write-heavy**: muito registro, pouca retroalimentação via sink.

| Componente | Estado | Veredito | Risco |
|---|---|---|---|
| `akasha_event_sink` (eventos) | Forte em escrita | 🟡 | Cola fraca entre execução e reuso |
| `memory/interface.py` + `caption_memory.py` | Há leitura real para casos específicos | 🟢 | Funciona, mas escopo ainda parcial |
| `memory/akasha_reader.py` | Leitura direta com DSN default local | 🟡 | Portabilidade/segurança de config |

**Resumo da camada:** não é 100% write-only, mas a cola de memória ainda é parcial e concentrada em poucos fluxos.

---

## CAMADA 4 — Governança (approval gate, caption_approval)

### O que funciona de verdade
- Gate unificado em `src/approval_center/gate.py`.
- Aplicação de gate no fluxo de graph/orchestrator:
  - `src/mission_orchestrator/approval_gate.py`
  - `src/execution_graph/approval_bridge.py`
  - `src/execution_graph/mission_bridge.py`
- Aprovação editorial conectada no agente:
  - `src/agentic/caption_draft_agent.py` usa `src/caption_approval/approvals.py`.

### O que está frouxo/paralelo
- Existem gates locais por palavra-chave em alguns legos (ex.: `code_executor_lego`, `video_processor_lego`, `research_conductor_lego`, `channel_messenger_lego`) em vez de um único ponto de política para tudo.

| Componente | Estado | Veredito | Risco |
|---|---|---|---|
| Gate unificado (`approval_center`) | Conectado no execution path principal | 🟢 | Bom para freio de risco |
| `caption_approval` | Integrado ao fluxo do caption agent | 🟢 | Bom no domínio editorial |
| Gates locais por lego | Regras locais, não totalmente centralizadas | 🟡 | Inconsistência de governança |

**Resumo da camada:** governança existe e está conectada em trilhas críticas, mas ainda há política distribuída em módulos.

---

## CAMADA 5 — Pontas externas (publish, analytics, atendimento)

### O que realmente toca o mundo
- **Mensageria outbound real:** `src/legos/channel_messenger_lego.py` (WhatsApp/Telegram via HTTP).
- **Pesquisa web real:** `src/legos/research_conductor_lego.py` (LLM + backend web quando configurado).
- **Navegação real:** `src/legos/browser_executor_lego.py` com Playwright.
- **Bridge Publisher OS real (localhost):** `src/workflow/publisher_bridge.py` chama endpoints HTTP (`:8000`) para crew/MCP.

### O que é modelo/fachada
- `src/publisher_argos/planner.py` declara explicitamente dry-run/modeling only (não publica de fato).
- `src/analytics/service.py` é determinístico local (sem rede/DB/LLM).
- `src/remote_control/router.py` bloqueia modo real (`real remote execution disabled`) e executa apenas em dry-run.

| Componente | Estado | Veredito | Risco |
|---|---|---|---|
| ChannelMessengerLego | Saída externa real | 🟡 | Precisa disciplina forte de gate/política |
| ResearchConductorLego | Busca/LLM real | 🟡 | Depende de validação robusta de destino |
| BrowserExecutorLego | Navegação real com sandbox | 🟡 | Alto impacto se regras de sandbox falharem |
| Publisher Argos Planner | Planejamento somente | 🔴 | Não é publicação real |
| Analytics service | Núcleo local de cálculo | 🟢 | Baixo risco externo |
| Remote control router | Dry-run por design | 🟡 | Funciona como proteção, não como execução real |

**Resumo da camada:** o sistema já tem portas externas reais, mas algumas “pontas de negócio” seguem em modo modelagem/dry-run.

---

## CAMADA 6 — Segurança (resumo)

### Achados principais
- **RCE (status atual):** em `src/legos/code_executor_lego.py` o goal vai como argumento, sem interpolação direta no script; há bloqueio de payload suspeito.  
  Veredito: risco caiu, mas ainda depende de política de sandbox consistente.
- **SSRF:** guardas explícitas em `src/legos/research_conductor_lego.py` e `src/computer_use/sandbox.py` (loopback, redes privadas, 169.254/16 etc.).
- **Path traversal:** proteção explícita em `src/legos/video_processor_lego.py` (`_assert_path_safe`).
- **Secrets/hardcoded dev creds:** ainda existem defaults locais sensíveis, por exemplo:
  - `src/memory/akasha_reader.py` (DSN default com credencial local),
  - `src/memory_unification/memory_router.py` (`password=postgres` inline).

| Tema | Estado | Veredito | Risco |
|---|---|---|---|
| RCE (code executor) | Mitigado em relação ao vetor original | 🟡 | Requer vigilância contínua |
| SSRF | Bloqueios implementados | 🟢 | Bom, manter testes de regressão |
| Path traversal | Bloqueio implementado | 🟢 | Bom, manter testes |
| Hardcoded credenciais dev | Ainda presente em módulos | 🔴 | Risco de governança/portabilidade |

**Resumo da camada:** não há “terra arrasada” de segurança agora, mas ainda há passivos de configuração e superfícies sensíveis que pedem monitoramento contínuo.

---

## TABELA-RESUMO FINAL (por camada)

| Camada | Funciona de verdade | Mock/Fachada | Desconectado/Frouxo | Risco geral |
|---|---|---|---|---|
| 1. Workflows | Parte relevante roda | Vários defaults simulados | Diversos fluxos ilhados + construtores frágeis | **Alto** |
| 2. Orquestração | Há coordenação funcional | — | Dois trilhos de orquestração coexistindo | **Médio-Alto** |
| 3. Memória | Há leitura real pontual | — | Eventos mais write do que read | **Médio** |
| 4. Governança | Gate central aplicado em trilhas críticas | — | Regras locais distribuídas por lego | **Médio** |
| 5. Pontas externas | Mensageria, pesquisa, browser e bridge HTTP reais | Planner Argos ainda modelagem | Alguns caminhos ainda dry-run-only | **Médio-Alto** |
| 6. Segurança | SSRF/path traversal com proteção | — | Credenciais dev hardcoded em pontos específicos | **Médio-Alto** |

---

## Veredito geral

O sistema **já opera partes reais relevantes**, mas ainda com **arquitetura parcialmente bifurcada** (orquestração/workflows) e com **degraus frágeis** em alguns workflows por construção de sink default.  
Para evoluir com segurança, o primeiro ganho estrutural não é “mais feature”, e sim **fechar os pontos vermelhos de runtime/configuração** e consolidar o trilho oficial de execução.

