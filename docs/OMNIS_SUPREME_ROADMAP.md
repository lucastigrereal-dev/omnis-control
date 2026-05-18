# OMNIS SUPREME — ROADMAP COMPLETO DE ENTREGA AGENTIC
**Data:** 2026-05-18 | **Versão:** 1.0 | **Operador:** Lucas Tigre

> Premissa: OMNIS executa e entrega pacote. Você posta. Sem conexão externa até o pacote estar pronto.

---

## DIAGNÓSTICO — O QUE JÁ EXISTE (não reescrever)

### Módulos funcionais em `omnis-appfactory/src/`
| Módulo | Status | O que faz |
|---|---|---|
| `mission_orchestrator/` | ✅ Funcional | planner, executor, approval_gate, service |
| `execution_graph/` | ✅ Funcional | builder, runner, retry, rollback, circuit_breaker, metrics |
| `squad_composer/` | ✅ Funcional | composer, models, templates, service |
| `skills_bridge/` | ✅ Funcional | selection (semântica), adapter, dryrun |
| `capability_forge_real/` | ✅ Funcional | builder, evaluator, sandbox, scaffold, test_generator |
| `providers/` | ✅ Funcional | registry, embedding (TFIDF+ST), tracing (Langfuse), memory (Akasha) |
| `governance/` | ✅ Parcial | models, service — falta runtime enforcement |
| `commercial/` | ✅ Funcional | lead_qualifier, hotel_lead, lead_pipeline (BANT + semântico) |
| `omnis_health/` | ✅ Funcional | models, server, checks |

### Skills em `~/.claude/skills/` e `omnis-control/skills/`
| Skill | Uso no Supreme |
|---|---|
| `jarvis-router` | Intent Router Agent |
| `jarvis-brain` | Memory Retrieval + Context Builder |
| `jarvis-delegate` | Task Dispatcher |
| `jarvis-guardrails` | Guardrails Agent |
| `jarvis-decide` | Approval Gate |
| `jarvis-memory-write` | Learning Loop |
| `skill-creator` | Capability Forge |
| `generate_seogram_caption` | Publisher Execution (legendas) |
| `create_30_day_content_calendar` | Mission Planner (marketing) |
| `create_sales_dm_sequence` | Sales Execution Agent |
| `create_instagram_carousel` | Publisher Execution (carrossel) |
| `export_content_batch_to_csv` | Deliverable Mapper (export) |
| `argos-bridge` | Publisher Bridge |
| `revenue-tracker` | Finance + Metrics Agent |
| `crm-pipeline` | Sales Execution Agent |
| `video_to_content` | Video Studio Executor |

### O que falta construir (GAP real)
- `mission_engine.py` — cria `mission_id`, pasta `missions/<id>/`, `mission_contract.json`
- `mission_reporter.py` — gera `relatorio_final.md` e fecha pacote
- `approval_gate.py` runtime — intercepta em runtime (o modelo tem só models)
- `learning_writer.py` — grava `10_learnings.md` + writeback Akasha
- `autonomy_supervisor.py` — controla nível N0→N7
- `task_dispatcher.py` standalone — roteia para executor certo
- `observability_agent.py` — trace por missão com custo
- `report_generator.py` — consolida todos os MDs em `relatorio_final.md`
- Cockpit HTML local — painel de missões/aprovações/outputs

---

## MAPA DOS 30 AGENTES — ONDE CADA UM VIVE

```
src/agentic/           ← agentes de entrada e planejamento (1–8)
src/capability_forge/  ← forja de skills (9–10) [já existe capability_forge_real/]
src/executors/         ← workers de execução (11–22)
src/governance/        ← guardrails, gate, risco (23–24)
src/quality/           ← validação e QA (25)
src/observability/     ← trace, métricas, custo (26–27)
src/memory/            ← learning loop e writeback (28)
src/reports/           ← gerador de relatório (29)
src/autonomy/          ← supervisor de autonomia (30)
```

