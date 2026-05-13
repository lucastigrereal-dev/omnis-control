# P19 Campaign Manager — Architecture

**Status:** RESUBMITTED (corrigido conforme ONDA6_ARCHITECTURE_REVIEW)
**Date:** 2026-05-13
**Wave:** Onda 6+ (depende de P5, P8, P13)
**Autor:** Lucas Tigre via Claude Code
**Dependências upstream:** P5 (Marketing Supreme), P8 (Publisher / ARGOS Export), P13 (Analytics)
**Módulos downstream:** P20 (OMNIS Supreme)

---

## 1. Definicao da P19

A P19 Campaign Manager e o **motor de coordenacao de campanhas** do OMNIS. Ela transforma uma intencao comercial ou estrategica — tipicamente originada de um Brief de marketing do P5 — em uma **campanha estruturada, sequenciavel, rastreavel e auditavel**.

A P19 NAO produz assets, NAO publica, NAO entrega ao cliente. Ela e o **plano-mestre** que conecta marketing, publicacao e metrica sob um unico contrato de campanha.

### Metafora

Se o OMNIS e uma fabrica:
- P5 (Marketing) define **o que** produzir e **para quem**
- P8 (Publisher / ARGOS) **publica** nos canais
- P13 (Analytics) **mede** os resultados
- **P19 (Campaign Manager) e o gerente de producao** — coordena quem faz o que, em qual ordem, com qual deadline

---

## 2. Problema que Resolve

### Status quo (sem P19)
- Briefs de marketing (P5) existem soltos, sem amarracao com execucao real
- Deals fechados viram tarefas manuais no WhatsApp do Tigrao
- Ninguem sabe se uma campanha de 5 posts esta no post 2 ou no post 4
- Metricas de campanha sao calculadas no olho, semanas depois
- Cliente pergunta "cade meus posts?" e nao ha resposta estruturada

### Com P19
- Toda campanha tem **contrato explicito** (goals, canais, prazos, budget, ROI)
- Estado da campanha e **queryable a qualquer momento**
- Metricas basicas sao **planejadas no start** e populadas via P13
- Orquestracao centralizada de budget e ROI tracking

---

## 3. O Que Entra no Modulo

| Entrada | Origem | Descricao |
|---|---|---|
| `CampaignBrief` | P5 (`src/marketing/models.py`) | Brief de marketing com objetivo, audiencia, audience, tom |
| `CampaignPackage` | P5 (`src/marketing/models.py`) | Pacote de campanha com brief + plano de conteudo |
| `MetricDefinition` | P13 (`src/analytics/models.py`) | Definicao de metricas a serem coletadas |
| `MetricSummary` | P13 (`src/analytics/models.py`) | Sumario estatistico de metricas |
| `PublisherHandoff` | P8 (`src/publisher_argos/models.py`) | Handoff de publicacao (campanha publicada) |

### O que dispara uma campanha:
1. **Brief de marketing** no P5 → `CampaignOrchestrator.orchestrate_campaign(brief)`
2. **Comando manual** → entrada direta de parametros de campanha

---

## 4. O Que Sai do Modulo

| Saida | Destino | Descricao |
|---|---|---|
| `Campaign` | Memoria (in-memory) + `exports/campaigns/<id>/campaign_manifest.json` | Campanha orquestrada completa |
| `CampaignManifest` | `exports/campaigns/<campaign_id>/` | Manifesto JSON generico (contrato + budget + ROI + status) |
| `PublishQueuePlan` | P8 (`src/publisher_argos/`) | Plano de fila de publicacao derivado da campanha |

---

## 5. O Que NAO Pertence ao Modulo

