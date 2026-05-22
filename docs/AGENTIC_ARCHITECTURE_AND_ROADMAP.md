# OMNIS Agentic Layer — Arquitetura & Roadmap

> **Status:** AGUARDANDO APROVAÇÃO DO OPERADOR
> **Data:** 2026-05-22
> **Auditoria base:** 8 módulos, 54 arquivos, 5.278 linhas

---

## 1. Diagnóstico (estado atual)

### 1.1 O que existe

A camada agentica tem 8 módulos com boa arquitetura interna — mas nenhum executa de verdade:

```
Intake(regex) → Engine(dataclass) → Squad(hardcoded) → Dispatch(dict) → Graph(dry) → SkillBridge(mock)
                                                                              ↓
                                                                     ModelRouter(mock)
```

| Módulo | Arquivos | Linhas | O que faz | Modo real? |
|---|---|---|---|---|
| `agentic/` | 8 | 1.193 | Intake, engine, squad, dispatch, forge | ❌ Regex + dicts |
| `execution_graph/` | 15 | 1.976 | DAG builder, retry, rollback, circuit breaker | ❌ `run_graph_dry()` |
| `skills_bridge/` | 5 | ~300 | Skill adapter, selector, dry_run engine | ❌ MockSkillAdapter |
| `skill_router_bridge/` | 6 | ~350 | **DUPLICATA** de skills_bridge | ❌ Mock |
| `multi_model_orchestration/` | 10 | ~500 | Model router, classifier, fallback | ❌ Só mock_adapter |
| `autonomous_execution/` | 9 | ~600 | Executor, checkpoint, recovery, CLI | ❌ dry_run |
| `plugin_runtime/` | 10 | ~700 | MCP bridge, session, tool registry, permissions | ⚠️ Parcial |
| `capabilityforge/` | 7 | ~300 | **TRÊS VARIANTES** concorrentes | ⚠️ Parcial |
| `capability_forge_lite/` | 9 | ~400 | **DUPLICATA** | ⚠️ Parcial |
| `capability_forge_real/` | 10 | ~500 | Forge canônica | ⚠️ Parcial |
| `runtime_orchestrator/` | 3 | ~150 | Pipeline de execução | ❌ dry_run |
| `runners/` | 1 | 128 | Skill runner wrapper | ❌ Mock |

### 1.2 Os 5 gaps críticos

**G1 — Duplicação.** `skills_bridge` vs `skill_router_bridge` (mesma função, nomes diferentes). Três forges (`capabilityforge`, `capability_forge_lite`, `capability_forge_real`) competindo sem canônico declarado.

**G2 — ModelRouter sem adapters reais.** `multi_model_orchestration/adapters/` só tem `mock_adapter.py`. Nenhum adapter para OpenAI, Anthropic, ou Ollama. Toda chamada retorna `"[MOCK] Simulated response..."`.

**G3 — ExecutionGraph só simula.** `runner.py` é `run_graph_dry()`. Constrói DAGs com retry, rollback, circuit breaker — mas nunca executa um passo real.

**G4 — Skills hardcoded.** `skills_bridge/selection.py` define `MOCK_SKILLS` como lista fixa de 7 skills. Sem descoberta dinâmica, sem integração com registry, sem invocação real.

**G5 — Módulos não conversam.** Nenhum módulo chama o próximo na cadeia. ExecutionGraph não chama SkillBridge. SkillBridge não chama skills reais. ModelRouter não é usado por nenhum outro módulo. Plugin/MCP Runtime está isolado.

---

## 2. Arquitetura-alvo

### 2.1 Diagrama de integração