| # | Agente | Arquivo | Status |
|---|---|---|---|
| 1 | Mission Intake | `src/agentic/mission_intake.py` | 🔴 BUILD |
| 2 | Intent Router | `skills/jarvis-router` | ✅ EXISTS |
| 3 | Memory Retrieval | `skills/jarvis-brain` | ✅ EXISTS |
| 4 | Context Builder | `src/knowledge_context/` | ⚠️ WRAP |
| 5 | Mission Planner | `src/mission_orchestrator/planner.py` | ✅ EXISTS |
| 6 | Deliverable Mapper | `src/agentic/deliverable_mapper.py` | 🔴 BUILD |
| 7 | Squad Composer | `src/squad_composer/composer.py` | ✅ EXISTS |
| 8 | Skill Matcher | `src/skills_bridge/selection.py` | ✅ EXISTS |
| 9 | Gap Detector | `src/capability_gap/` | ✅ EXISTS |
| 10 | Capability Forge | `src/capability_forge_real/` | ✅ EXISTS |
| 11 | Execution Graph | `src/execution_graph/` | ✅ EXISTS |
| 12 | Task Dispatcher | `src/agentic/task_dispatcher.py` | 🔴 BUILD |
| 13 | Skill Runner | `src/runners/` | ⚠️ WRAP |
| 14 | Code Executor | `src/autonomous_execution/` | ⚠️ WRAP |
| 15 | Browser Automation | `src/executors/browser_executor.py` | 🔴 BUILD |
| 16 | Workflow Runner | `src/automation/` | ⚠️ WRAP |
| 17 | Publisher Agent | `src/publisher_argos/` + `skills/argos-bridge` | ⚠️ WRAP |
| 18 | Sales Agent | `src/commercial/lead_pipeline.py` + `skills/crm-pipeline` | ⚠️ WRAP |
| 19 | App Factory | `src/app_factory_supreme/` | ⚠️ WRAP |
| 20 | Analytics Agent | `src/analytics/` | ⚠️ WRAP |
| 21 | Finance Agent | `src/finance/` + `skills/revenue-tracker` | ⚠️ WRAP |
| 22 | Computer Ops | `src/computer_ops/` | ⚠️ WRAP |
| 23 | Guardrails | `src/governance/service.py` | ⚠️ ENFORCE |
| 24 | Approval Gate | `src/mission_orchestrator/approval_gate.py` | ⚠️ WIRE |
| 25 | Validator / QA | `src/quality_layer/` | ⚠️ WIRE |
| 26 | Observability | `src/observability/` + Langfuse | ⚠️ WIRE |
| 27 | Metrics | `src/metrics/` | ⚠️ WRAP |
| 28 | Learning Loop | `src/memory/learning_writer.py` | 🔴 BUILD |
| 29 | Report Generator | `src/mission_report/` | ⚠️ WIRE |
| 30 | Autonomy Supervisor | `src/autonomy/supervisor.py` | 🔴 BUILD |

**Legenda:** ✅ EXISTS = usar direto | ⚠️ WRAP = conectar ao pipeline | 🔴 BUILD = criar do zero

---

## ESTRUTURA DE MISSÃO (padrão de entrega)

```
missions/
└── <MISSION_ID>/               ← ex: MIS-20260518-001
    ├── mission_contract.json   ← gerado pelo Mission Intake
    ├── 01_mission_brief.md
    ├── 02_context_used.md
    ├── 03_execution_plan.md
    ├── 04_squad_assigned.md
    ├── 05_outputs/             ← arquivos gerados pelos executores
    ├── 06_exports/             ← CSV, ZIPs, pacotes prontos pra postar
    ├── 07_approval/            ← approval_request.md + approval_status.json
    ├── 08_logs/                ← task_dispatch_log.jsonl + mission_trace.jsonl
    ├── 09_next_action.md
    ├── 10_learnings.md
    └── relatorio_final.md
```

---

## FLUXO DE EXECUÇÃO COMPLETO