| Nao pertence | Motivo |
|---|---|
| Gerar assets criativos brutos | Pertence a P2 — P19 nao depende de P2 |
| Redigir ou aprovar legendas | Pertence a P3 — P19 nao depende de P3 |
| Publicar no Instagram/ARGOS | Pertence a P8 — P19 gera plano, nao publica |
| Entregar assets ao cliente | Pertence a P17 — P19 nao conhece P17 |
| Calcular metricas complexas | Pertence a P13 — P19 planeja, nao calcula |
| Dashboard visual | Pertence a P20 — P19 expoe dados, nao renderiza |
| OAuth / autenticacao real | P19 e dry-run, nao autentica |
| Criar leads/deals | P19 nao depende de P10 |
| ZIP / Bundle / Export fisico | Feature phase, nao skeleton |

---

## 6. Campaign Core Model

```json
{
  "campaign_id": "cmp_a1b2c3d4",
  "campaign_name": "Hotel Villa do Sol — Collab Maio 2026",
  "brief_ref": "cmp_abc12300",
  "status": "planned",
  "channels": [
    {"profile": "lucastigrereal", "role": "primary_authority", "slot_count": 2},
    {"profile": "afamiliatigrereal", "role": "family_support", "slot_count": 1}
  ],
  "budget": {
    "budget_id": "bud_cmp_a1b2c3d4",
    "total_budget_brl": 350.00,
    "allocated_brl": 350.00,
    "spent_brl": 0.00,
    "currency": "BRL"
  },
  "roi": {
    "roi_id": "roi_cmp_a1b2c3d4",
    "projected_revenue_brl": 350.00,
    "projected_cost_brl": 0.00,
    "projected_roi_percent": null,
    "actual_revenue_brl": null,
    "actual_cost_brl": null,
    "actual_roi_percent": null,
    "calculated_at": null
  },
  "metrics_plan": {
    "target_metrics": [
      {"metric_name": "total_likes", "target_min": 500, "unit": "count"},
      {"metric_name": "total_comments", "target_min": 50, "unit": "count"},
      {"metric_name": "total_saves", "target_min": 200, "unit": "count"}
    ]
  },
  "timeline": {
    "created_at": "2026-05-13T10:00:00Z",
    "deadline": "2026-05-20T23:59:59Z",
    "started_at": null,
    "completed_at": null,
    "analyzed_at": null,
    "archived_at": null
  },
  "publish_queue_plan_ref": null,
  "dry_run": true,
  "approval_required": true,
  "tags": ["hotel", "collab", "maio-2026", "rn"]
}
```

### ID Prefix Convention (reduzida ao necessario)
| Entidade | Prefixo |
|---|---|
| Campaign | `cmp_` |
| BudgetTracker | `bud_` |
| ROICalculation | `roi_` |

---

## 7. Budget Tracker Model

```json
{
  "budget_id": "bud_cmp_a1b2c3d4",
  "campaign_ref": "cmp_a1b2c3d4",
  "total_budget_brl": 990.00,
  "allocated_brl": 990.00,
  "spent_brl": 0.00,
  "breakdown": [
    {"category": "collab_posts", "allocated_brl": 600.00, "spent_brl": 0.00, "notes": "3 collabs @ R$200 cada"},
    {"category": "stories", "allocated_brl": 300.00, "spent_brl": 0.00, "notes": "3 stories @ R$100 cada"},
    {"category": "boosting", "allocated_brl": 90.00, "spent_brl": 0.00, "notes": "reserva para impulsionamento organico"}
  ],
  "currency": "BRL",
  "created_at": "2026-05-13T10:00:00Z",
  "updated_at": "2026-05-13T10:00:00Z"
}
```

---

## 8. ROI Calculation Model

```json
{
  "roi_id": "roi_cmp_a1b2c3d4",
  "campaign_ref": "cmp_a1b2c3d4",
  "projected_revenue_brl": 990.00,
  "projected_cost_brl": 0.00,
  "projected_roi_percent": null,
  "actual_revenue_brl": null,
  "actual_cost_brl": null,
  "actual_roi_percent": null,
  "calculated_at": null,
  "formula": "(revenue - cost) / cost * 100",
  "notes": "ROI calculado apos conclusao da campanha + coleta de metricas"
}
```