```
                          ┌─────────────────────┐
                          │   OMNIS_DRY_RUN env  │
                          │   (global override)  │
                          └──────────┬──────────┘
                                     │
  ┌──────────┐    ┌──────────┐    ┌──┴───────────┐    ┌──────────────┐
  │ Intake   │───→│ Engine   │───→│ SquadSelector │───→│ Dispatcher   │
  │ (regex)  │    │ (contr.) │    │ (5 squads)    │    │ (sector→exec)│
  └──────────┘    └──────────┘    └───────────────┘    └──────┬───────┘
                                                               │
                         ┌─────────────────────────────────────┘
                         ▼
  ┌──────────────────────────────────────────────────────────────────┐
  │                    EXECUTION GRAPH (canônico)                     │
  │  builder.py  runner.py  retry.py  rollback.py  circuit_breaker.py│
  │  ┌─────────────────────────────────────────────────────────────┐ │
  │  │ run_graph(real=True) → executa passos em ordem topológica   │ │
  │  │ Cada passo chama SkillBridge com dry_run=resolve_dry_run()  │ │
  │  └─────────────────────────────────────────────────────────────┘ │
  └──────────────────────────────┬───────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
  ┌─────────────────────────┐    ┌─────────────────────────┐
  │     SKILLS BRIDGE       │    │    MODEL ROUTER         │
  │  (canônico, unificado)  │    │  (multi-model orch)     │
  │                         │    │                         │
  │  SkillSelector           │    │  ┌───────────────────┐  │
  │  ┌─────────────────────┐ │    │  │ OpenAI adapter    │  │
  │  │ Descoberta dinâmica │ │    │  │ (GPT-4o/GPT-4.1) │  │
  │  │ via .claude/skills/ │ │    │  └───────────────────┘  │
  │  │ + registry YAML     │ │    │  ┌───────────────────┐  │
  │  └─────────────────────┘ │    │  │ Anthropic adapter │  │
  │  DryRunEngine             │    │  │ (Opus/Sonnet)     │  │
  │  ┌─────────────────────┐ │    │  └───────────────────┘  │
  │  │ Resolve via         │ │    │  ┌───────────────────┐  │
  │  │ resolve_dry_run()   │ │    │  │ Ollama adapter    │  │
  │  └─────────────────────┘ │    │  │ (local, fallback) │  │
  └─────────────────────────┘    │  └───────────────────┘  │
                                 └─────────────────────────┘
```

### 2.2 Princípios de design

1. **Um canônico, zero duplicata.** Cada função tem exatamente UM módulo. Duplicatas são arquivadas.
2. **Resolver, não hardcodar.** Skills são descobertas do filesystem + registry, não de lista fixa.
3. **Adapter pattern real.** ModelRouter tem adapters reais (OpenAI, Anthropic, Ollama) com fallback.
4. **dry_run no entry point.** Toda execução passa por `resolve_dry_run()`. Sem `dry_run=True` hardcoded nos construtores dos módulos canônicos.
5. **Execution Graph é o hub central.** Toda missão vira um DAG. Cada nó do DAG chama SkillBridge. SkillBridge chama skills reais ou ModelRouter.

### 2.3 Consolidação (o que some, o que fica)

| Módulo | Decisão | Justificativa |
|---|---|---|
| `skills_bridge/` | **CANÔNICO** | Agentic já importa dele |
| `skill_router_bridge/` | **ARQUIVAR** | Duplicata. Mover para `_archived/` |
| `capability_forge_real/` | **CANÔNICO** | Mais completo (builder, scaffold, test_gen, sandbox) |
| `capability_forge_lite/` | **ARQUIVAR** | Subset do `_real` |
| `capabilityforge/` | **ARQUIVAR** | Versão antiga, superseded pelo `_real` |
| `execution_graph/` | **CANÔNICO** | Módulo mais maduro. Precisa de runner real |
| `multi_model_orchestration/` | **CANÔNICO** | Precisa de adapters reais |
| `agentic/` | **CANÔNICO** | Precisa de integração vertical |
| `plugin_runtime/` | **CANÔNICO** | Conectar ao SkillBridge para MCP tools |
| `autonomous_execution/` | **CANÔNICO** | Conectar ao ExecutionGraph |
| `runtime_orchestrator/` | **CANÔNICO** | Já atualizado com resolve_dry_run() |
| `runners/` | **CANÔNICO** | Embrulho fino, manter |

---

## 3. Roadmap

### Fase 1 — Consolidação (30 min)
**Objetivo:** Um canônico por função. Zero duplicata.

| Passo | Ação | Risco |
|---|---|---|
| 1.1 | Mover `skill_router_bridge/` → `_archived/skill_router_bridge/` | Baixo — nada importa dele |
| 1.2 | Mover `capability_forge_lite/` → `_archived/capability_forge_lite/` | Baixo — `_real` cobre |
| 1.3 | Mover `capabilityforge/` → `_archived/capabilityforge/` | Baixo — `_real` cobre |
| 1.4 | Atualizar imports quebrados (se houver) | Médio — verificar antes |
| 1.5 | Rodar suite completa (8.649 testes) | Zero — só arquivamento |

**Gate:** Suite verde. Zero imports quebrados.