```
LUCAS digita missão
        ↓
[1] Mission Intake → mission_contract.json + pasta missions/<id>/
        ↓
[2] Intent Router (jarvis-router) → setor + risco + formato
        ↓
[3] Memory Retrieval (jarvis-brain) → busca Akasha + Obsidian
        ↓
[4] Context Builder → 02_context_used.md limpo
        ↓
[5] Mission Planner → 03_execution_plan.md + execution_plan.json
        ↓
[6] Deliverable Mapper → deliverables_manifest.json (arquivos exatos)
        ↓
[7] Squad Composer → 04_squad_assigned.md
        ↓
[8] Skill Matcher → skill_execution_map.json
        ↓
    [skill existe?]
    ├── SIM → continua
    └── NÃO → [9] Gap Detector → [10] Capability Forge → nova skill testada
        ↓
[11] Execution Graph → grafo sequencial/paralelo com deps e retries
        ↓
[12] Task Dispatcher → roteia cada task para executor certo:
    ├── [13] Skill Runner     (skills Python)
    ├── [14] Code Executor    (app factory, scripts, patches)
    ├── [15] Browser Agent    (pesquisa web, formulários)
    ├── [16] Workflow Runner  (n8n, automações)
    ├── [17] Publisher Agent  (legendas, calendário, exports CSV)
    ├── [18] Sales Agent      (leads, DMs, propostas, pipeline)
    ├── [19] App Factory      (PRD, schema, API, frontend, testes)
    ├── [20] Analytics Agent  (relatórios, ROI, métricas)
    ├── [21] Finance Agent    (pricing, forecast, comissão)
    └── [22] Computer Ops     (audit, organização, health check)
        ↓
[23] Guardrails → bloqueia ação destrutiva/externa
        ↓
[24] Approval Gate → dry-run → mostra pacote → LUCAS aprova → executa
        ↓
[25] Validator / QA → checa formato, tom, completude
        ↓
[26] Observability → trace JSONL + Langfuse + custo por execução
        ↓
        05_outputs/ + 06_exports/ preenchidos
        ↓
[27] Metrics → performance_report.md
        ↓
[28] Learning Loop → 10_learnings.md + writeback Akasha
        ↓
[29] Report Generator → relatorio_final.md (pacote fechado)
        ↓
[30] Autonomy Supervisor → registra nível usado, logs SLO
        ↓
MISSION PACKAGE PRONTO → LUCAS posta / envia / usa
```

---

## ROADMAP DE CONSTRUÇÃO — 6 FASES

### FASE A — NÚCLEO DE MISSÃO (Semana 1)
> Toda missão nasce com ID, cria pasta, termina com relatório.

| Wave | Entrega | Arquivo |
|---|---|---|
| W-A1 | `MissionEngine` — cria ID, pasta, `mission_contract.json` | `src/agentic/mission_engine.py` |
| W-A2 | `MissionIntake` — extrai objetivo, prazo, tipo, risco do texto livre | `src/agentic/mission_intake.py` |
| W-A3 | `DeliverableMapper` — define arquivos exatos de saída | `src/agentic/deliverable_mapper.py` |
| W-A4 | `ReportGenerator` — consolida tudo em `relatorio_final.md` | `src/reports/report_generator.py` |
| W-A5 | `MissionCLI` — `omnis mission "texto"` roda o fluxo completo | `src/cli.py` atualizado |

**Gate:** `omnis mission "cria campanha hotel"` → cria `missions/MIS-xxx/`, preenche 01–04, gera `relatorio_final.md`.

---

### FASE B — EXECUÇÃO RASTREADA (Semana 1–2)
> Skills rodam com log, retry e status por etapa.