---

## 9. Campaign States

6 estados definidos pela Control Tower. Nenhum outro.

```
  ┌──────────────┐
  │    DRAFT     │  ← campanha criada, nao validada
  └──────┬───────┘
         │ validate()
         ▼
  ┌──────────────┐
  │   PLANNED    │  ← contrato validado, budget alocado, metricas planejadas
  └──────┬───────┘
         │ execute()  [dry_run: false]
         ▼
  ┌──────────────┐
  │ IN_PROGRESS  │  ← campanha em execucao (publish queue enviado ao P8)
  └──────┬───────┘
         │ all stages done
         ▼
  ┌──────────────┐
  │  COMPLETED   │  ← publicacao concluida, aguardando metricas
  └──────┬───────┘
         │ metrics collected via P13
         ▼
  ┌──────────────┐
  │   ANALYZED   │  ← metricas coletadas, ROI calculado
  └──────┬───────┘
         │ archive()
         ▼
  ┌──────────────┐
  │   ARCHIVED   │  ← campanha encerrada
  └──────────────┘
```

### Enum `CampaignStatus`:
| Estado | Descricao |
|---|---|
| `draft` | Contrato criado, validacao pendente |
| `planned` | Validado, budget alocado, pronto para executar |
| `in_progress` | Em execucao (publish queue enviado ao P8) |
| `completed` | Todas as etapas concluidas, aguardando metricas |
| `analyzed` | Metricas recebidas do P13, ROI calculado |
| `archived` | Encerrada (+30 dias ou manual) |

### Notas sobre o que NAO sao estados:
- **dry_run_ok / dry_run_failed** — dry-run e validacao, nao ciclo de vida. Operacao sobre `draft`.
- **paused** — operacao operacional sobre `in_progress`, nao estado.
- **cancelled** — e `archived` com motivo. Atributo `archive_reason`, nao estado.
- **failed** — tratado via retry (atributo `retry_count`), nao estado.
- **exported** — export e acao, nao estado.

---

## 10. Campaign Manifest (Output Contract)

Ao final do planejamento, P19 gera um manifest JSON generico em `exports/campaigns/<campaign_id>/campaign_manifest.json`. Este manifest e auto-contido e podera ser consumido pelo P20 Supreme ou por qualquer outro sistema, sem dependencia de P17.

```json
{
  "manifest_version": "1.0",
  "generated_by": "src/campaign_manager/",
  "campaign": { "campaign_id": "cmp_xxxx", "...": "snapshot completo do Campaign model" },
  "budget": { "budget_id": "bud_xxxx", "...": "snapshot completo do BudgetTracker" },
  "roi": { "roi_id": "roi_xxxx", "...": "snapshot completo do ROICalculation" },
  "status": "planned",
  "checksum": "sha256_xxxx",
  "generated_at": "2026-05-13T10:30:00Z"
}
```

---

## 11. Campaign Graph (Sequenciamento Interno)

P19 constroi um DAG internamente usando algoritmo de Kahn com `collections.deque` (stdlib puro, sem import de `src/execution_graph/`).

Cada no representa um passo da campanha (criacao → aprovacao → publicacao → metrica). As arestas representam dependencias entre passos.

```
  P5 CampaignBrief
        │
        ▼
  ┌─────────────────┐
  │ 1. Validate     │  ← valida brief + contrato
  │    Contract     │
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │ 2. Allocate     │  ← aloca budget por canal
  │    Budget       │
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │ 3. Build        │  ← constroi publish queue plan
  │    PublishQueue │
  │    Plan         │
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │ 4. Handoff → P8 │  ← envia para P8 Publisher ARGOS
  │    Publisher    │
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │ 5. Metrics Plan │  ← configura coleta de metricas
  │    → P13        │
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │ 6. ROI Calc     │  ← calcula ROI apos metricas
  │    (analyzed)   │
  └─────────────────┘
```