---

### Fase 2 — Adapters reais no ModelRouter (60 min)
**Objetivo:** ModelRouter chama LLMs reais, não mock.

| Passo | Ação | Risco |
|---|---|---|
| 2.1 | Criar `multi_model_orchestration/adapters/openai_adapter.py` | Baixo — adapter isolado |
| 2.2 | Criar `multi_model_orchestration/adapters/anthropic_adapter.py` | Baixo — adapter isolado |
| 2.3 | Registrar no `ADAPTER_REGISTRY` | Baixo |
| 2.4 | Testar cada adapter isoladamente | Baixo |
| 2.5 | ModelRouter usa adapter real por padrão com fallback mock | Médio — mudança de comportamento |

**Gate:** Cada adapter responde com resposta real. Fallback mock funciona se API offline.

---

### Fase 3 — Primeiro caminho vertical E2E (90 min)
**Objetivo:** UMA missão real ponta a ponta: "cria legenda para @lucastigrereal sobre viagem em Natal"

| Passo | Ação | Risco |
|---|---|---|
| 3.1 | `skills_bridge/selection.py`: substituir MOCK_SKILLS por descoberta dinâmica do registry + filesystem | Médio |
| 3.2 | `execution_graph/runner.py`: criar `run_graph_real()` que chama SkillBridge em vez de simular | Médio |
| 3.3 | `agentic/skill_runner_bridge.py`: trocar MockSkillAdapter por SkillAdapter real quando `OMNIS_DRY_RUN=false` | Médio |
| 3.4 | Criar 1 skill real de baixo risco: `generate_seogram_caption` (já existe como mock) | Baixo |
| 3.5 | Teste E2E: `Intake → Engine → Squad → Dispatcher → Graph → SkillBridge → ModelRouter(OpenRouter) → output real` | — |

**Gate:** Uma missão de criação de legenda executada do início ao fim, com output real em arquivo.

---

### Fase 4 — Skill discovery dinâmico (45 min)
**Objetivo:** SkillBridge descobre skills do ecossistema real (`.claude/skills/`, registry YAML, MCP tools).

| Passo | Ação | Risco |
|---|---|---|
| 4.1 | SkillSelector lê `~/.claude/registry/skills.yaml` | Baixo |
| 4.2 | SkillSelector escaneia `~/.claude/skills/` por SKILL.md | Baixo |
| 4.3 | SkillSelector consulta MCP tools via `plugin_runtime/mcp_tool_registry.py` | Baixo |
| 4.4 | Unificar em `SkillCatalog` com cache em memória | Médio |

**Gate:** `SkillSelector.select()` retorna skills reais do teu ecossistema, não mock.

---

### Fase 5 — Execution Graph real (60 min)
**Objetivo:** Toda missão complexa vira DAG com execução real.

| Passo | Ação | Risco |
|---|---|---|
| 5.1 | `run_graph_real()` usa retry/circuit_breaker/rollback reais | Médio |
| 5.2 | Cada StepNode tem `dry_run` herdado do grafo | Baixo |
| 5.3 | Integrar com `autonomous_execution/executor.py` para execução autônoma com checkpoint | Alto |
| 5.4 | Conectar `plugin_runtime/mcp_bridge.py` para steps que usam MCP tools | Médio |

**Gate:** Missão multi-step (ex: carrossel completo) executada como DAG com retry real.

---

### Fase 6 — Squads + Forge integrados (60 min)
**Objetivo:** Squads usam skills reais. Forge cria skills novas sob demanda.

| Passo | Ação | Risco |
|---|---|---|
| 6.1 | SquadSelector.resolve() consulta `SkillCatalog` para validar members | Baixo |
| 6.2 | ForgeOrchestrator detecta gap → chama `capability_forge_real` → scaffold → registra → Squad usa | Alto |
| 6.3 | Testar ciclo completo: missão com gap → forge cria skill → missão reexecuta com sucesso | Alto |

**Gate:** Ciclo de self-improvement fechado.

---

## 4. O primeiro vertical slice (Fase 3 em detalhe)

### 4.1 O que vai acontecer

Usando `OMNIS_DRY_RUN=false`, uma missão real:

```
Input: "cria uma legenda Instagram para @lucastigrereal sobre viagem em família em Natal"
```