| Wave | Entrega | Arquivo |
|---|---|---|
| W-B1 | `TaskDispatcher` — roteia task → executor correto | `src/agentic/task_dispatcher.py` |
| W-B2 | `SkillRunner` wired — conecta `skills_bridge/selection.py` ao dispatcher | `src/runners/skill_runner.py` |
| W-B3 | Execution log por task — `08_logs/task_dispatch_log.jsonl` | via `execution_graph/` |
| W-B4 | Dry-run universal — toda task executa em modo dry por padrão | flag em `task_dispatcher` |
| W-B5 | `LearningWriter` — grava `10_learnings.md` + writeback Akasha | `src/memory/learning_writer.py` |

**Gate:** Missão roda 3+ skills em sequência, cada uma com log, dry-run funciona, learning grava no Akasha.

---

### FASE C — GOVERNANÇA REAL (Semana 2)
> Guardrails interceptam em runtime, não só em YAML.

| Wave | Entrega | Arquivo |
|---|---|---|
| W-C1 | `ApprovalGate` runtime — dry → mostra pacote → input humano → executa | `src/governance/approval_gate.py` |
| W-C2 | `RiskClassifier` — pontua ação (0–10) antes de executar | `src/governance/risk_classifier.py` |
| W-C3 | `GuardrailsEnforcer` — intercepta em task_dispatcher baseado em score | `src/governance/enforcer.py` |
| W-C4 | `AutonomySupervisor` — controla nível N0→N7 por missão | `src/autonomy/supervisor.py` |
| W-C5 | Approval log — `07_approval/approval_status.json` por missão | via approval gate |

**Gate:** Ação de risco≥7 para execução e mostra `approval_request.md`. Lucas confirma. Sistema executa.

---

### FASE D — SQUADS ESPECIALIZADOS (Semana 2–3)
> Missões complexas ganham equipes com papéis definidos.

| Wave | Entrega | Squad |
|---|---|---|
| W-D1 | Marketing Squad wired | Content + Caption + Calendar + Publisher |
| W-D2 | Sales Squad wired | Lead Qualifier + DM Sequence + CRM Pipeline |
| W-D3 | App Factory Squad wired | PRD + Schema + API + Tests |
| W-D4 | Computer Ops Squad wired | Disk Audit + Health Check + Quarantine |
| W-D5 | `squad_selector.py` — escolhe squad pelo setor detectado | `src/agentic/squad_selector.py` |

**Gate:** `omnis mission "campanha 30 dias hotel nordeste"` → monta Marketing Squad, executa, entrega `06_exports/calendario_30_dias.csv` + 30 legendas.

---

### FASE E — CAPABILITY FORGE ATIVA (Semana 3)
> OMNIS detecta gap e cria skill nova com teste e registro.

| Wave | Entrega | Arquivo |
|---|---|---|
| W-E1 | `GapDetector` wired no fluxo — detecta skill ausente antes de executar | `src/capability_gap/` wired |
| W-E2 | `ForgeOrchestrator` — gap → spec → build → sandbox → avaliar → registrar | `src/capability_forge_real/` wired |
| W-E3 | Skill aprovada vai para `omnis-control/skills/` automaticamente | `registry_manager.py` |
| W-E4 | `SkillVersioning` — rollback de skill quebrada | `src/capability_forge_real/` |

**Gate:** Missão pede skill inexistente → Forge cria → testa no sandbox → skill disponível na próxima missão.

---

### FASE F — COCKPIT LOCAL (Semana 3–4, paralelo)
> Painel HTML local. Sem backend externo. Arquivo estático.

| Wave | Entrega | Arquivo |
|---|---|---|
| W-F1 | `missions_index.html` — lista missões + status + links | `cockpit/index.html` |
| W-F2 | `mission_viewer.html` — abre qualquer `missions/<id>/` | `cockpit/mission.html` |
| W-F3 | `approvals_panel.html` — mostra `07_approval/approval_request.md` pendentes | `cockpit/approvals.html` |
| W-F4 | `outputs_viewer.html` — lista `05_outputs/` e `06_exports/` | `cockpit/outputs.html` |
| W-F5 | `cockpit_generator.py` — re-gera HTML a cada missão encerrada | `src/reports/cockpit_generator.py` |