### Implementacao:
- Ordenacao topologica: `collections.deque`, zero imports externos
- Deteccao de ciclos: inline, raise `CampaignError` se detectado
- Sem dependencia de `src/execution_graph/` (legado)

---

## 12. Relacao com P5 Marketing Supreme

**Dependencia autorizada.** P19 importa do P5:

| Import | Classe | Uso |
|---|---|---|
| `src/marketing/models.py` | `CampaignBrief` | Input principal — brief com objetivo, audiencia, tom |
| `src/marketing/models.py` | `CampaignPackage` | Pacote completo (brief + plano de conteudo + validacao) |
| `src/marketing/models.py` | `MarketingObjective` | Objetivo mensuravel (awareness, engagement, conversion, retention) |
| `src/marketing/models.py` | `AudienceProfile` | Publico-alvo com demografia |

Contrato: P5 define o que produzir. P19 orquestra como e quando.

---

## 13. Relacao com P8 Publisher / ARGOS

**Dependencia autorizada.** P19 importa do P8:

| Import | Classe | Uso |
|---|---|---|
| `src/publisher_argos/models.py` | `PublisherHandoff` | Handoff pos-publicacao — P19 encapsula, nao redefine |
| `src/publisher_argos/models.py` | `ArgosExportItem` | Item de export ja contem caption + media_url |
| `src/publisher_argos/models.py` | `ArgosExportPackage` | Pacote de export pronto para ARGOS |

P19 NAO cria modelo de handoff proprio. Encapsula `PublisherHandoff` do P8 como referencia (`handoff_ref`).

### Fluxo P19 → P8:
1. `CampaignOrchestrator.orchestrate_campaign(brief)` → planeja campanha
2. `CampaignOrchestrator.build_publish_queue_plan()` → gera `PublishQueuePlan`
3. P8 recebe `PublishQueuePlan` e executa publicacao
4. P8 retorna `PublisherHandoff` — P19 armazena referencia

NAO existe "P8 Lite" vs "P8 Publisher". So existe UM P8: `src/publisher_argos/`.

---

## 14. Relacao com P13 Analytics

**Dependencia autorizada.** P19 importa do P13:

| Import | Classe | Uso |
|---|---|---|
| `src/analytics/models.py` | `MetricDefinition` | Definicao de metricas a serem coletadas |
| `src/analytics/models.py` | `MetricSummary` | Sumario estatistico para calculo de ROI |

P19 planeja metricas no start (quais coletar, targets). Apos `completed`, consome `MetricSummary` do P13 para popular `ROICalculation.actual_*` e transicionar para `analyzed`.

---

## 15. Relacao Futura com P20 Supreme

A P20 (OMNIS Supreme) sera o orquestrador total. A P19 e um dos inputs do Supreme.

### O que a P19 entrega para o Supreme:
- **Campaign Manifest** — JSON auto-contido em `exports/campaigns/<id>/campaign_manifest.json`
- **Budget + ROI** — dados estruturados para dashboard financeiro
- **Audit trail** — todas as transicoes de estado documentadas

### O que o Supreme faz com a P19:
- Dashboard unificado de campanhas ativas
- Cross-campaign analytics (ex: "qual perfil performa melhor em collab de hotel?")
- Ponte para P17 Delivery (Supreme conecta P19 Manifest → P17 DeliveryPackage)

---

## 16. Pastas (Estrutura Alvo — Skeleton)

```
src/campaign_manager/
├── __init__.py    # Public API: CampaignOrchestrator + 3 models + CampaignStatus enum
├── models.py      # 3 dataclasses: Campaign, BudgetTracker, ROICalculation + 1 enum: CampaignStatus
├── service.py     # CampaignOrchestrator (static methods)
└── errors.py      # CampaignError hierarchy (~4 excecoes)

tests/campaign_manager/
├── __init__.py
├── test_models.py      # Instanciacao, .new(), to_dict()/from_dict(), ID prefixes
├── test_service.py     # orchestrate_campaign(), state transitions, budget, ROI
└── test_contracts.py   # Import contracts: P5 + P8 + P13 (mock-based)

docs/architecture/
└── P19_CAMPAIGN_ARCHITECTURE.md   # This document
```

