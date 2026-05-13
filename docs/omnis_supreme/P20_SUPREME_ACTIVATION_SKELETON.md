# P20 — OMNIS SUPREME ACTIVATION SKELETON

> **Data:** 2026-05-13
> **Status:** SKELETON COMPLETE — M1-M5 concluídos
> **Branch:** parallel/p20-omnis-supreme
> **Base:** master `de22369` (3941 testes baseline)

---

## 1. Visao Geral

P20 OMNIS Supreme Activation e a camada de orquestracao fina que conecta 20 modulos isolados em fluxos de execucao por missao. Nao e um modulo de dominio — e um condutor de orquestra.

```
User Request → Supreme Intake → Supreme Context → Supreme Plan
→ Dry Run → Approval Gate → Execute → Delivery → Report
```

## 2. Arquitetura

### 2.1. Source Files (8)

| Arquivo | Linhas | Responsabilidade |
|---|---|---|
| `__init__.py` | 56 | Exports publicos |
| `models.py` | 320 | SupremeMission, SupremePlan, SupremeStep, SupremeStatus, MissionReport |
| `errors.py` | 30 | 7 erros hierarquicos (SupremeError base + 6 filhos) |
| `adapters.py` | 60 | ADAPTER_REGISTRY com 8 lambda bridges |
| `service.py` | 286 | SupremeIntake, SupremeContextBuilder, SupremePlanner, SupremeExecutor, SupremeOrchestrator |
| `tracer.py` | 42 | ObservabilityTracer + Span (wrapper P16) |
| `approval_gate.py` | 55 | SupremeApprovalGate (2 gates via P18) |
| `reporter.py` | 72 | SupremeReporter (MissionReport + learnings) |

### 2.2. Test Files (5)

| Arquivo | Testes |
|---|---|
| `test_models.py` | 61 |
| `test_service.py` | 46 |
| `test_adapters.py` | 23 |
| `test_e2e_supreme.py` | 24 |
| `test_approval_gate.py` | 23 |
| **Total** | **177** |

### 2.3. SupremeStatus (9 estados)

```
INTAKE → CONTEXT_BUILDING → PLANNING → DRY_RUN
→ AWAITING_APPROVAL → EXECUTING → COMPLETED
Desvios: FAILED (→ PLANNING), CANCELLED (terminal)
```

Transicoes validadas via `VALID_SUPREME_TRANSITIONS` dict.

### 2.4. ADAPTER_REGISTRY (8 bridges)

| Key | Bridge |
|---|---|
| `("P5", "build_campaign_brief")` | MarketingPlanner → CampaignBrief |
| `("P19", "orchestrate_campaign")` | CampaignOrchestrator → Campaign |
| `("P19", "allocate_budget")` | CampaignOrchestrator → BudgetTracker |
| `("P19", "calculate_roi")` | CampaignOrchestrator → ROICalculation |
| `("P19", "build_publish_queue_plan")` | CampaignOrchestrator → dict |
| `("P8", "validate_publish_readiness")` | PublisherArgosPlanner → PublishReadinessCheck |
| `("P17", "build_delivery_package")` | DeliveryPlanner → DeliveryPackage |
| `("P19", "generate_manifest")` | CampaignOrchestrator → dict |

Cada adapter e um lambda `(config, context) → dict` com ≤ 3 linhas de logica.

## 3. Fluxo Completo

### 3.1. SupremeOrchestrator.run()

```
1. SupremeIntake.parse(request) → SupremeMission
2. SupremeContextBuilder.build(intent) → context dict
3. SupremePlanner.plan(mission) → SupremePlan
4. SupremeExecutor.dry_run(plan) → simulated execution
5. [If !dry_run] SupremeExecutor.execute(plan) → ExecutionResult
```

### 3.2. INTENT_PATTERNS (5 intents)

| Intent | Keywords |
|---|---|
| `create_campaign` | campanha, campaign, briefing, marketing |
| `publish_content` | publicar, postar, conteudo, publish, post |
| `deliver_to_client` | entregar, cliente, delivery, entrega |
| `analyze_performance` | analisar, metricas, relatorio, performance, analytics |
| `commercial_outreach` | comercial, prospeccao, vender, prospect, lead, sdr |

### 3.3. INTENT_TO_PIPELINE

Cada intent mapeia para uma sequencia de `(module_ref, operation)` steps.

## 4. Padroes Obrigatorios

| Padrao | Status |
|---|---|
| `dry_run: bool = True` | OK — SupremeMission, SupremePlan, SupremeExecutor |
| `approval_required: bool = True` | OK — SupremeMission |
| `.new()` classmethod | OK — 4 modelos + ExecutionResult |
| `.to_dict()` | OK — 4 modelos + ExecutionResult + Span/Snapshot |
| `.from_dict()` | OK — 4 modelos |
| `_now_iso()` helper | OK — UTC ISO 8601 |
| `_new_id(prefix)` helper | OK — uuid4 hex[:8] |
| IDs: `spr_`, `plan_`, `step_`, `rpt_` | OK — 4 prefixos |

## 5. Restricoes

### 5.1. Imports Autorizados (apenas estes)

- `src.mission.models`
- `src.marketing.models`, `src.marketing.service`
- `src.publisher_argos.models`, `src.publisher_argos.planner`
- `src.delivery_portal.models`, `src.delivery_portal.service`
- `src.campaign_manager.models`, `src.campaign_manager.service`
- `src.governance.models`, `src.governance.service`
- `src.observability_local.models`
- `src.memory_pack.models`
- `src.analytics.service`

### 5.2. Imports Proibidos (NUNCA)

`creative_production_v2`, `caption_approval_v2`, `sales_crm`, `finance`, `computer_ops`, `capabilityforge`, `capability_forge_lite`, `client_delivery`, `delivery_templates`, `approval_center`, `execution_graph`, `content_scheduler`, `commercial_sdr`, `app_factory`, `automation`, `design_art`, `video_studio`

### 5.3. Design Constraints

- < 500 linhas de logica propria (~180 linhas efetivas)
- Zero toques em modulos existentes fora de `src/omnis_supreme/` e `tests/omnis_supreme/`
- Adapters ≤ 3 linhas, sem logica de negocio
- dry_run=True default em todas as classes
- approval_required=True default inegociavel

## 6. Milestones

| M | Descricao | Testes |
|---|---|---|
| M1 | Core Models + Errors | 61 |
| M2 | Service Layer + Adapters | 46 |
| M3 | Executor + Tracing + E2E | 47 |
| M4 | Approval Gate + Reporter | 23 |
| M5 | Integration + Docs + Suite | — |
| **Total** | | **177** |

## 7. Proximo Passos (pos-skeleton)

1. Integrar SupremeOrchestrator com interface real (CLI/API)
2. Substituir adapters stub por chamadas reais de modulos (pos-OAuth)
3. Adicionar politicas de approval baseadas em thresholds reais de budget/risco
4. Expandir INTENT_PATTERNS com NLP real (em vez de regex)
5. Conectar learning extraction ao memory_pack (P4) para ciclo de feedback