**Gate:** `omnis cockpit` abre navegador com missões, aprovações e outputs sem servidor.

---

## PADRÃO UNIVERSAL POR SETOR

```
[Setor] Registry → Queue → Draft → Approval → Bridge → Execute → Metrics → Learning
```

| Setor | Registry | Execute | Export |
|---|---|---|---|
| Marketing | asset_inbox | generate_seogram_caption | export_content_batch_to_csv |
| Sales | lead_pipeline | create_sales_dm_sequence | proposta_comercial.md |
| App Factory | mission_builder | app_factory_supreme | deploy_report.md |
| Automation | workflow/ | automation/ | n8n_execution_log.json |
| Computer Ops | computer_ops | disk_audit | quarantine_plan.md |
| Finance | finance/ | revenue-tracker | pricing_model.csv |

---

## SKILLS PRIORITÁRIAS PARA O ROADMAP

### Tier 1 — Usar direto (já funcionam)
1. **`jarvis-router`** — classifica intenção + setor (Agente 2)
2. **`jarvis-brain`** — busca contexto multi-fonte (Agente 3)
3. **`jarvis-delegate`** — roteia para skill certa (Agente 12 parcial)
4. **`jarvis-guardrails`** — bloqueia ações perigosas (Agente 23)
5. **`jarvis-decide`** — decision gate (Agente 24 parcial)
6. **`jarvis-memory-write`** — grava no Akasha (Agente 28 parcial)
7. **`skill-creator`** — cria nova skill (Agente 10 interface)

### Tier 2 — Wired nos executores de setor
8. **`generate_seogram_caption`** → Publisher Agent (Marketing Squad)
9. **`create_30_day_content_calendar`** → Mission Planner (Marketing)
10. **`create_sales_dm_sequence`** → Sales Agent
11. **`create_instagram_carousel`** → Publisher Agent
12. **`export_content_batch_to_csv`** → Deliverable Mapper
13. **`argos-bridge`** → Publisher Execution Bridge
14. **`revenue-tracker`** → Finance Agent + Metrics
15. **`crm-pipeline`** → Sales Agent CRM
16. **`video_to_content`** → Video Studio Executor

### Tier 3 — Criar junto ao roadmap
17. **`mission-intake`** — extrai missão do texto livre → Fase A
18. **`deliverable-mapper`** — define output exato → Fase A
19. **`learning-writer`** — grava aprendizados → Fase B
20. **`approval-gate-runtime`** — gate interativo → Fase C
21. **`squad-selector`** — monta squad por setor → Fase D
22. **`gap-to-forge`** — detecta gap + aciona forja → Fase E

---

## MÉTRICAS DE SUCESSO (por fase)

| Fase | Métrica de conclusão |
|---|---|
| A | `omnis mission "X"` cria pasta + contrato + relatorio_final |
| B | 3 skills executam com log JSONL + dry-run + learning no Akasha |
| C | Ação de risco≥7 trava e aguarda input humano |
| D | Campanha 30 dias gera 06_exports/ com CSV + 30 legendas |
| E | Skill inexistente → Forge cria → registra → disponível |
| F | Cockpit HTML mostra missões + aprovações sem servidor |

---

## ORDEM DE EXECUÇÃO (próximas waves)

```
W-A1 → W-A2 → W-A3 → W-A4 → W-A5   ← Mission Engine completo
         ↓ (paralelo)
W-B1 → W-B2 → W-B3 → W-B4 → W-B5   ← Execução rastreada
         ↓
W-C1 → W-C2 → W-C3 → W-C4 → W-C5   ← Governança real
         ↓ (paralelo com C)
W-F1 → W-F2 → W-F3 → W-F4 → W-F5   ← Cockpit local
         ↓
W-D1 → W-D2 → W-D3 → W-D4 → W-D5   ← Squads
         ↓
W-E1 → W-E2 → W-E3 → W-E4           ← Forge ativa
```

**Primeira wave para executar agora:** `W-A1` — `MissionEngine`.