### O que NAO entra no skeleton (feature phase):
- `scheduler.py`, `cta_chain.py`, `dry_run.py`, `graph_builder.py`
- `exporters.py`, `store.py`, `validator.py`
- `observability.py`, `retry.py`, `archiver.py`
- CLI commands (`src/cli_commands/campaign_engine_cmd.py`)

---

## 17. Classes

### 17.1 Models (`models.py` — 3 dataclasses + 1 enum)

| Classe | Prefixo | Campos principais |
|---|---|---|
| `Campaign` | `cmp_` | name, brief_ref, status, channels, budget, roi, metrics_plan, timeline, publish_queue_plan_ref |
| `BudgetTracker` | `bud_` | campaign_ref, total_budget_brl, allocated_brl, spent_brl, breakdown, currency |
| `ROICalculation` | `roi_` | campaign_ref, projected_*, actual_*, formula, calculated_at |

### 17.2 Enum (`models.py`)

| Enum | Valores |
|---|---|
| `CampaignStatus` | `draft`, `planned`, `in_progress`, `completed`, `analyzed`, `archived` |

### 17.3 CampaignOrchestrator (`service.py`)

Nome corrigido: `CampaignOrchestrator` (nao `CampaignPlanner`), reflete o escopo real de orquestracao.

| Metodo (@staticmethod) | Input | Output | Descricao |
|---|---|---|---|
| `orchestrate_campaign()` | `CampaignBrief` | `Campaign` | Pipeline completo: validar → budget → plano → publish queue |
| `allocate_budget()` | `Campaign` + valores | `BudgetTracker` | Aloca budget por categoria/canal |
| `calculate_roi()` | `Campaign` + `MetricSummary` | `ROICalculation` | Calcula ROI projetado e real |
| `transition_state()` | `Campaign` + `CampaignStatus` | `Campaign` | Transicao de estado com validacao |
| `build_publish_queue_plan()` | `Campaign` | `dict` | Gera plano de publicacao para P8 |
| `generate_manifest()` | `Campaign` | `dict` | Gera manifest JSON generico |

---

## 18. Logs e Observabilidade

Logs estruturados internamente via `logging` + JSONL (stdlib). Sem dependencia de P16 (`src/observability_local/`).

### Eventos de log:
```
campaign.created    — campanha instanciada
campaign.validated  — contrato validado
campaign.planned    — budget alocado, plano pronto
campaign.started    — transicao para in_progress
campaign.completed  — publicacao concluida
campaign.analyzed   — metricas recebidas, ROI calculado
campaign.archived   — campanha encerrada
campaign.error      — erro com traceback
```

### Arquivo de log (unico, append-only):
- `logs/campaign_manager.jsonl`

---

## 19. Dry-Run Strategy

- `dry_run: True` por padrao em todo modelo
- Validacao de contrato e budget sao sempre seguras (stdlib)
- Nenhuma operacao toca em OAuth, rede, ou publisher real
- Manifest gerado em `exports/campaigns/<id>/` e a unica saida em disco no skeleton
- Dry-run e uma **validacao**, nao um estado — executado como metodo interno, sem alterar `CampaignStatus`

---

## 20. Failure / Retry Model (simplificado)

- **Retry:** atributo `retry_count` no Campaign (int, default 0). Maximo 3.
- **Backoff:** nao implementado no skeleton (feature phase).
- **Falha total:** apos 3 retries, Campaign permanece no estado atual com `error_message` populado.
- NAO existe estado `failed` — falha e atributo, nao ciclo de vida.