```
1. MissionIntake.parse()
   → setor=marketing, tipo=content, objetivo="criar legenda", account=@lucastigrereal

2. MissionEngine.create()
   → mission_id=MISS-20260522-001, pasta em missions/

3. SquadSelector.assign(mission_id, sector="marketing")
   → SQD-MKT (Content Strategist + Caption Writer + Carousel Designer + Publisher Bridge)

4. TaskDispatcher.dispatch(mission)
   → 2 tasks: [generate_caption, review_caption]
   → executor: "publisher" (via SECTOR_EXECUTOR)

5. ExecutionGraph.build(squad_plan, task_plan)
   → DAG: generate_caption → review_caption (2 nós, 1 dependência)

6. run_graph_real(graph, dry_run=False)
   → Step 1: generate_caption
     → SkillBridge.call_skill("generate_seogram_caption", ...)
       → SkillSelector.select("generate_seogram_caption")
         → Encontra skill no registry
       → SkillAdapter.call_skill()  [dry_run=False]
         → ModelRouter.select_model(task="caption_generation")
           → OpenAI adapter → GPT-4o mini (rapido, barato)
           → Retorna: legenda SEO + hashtags + CTA
     → output escrito em missions/MISS-20260522-001/05_outputs/caption.md

   → Step 2: review_caption
     → SkillBridge.call_skill("review_caption", caption=output_do_step1)
     → ModelRouter → Anthropic adapter → Claude Haiku (revisor rapido)
     → output: caption_review.md com score + sugestões

7. Relatório final em missions/MISS-20260522-001/08_logs/run_report.md
```

### 4.2 Arquivos que serão criados/modificados

| Arquivo | Ação |
|---|---|
| `src/multi_model_orchestration/adapters/openai_adapter.py` | NOVO — Adapter OpenAI real |
| `src/multi_model_orchestration/adapters/anthropic_adapter.py` | NOVO — Adapter Anthropic real |
| `src/skills_bridge/skill_catalog.py` | NOVO — Descoberta dinâmica |
| `src/execution_graph/runner_real.py` | NOVO — Runner real |
| `src/agentic/skill_runner_bridge.py` | EDIT — Trocar MockSkillAdapter → SkillAdapter |
| `src/skills_bridge/adapter.py` | EDIT — Adicionar SkillAdapter real |
| `src/skills_bridge/selection.py` | EDIT — Substituir MOCK_SKILLS por SkillCatalog |

### 4.3 O que NÃO será tocado

- `sales_crm/`, `sales/`, `commercial_sdr/`, `publisher/`, `argos_bridge/` — L3+, congelado
- `real_world_actions/` — publicar/postar/mandar DM — risco alto, congelado
- `kratos-mission-control/` — proibido pelo CLAUDE.md

---

## 5. Governança

### 5.1 Regras de execução

1. **OMNIS_DRY_RUN=false** só afeta L0-L2 (agentic, execution_graph, skills_bridge, model_router, memory_intel)
2. **L3+ permanece dry_run** independente do env var (sales, publisher, real_world_actions)
3. **Nenhuma API externa sem adapter com health check** — se OpenAI/Anthropic falharem, fallback Ollama → mock
4. **Todo output real vai pra `missions/<id>/05_outputs/`** — nunca sobrescrever arquivos de sistema
5. **Toda missão real gera log em `missions/<id>/08_logs/`** — auditável, replayable

### 5.2 Critérios de sucesso por fase

| Fase | Critério |
|---|---|
| 1 | Suite 8.649 testes verde. Zero imports quebrados. |
| 2 | OpenAI + Anthropic adapters retornam resposta real. Fallback Ollama → mock funcional. |
| 3 | Missão "criar legenda" executada E2E com output real em arquivo. |
| 4 | SkillSelector descobre skills do `~/.claude/skills/` + registry YAML. |
| 5 | Missão multi-step executada como DAG com retry. |
| 6 | Gap detection → forge → nova skill → missão reexecutada com sucesso. |

---

## 6. Aprovação

**Operador, validar:**
- [ ] Arquitetura-alvo (seção 2) — a direção está certa?
- [ ] Consolidação (seção 2.3) — pode arquivar as 3 duplicatas?
- [ ] Roadmap (seção 3) — a ordem das fases está certa?
- [ ] Vertical slice (seção 4) — o primeiro caminho E2E é esse mesmo?
- [ ] Governança (seção 5) — as regras de segurança estão corretas?

**Após aprovação:** executo Fase 1 (consolidação) primeiro, paro para validação, depois Fase 2, etc.