---

## 21. Edge Cases

| # | Edge Case | Comportamento Esperado |
|---|---|---|
| 1 | Brief sem canais definidos | `CampaignError`: "brief must define at least 1 channel" |
| 2 | Budget negativo ou zero | `BudgetError`: "total_budget_brl must be > 0" |
| 3 | Transicao invalida (ex: draft → archived) | `StateTransitionError`: "invalid transition from draft to archived" |
| 4 | MetricSummary vazio ao calcular ROI | `ROIError`: "cannot calculate ROI without metrics" |
| 5 | PublishQueuePlan para P8 com 0 itens | `CampaignError`: "publish queue plan is empty" |
| 6 | Campaign sem deadline | Warning no log, nao bloqueia |
| 7 | Tentativa de reabrir campanha arquivada | `StateTransitionError`: "archived campaigns cannot be reopened" |

---

## 22. Test Strategy

### Alvo: 60-80 testes (skeleton)

| Arquivo de Teste | Foco | Estimativa |
|---|---|---|
| `test_models.py` | `.new()` factory, `to_dict()`/`from_dict()`, ID prefixes (`cmp_`, `bud_`, `roi_`), defaults, CampaignStatus enum | 25 |
| `test_service.py` | `orchestrate_campaign()`, `allocate_budget()`, `calculate_roi()`, `transition_state()`, `build_publish_queue_plan()`, `generate_manifest()` | 20 |
| `test_contracts.py` | Import contracts: garante que so P5+P8+P13 sao importados; mock de `CampaignBrief`, `PublisherHandoff`, `MetricDefinition` | 15 |

### Propriedades testadas:
- **Determinismo:** mesma entrada → mesma saida
- **Round-trip:** `model.to_dict()` → `Model.from_dict(data)` → igualdade
- **State machine:** transicoes validas OK, transicoes invalidas levantam erro
- **Skeleton safety:** zero imports de P2, P3, P10, P17, `execution_graph`, `approval_center`, `campaign_package`, `campaign_auditor`

---

## 23. Criterios de Aceite

- [ ] Pasta `src/campaign_manager/` (nome exato, conforme CT)
- [ ] Models: `Campaign`, `CampaignStatus` (enum 6 estados CT), `BudgetTracker`, `ROICalculation`
- [ ] Service: `CampaignOrchestrator` com `orchestrate_campaign(brief: CampaignBrief) → Campaign`
- [ ] Imports: APENAS `src/marketing/models.py` + `src/publisher_argos/models.py` + `src/analytics/models.py`
- [ ] NAO importa: P2, P3, P10, P14, P17, `campaign_package`, `campaign_auditor`, `execution_graph`, `approval_center`
- [ ] `dry_run: True`, `approval_required: True`
- [ ] IDs prefixo `cmp_`, `bud_`, `roi_`
- [ ] `.new()` + `.to_dict()` + `.from_dict()` + `_now_iso()`
- [ ] Targeted tests: >= 50 passando em `tests/campaign_manager/`
- [ ] `grep -r "campaign_engine" docs/architecture/P19_*.md` retorna VAZIO
- [ ] `grep -r "Execution Graph" docs/architecture/P19_*.md` retorna VAZIO
- [ ] `grep "deps\|dependências\|Dependencies" docs/architecture/P19_*.md` mostra apenas P5 + P8 + P13

---

## 24. Plano Incremental de Implementacao

### P19.0 — Models & Enums Foundation
- Escopo: `src/campaign_manager/models.py` + `src/campaign_manager/errors.py`
- Entregavel: 3 dataclasses + 1 enum + 4 excecoes
- Testes: 25
- Dependencias: zero (stdlib only)

### P19.1 — CampaignOrchestrator Core
- Escopo: `src/campaign_manager/service.py`
- Entregavel: 6 metodos `@staticmethod` no `CampaignOrchestrator`
- Testes: 20
- Dependencias: P19.0 + contratos P5/P8/P13

### P19.2 — Contract Tests + Manifest
- Escopo: `src/campaign_manager/__init__.py` + contract tests
- Entregavel: Public API + validacao de contratos de import + manifest generator
- Testes: 15
- Dependencias: P19.1

### P19.3 — Final Seal
- Escopo: Full suite, smoke tests, docs
- Entregavel: 60-80 testes PASS, 0 regressoes, documentacao completa
- Dependencias: P19.2

---

## Resubmission Notes

### O que foi corrigido:
1. **Namespace:** `campaign_engine` → `campaign_manager` em todo o documento (secoes 1, 16, 17, 19, 23, 24 + titulo)
2. **Dependencias:** removidas P2 e P3. Mantidas apenas P5 + P8 + P13. Secoes 14 (P2) e 15 (P3) removidas por completo
3. **P8:** todas as referencias corrigidas para "P8 Publisher / ARGOS Export" (`src/publisher_argos/`). Removida mencao a "P8 Execution Graph" e distincao "P8 Lite vs Publisher"
4. **P10:** removido como dependencia. P19 nao depende de P10. Secoes de entrada removidas
5. **State machine:** reduzida de 11 estados para exatamente 6: `draft → planned → in_progress → completed → analyzed → archived`
6. **Handoff:** removido contrato P19↔P17. P19 emite CampaignManifest JSON generico para `exports/campaigns/<id>/`. Sem acoplamento com P17
7. **Escopo:** reduzido de 11 arquivos para 4 core (models, service, errors, `__init__`). Removidos: scheduler, cta_chain, dry_run, exporters, store, validator, graph_builder, CLI commands
8. **Testes:** reduzidos de 140 para 60-80. 3 arquivos de teste apenas
9. **Nome do Service:** `CampaignPlanner` → `CampaignOrchestrator` (nome mais honesto para o escopo real)
10. **Topological sort:** esclarecido como implementacao inline com `collections.deque` (stdlib), sem import de `src/execution_graph/`

### O que foi removido:
- Secao 14: "Relacao com P2 Creative Production" (dependencia nao autorizada)
- Secao 15: "Relacao com P3 Caption Approval" (dependencia nao autorizada)
- Secao 17: "Relacao com P17 Delivery" (acoplamento cross-module)
- Secao 21: "CLI Commands Sugeridos" (feature phase, nao skeleton)
- Secoes de arquivos extras: scheduler.py, cta_chain.py, dry_run.py, exporters.py, store.py, validator.py, graph_builder.py, observability.py
- Modelos extras: CampaignContract, CampaignStage, CampaignAsset, Channel, Calendar, CalendarSlot, CTAChain, CampaignRun, CampaignBundle
- Enums extras: StageStatus, AssetType, CTAStrategy, SlotType, CampaignOrigin, ApprovalPolicy, ChannelRole
- Referencias a P2, P3, P10, P17 como dependencias
- Referencias a `approval_center`, `delivery_templates`, `campaign_package`, `campaign_auditor`, `execution_graph`

### Decisoes que aguardam Control Tower:
1. **Contrato P19→P8 confirmado:** `PublishQueuePlan` como estrutura de saida para o Publisher. Schema exato a definir com P8
2. **Contrato P5→P19 confirmado:** `CampaignBrief` + `CampaignPackage` como input. Campos especificos a validar com P5
3. **CampaignManifest schema:** formato generico proposto. Sera o contrato-base para P20 Supreme consumir
4. **P19.1 test count:** 60-80 e o alvo. Ajustar se CT definir numero exato
5. **Onda 6 merge order:** CT definiu P19 → P17. Confirmado que P19 nao precisa esperar P17

---

*OMNIS Control Tower — Documento corrigido conforme ONDA6_ARCHITECTURE_REVIEW.*
*Status: RESUBMITTED. Aguardando nova avaliacao.*
