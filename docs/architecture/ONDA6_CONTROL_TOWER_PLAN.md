# ONDA 6 — CONTROL TOWER PLAN

> **Data:** 2026-05-13
> **Operador:** Lucas Tigre (Tigrão)
> **Máquina:** Kratos
> **Função:** Arquiteto Coordenador — NÃO implementar

---

## 1. Estado Atual

| Item | Valor |
|---|---|
| Branch | `master` |
| HEAD | `0367c00` — chore: ignore local bundle backups |
| Remote | up to date with `origin/master` |
| Working tree | clean |
| Full suite | **3740 passed, 2 skipped, 0 failures** |
| Progressão | **18/20 módulos (90%)** |
| Onda 5 tag | `onda5-complete-20260513` |

### Módulos integrados (18)

mission, P1 Content Scheduler, P2 Creative Production V2, P3 Caption Approval V2, P4 Memory Pack, P5 Marketing, P6 Design Art, P7 Video Studio, P8 Publisher ARGOS, P9 Commercial SDR, P10 Sales CRM, P11 App Factory, P12 Automation, P13 Analytics, P14 Finance, P15 Computer Ops, P16 Observability, P18 Governance

### Pendentes (2)

P17 Delivery & Client Portal, P19 Campaign Manager

### Bloqueado

P20 OMNIS Supreme (requer 19/19)

---

## 2. Objetivo da Onda 6

Integrar os 2 últimos módulos restantes (P17 + P19) para atingir **19/20 (95%)** e desbloquear P20 OMNIS Supreme.

Esta é a **menor onda do roadmap** — apenas 2 frentes. Porém, são os módulos de mais alto nível na cadeia de valor: entrega ao cliente (P17) e orquestração de campanhas (P19). Ambos consomem múltiplos módulos downstream já integrados.

---

## 3. Escopo P17 — Delivery & Client Portal

### Propósito

Portal de entrega de assets ao cliente pós-venda. Fecha o ciclo: **Lead → Deal → Publish → Deliver → Feedback**.

### Dependências upstream

| Dependência | Módulo | Status | O que consome |
|---|---|---|---|
| P8 | `src/publisher_argos/` | Integrado Onda 5 | `PublisherHandoff`, `ArgosExportPackage`, `ArgosExportItem` |
| P10 | `src/sales_crm/` | Integrado Onda 3 | `Deal` (closed_won), `Lead`, `ProposalRecord` |

### Funcionalidades esperadas

1. **Client Portal** — interface de entrega onde o cliente visualiza assets publicados
2. **Delivery Package** — agrupa `ArgosExportItem`(s) + metadata do Deal em um pacote entregável
3. **Feedback Loop** — cliente pode aprovar/rejeitar/comentar assets entregues
4. **Delivery Tracking** — status: `pending_delivery → delivered → viewed → feedback_received → closed`
5. **Client Link Generation** — gera link/acesso para o portal do cliente (simulado, stdlib-only)

### Pasta sugerida

```
src/delivery_portal/
├── __init__.py
├── models.py          # DeliveryPackage, ClientPortal, FeedbackItem, DeliveryStatus
├── service.py         # DeliveryPlanner
├── errors.py          # DeliveryError, etc.
tests/delivery_portal/
├── __init__.py
├── test_models.py
├── test_service.py
docs/delivery_portal/
└── P17_DELIVERY_PORTAL_SKELETON.md
```

### Contratos de entrada (input contracts)

**Do P8 (`publisher_argos`)**:
- `PublisherHandoff` — contém `ArgosExportPackage` + metadata de publicação
- `ArgosExportPackage` — contém `PublishQueuePlan` + `PublishReadinessCheck`(s)
- `ArgosExportItem` — item individual publicado com caption, media, target, schedule

**Do P10 (`sales_crm`)**:
- `Deal` — referência ao negócio fechado (id, lead_id, package, value_brl, stage)
- `Lead` — identidade do cliente (name, business_name, contact_email, contact_phone, instagram_handle)

### Contrato de saída (output contract)

- `DeliveryPackage` — encapsula handoff do publisher + deal info + status de entrega
- `ClientPortal` — representa o portal do cliente com link, assets, feedback items
- `FeedbackItem` — comentário/aprovação/rejeição do cliente sobre asset entregue

---

## 4. Escopo P19 — Campaign Manager

### Propósito

Orquestração de campanhas ponta a ponta: **Brief → Content Plan → Publish → Track → ROI Report**.

### Dependências upstream

| Dependência | Módulo | Status | O que consome |
|---|---|---|---|
| P5 | `src/marketing/` | Integrado Onda 3 | `CampaignBrief`, `CampaignPackage`, `ContentPlan`, `MarketingObjective`, `AudienceProfile`, `ContentPillar` |
| P8 | `src/publisher_argos/` | Integrado Onda 5 | `PublisherHandoff`, `ArgosExportPackage`, `PublishQueuePlan` |
| P13 | `src/analytics/` | Integrado Onda 2 | `MetricDefinition`, `MetricSummary`, `DashboardSpec`, `ReportSpec` |

### Dependência implícita (NÃO listada no roadmap original)

| Dependência | Módulo | Status | Uso |
|---|---|---|---|
| P14 | `src/finance/` | Integrado Onda 3 | `RevenueSource`, revenue models — necessário para budget tracking real |

**Decisão arquitetural:** P19 NÃO deve importar P14 diretamente. Budget tracking do P19 será modelado com dados simulados internos. Se no futuro houver integração real, um adapter bridge conectará P19 ↔ P14 sem modificar nenhum dos dois.

### Funcionalidades esperadas

1. **Campaign Orchestrator** — pipeline: brief → content plan → publish queue → track
2. **Budget Tracker** — alocação, gasto realizado vs planejado, alertas de estouro
3. **ROI Calculator** — receita estimada / custo da campanha, com breakdown por perfil
4. **Campaign Dashboard** — visão consolidada de todas as campanhas ativas
5. **Campaign Status Machine** — `draft → planned → in_progress → completed → analyzed → archived`

### Pasta sugerida

```
src/campaign_manager/
├── __init__.py
├── models.py          # Campaign, BudgetTracker, ROICalculation, CampaignStatus, CampaignDashboard
├── service.py         # CampaignPlanner
├── errors.py          # CampaignError, etc.
tests/campaign_manager/
├── __init__.py
├── test_models.py
├── test_service.py
docs/campaign_manager/
└── P19_CAMPAIGN_MANAGER_SKELETON.md
```

### Contratos de entrada (input contracts)

**Do P5 (`marketing`)**:
- `CampaignBrief` — briefing da campanha (objetivo, audiência, pillars, budget, datas, tom, CTA)
- `CampaignPackage` — brief + plano de conteúdo validado
- `ContentPlan` — grid de `ContentItem`(s) com datas, tópicos, formatos
- `MarketingObjective` — objetivo com métrica-alvo e valor-alvo

**Do P8 (`publisher_argos`)**:
- `PublisherHandoff` — resultado de publicação para tracking
- `PublishQueuePlan` — fila planejada para medir execução vs plano

**Do P13 (`analytics`)**:
- `MetricDefinition` — definição de métricas para tracking
- `MetricSummary` — sumário estatístico para ROI

### Contrato de saída (output contract)

- `Campaign` — entidade central que unifica brief + plano + tracking + ROI
- `BudgetTracker` — tracking de orçamento com allocated/spent/remaining
- `ROICalculation` — receita, custo, ROI%, payback, breakdown por perfil
- `CampaignDashboard` — visão agregada de campanhas ativas

---

## 5. O que P17 NÃO deve fazer

1. **NÃO publicar conteúdo** — publish é responsabilidade do P8
2. **NÃO criar deals ou leads** — CRM é responsabilidade do P10
3. **NÃO gerar métricas de campanha** — analytics é P13, campaign tracking é P19
4. **NÃO tocar `src/client_delivery/`** — legado intocado
5. **NÃO tocar `src/delivery_templates/`** — legado intocado
6. **NÃO importar P5 (marketing)** — entrega é pós-venda, não precisa de briefings
7. **NÃO importar P13 (analytics)** — P17 não calcula métricas
8. **NÃO implementar autenticação real** — portal é simulacro stdlib-only
9. **NÃO enviar emails reais** — links e notificações são dry-run
10. **NÃO depender de P19** — P17 não deve conhecer Campaign Manager

---

## 6. O que P19 NÃO deve fazer

1. **NÃO publicar conteúdo diretamente** — sempre via P8 `PublisherHandoff`
2. **NÃO criar conteúdo** — criação é P2/P3/P6/P7, campanha só orquestra
3. **NÃO gerenciar leads/deals** — CRM é P10
4. **NÃO tocar `src/campaign_package/`** — legado intocado
5. **NÃO tocar `src/campaign_auditor/`** — legado intocado
6. **NÃO importar P14 (finance) diretamente** — budget tracking usa modelos internos simulados
7. **NÃO importar P10 (sales_crm)** — campanha não gerencia vendas
8. **NÃO implementar conexão com Meta Ads** — ROI é calculado com dados simulados
9. **NÃO depender de P17** — P19 não deve conhecer Delivery Portal
10. **NÃO iniciar publicações sem approval gate** — seguir padrão `approval_required=True`

---

## 7. Contratos Esperados

### Contrato A: PublisherHandoff → DeliveryPackage (P8 → P17)

P17 recebe `PublisherHandoff` e o encapsula em `DeliveryPackage`.
- **Input:** `PublisherHandoff` (id, package, source_module, target_system, handed_off_at, dry_run)
- **Output:** `DeliveryPackage` (id, handoff, deal_id, client_name, status, created_at)
- **Acoplamento:** Unidirecional — P17 referencia classes do P8; P8 NÃO conhece P17

### Contrato B: Deal → DeliveryPackage (P10 → P17)

P17 referencia `Deal` para associar entrega ao cliente.
- **Input:** `Deal.id`, `Deal.lead_id` (para buscar `Lead.name`, `Lead.contact_email`, `Lead.business_name`)
- **Output:** `DeliveryPackage.deal_id`, `DeliveryPackage.client_name`
- **Acoplamento:** Unidirecional — P17 referencia classes do P10

### Contrato C: CampaignBrief → Campaign (P5 → P19)

P19 consome `CampaignBrief` do P5 e o promove a `Campaign` orquestrada.
- **Input:** `CampaignBrief` (id, name, objective_id, audience_id, pillar_ids, start_date, end_date, budget, key_message, tone, cta)
- **Output:** `Campaign` (id, brief_id, status, plan_ref, budget_tracker, roi_calc, handoff_ids)
- **Acoplamento:** Unidirecional — P19 referencia classes do P5

### Contrato D: ContentPlan → PublishQueuePlan (P5 + P8 → P19)

P19 conecta o plano de conteúdo (P5) à fila de publicação (P8).
- **Input:** `ContentPlan` (P5) + `PublishQueuePlan` (P8)
- **Output:** `Campaign.publish_queue_refs` — lista de IDs de handoffs
- **Acoplamento:** P19 conhece P5 e P8 como dependências separadas; não cria acoplamento P5↔P8

### Contrato E: MetricDefinition + MetricSummary → ROICalculation (P13 → P19)

P19 usa métricas do P13 para calcular ROI.
- **Input:** `MetricDefinition` (target_metric, target_value) + `MetricSummary` (avg, sum, count)
- **Output:** `ROICalculation` (revenue_brl, cost_brl, roi_percent, payback_months, breakdown)
- **Acoplamento:** Unidirecional — P19 referencia classes do P13

### Contrato Cross: P19 → P8 → P17 (pipeline de valor)

```
P19 Campaign        → aciona → P8 Publisher → gera PublisherHandoff
P8 PublisherHandoff → é consumido por → P17 Delivery → gera DeliveryPackage
```

**Importante:** P19 e P17 NUNCA se referenciam diretamente. O P8 (`publisher_argos`) é o ponto de mediação. P19 produz campanhas que resultam em handoffs; P17 consome handoffs para entrega. Eles não sabem da existência um do outro.

---

## 8. Pontos de Integração

### P17 ↔ P8 (`publisher_argos`)

| Direção | O que trafega | Tipo de referência |
|---|---|---|
| P8 → P17 | `PublisherHandoff`, `ArgosExportPackage`, `ArgosExportItem`, `PublishQueuePlan` | Import de classes (models) |

**Validação:** P17 deve conseguir instanciar `DeliveryPackage` a partir de um `PublisherHandoff` + `Deal`.

### P17 ↔ P10 (`sales_crm`)

| Direção | O que trafega | Tipo de referência |
|---|---|---|
| P10 → P17 | `Deal` (id, lead_id, package, value_brl, stage), `Lead` (id, name, business_name, contact_email) | Import de classes (models) |

### P19 ↔ P5 (`marketing`)

| Direção | O que trafega | Tipo de referência |
|---|---|---|
| P5 → P19 | `CampaignBrief`, `CampaignPackage`, `ContentPlan`, `MarketingObjective`, `ContentItem` | Import de classes (models) |

### P19 ↔ P8 (`publisher_argos`)

| Direção | O que trafega | Tipo de referência |
|---|---|---|
| P8 → P19 | `PublisherHandoff` (id), `PublishQueuePlan` | Import de classes (id refs) |
| P19 → P8 | (conceitual) campanha dispara build do queue plan | Sem import reverso |

### P19 ↔ P13 (`analytics`)

| Direção | O que trafega | Tipo de referência |
|---|---|---|
| P13 → P19 | `MetricDefinition`, `MetricSummary` | Import de classes (models) |

### P17 ↔ P19 (via P8 — indireto)

NÃO há integração direta. O pipeline de valor é:

```
Deal (P10) + Brief (P5) → [P19 Campaign → P8 Publish → P17 Delivery] → Cliente recebe
```

O operador (humano ou P20 Supreme) conecta as pontas. Os módulos permanecem isolados.

---

## 9. Riscos Arquiteturais

| # | Risco | Severidade | Frente | Mitigação |
|---|---|---|---|---|
| R1 | P17 e P19 ambos importam P8 — namespace compartilhado | Média | Ambas | Cada módulo importa apenas classes específicas, não o módulo inteiro. Verificar que imports não criam dependência cíclica. |
| R2 | P19 precisa de budget tracking mas P14 (Finance) não está listado como dependência | Baixa | P19 | P19 usa modelos internos simulados para budget. NÃO importar P14. Adapter futuro fará a ponte. |
| R3 | P17 pode querer acessar métricas de entrega (views, feedback) que não existem | Baixa | P17 | Modelar com dados simulados. Métricas reais virão do P13 no futuro. |
| R4 | P19 ROI calculator pode produzir números sem sentido se dados simulados forem inconsistentes | Baixa | P19 | Definir fixtures realistas nos testes: CPM R$0,15, ticket médio R$350-1200, 3-5 collabs por campanha. |
| R5 | Escopos de P17/P19 podem "vazar" e querer orquestrar além do contrato | Média | Ambas | Checklist de revisão (seções 10-12) bloqueia qualquer funcionalidade fora do escopo definido. |
| R6 | Pastas legadas com nomes similares (`client_delivery/`, `delivery_templates/`, `campaign_package/`, `campaign_auditor/`) podem ser confundidas | Baixa | Ambas | P17 usa `delivery_portal/`, P19 usa `campaign_manager/`. Nomes distintos dos legados. Validação de escopo verifica que imports não cruzam para legado. |
| R7 | P19 pode querer depender de P17 (campanha → delivery automático) | Alta | P19 | PROIBIDO. P19 não conhece P17. Pipeline P19→P8→P17 é mediado pelo operador/P20, não por acoplamento direto. |

---

## 10. Checklist de Revisão P17

Antes de liberar implementação de P17, verificar:

- [ ] Pasta: `src/delivery_portal/` (NÃO `src/client_delivery/`, `src/delivery_templates/`)
- [ ] Models: DeliveryPackage, ClientPortal, FeedbackItem, DeliveryStatus (enum)
- [ ] Service: `DeliveryPlanner` com métodos `build_delivery_package()`, `create_portal()`, `record_feedback()`
- [ ] Erros: DeliveryError (base), e subclasses específicas
- [ ] Imports: referencia APENAS `src/publisher_argos/models.py` e `src/sales_crm/models.py`
- [ ] NÃO importa: P5 (marketing), P13 (analytics), P14 (finance), P19 (campaign_manager)
- [ ] NÃO importa: `src/client_delivery/`, `src/delivery_templates/`
- [ ] Padrão `dry_run: bool = True` em todos os modelos + service
- [ ] Padrão `approval_required: bool = True` em operações de entrega
- [ ] IDs com prefixo consistente (ex: `dlv_`, `pkg_`, `fb_`)
- [ ] `.new()` classmethod como construtor canônico
- [ ] `.to_dict()` / `.from_dict()` em todos os modelos
- [ ] `_now_iso()` helper para timestamps
- [ ] Testes isolados em `tests/delivery_portal/` — sem dependência de runtime real
- [ ] Documento skeleton em `docs/delivery_portal/P17_DELIVERY_PORTAL_SKELETON.md`
- [ ] Targeted tests passam: `python -m pytest tests/delivery_portal/ -q`

---

## 11. Checklist de Revisão P19

Antes de liberar implementação de P19, verificar:

- [ ] Pasta: `src/campaign_manager/` (NÃO `src/campaign_package/`, `src/campaign_auditor/`)
- [ ] Models: Campaign, BudgetTracker, ROICalculation, CampaignStatus (enum), CampaignDashboard
- [ ] Service: `CampaignPlanner` com métodos `orchestrate_campaign()`, `track_budget()`, `calculate_roi()`, `build_dashboard()`
- [ ] Erros: CampaignError (base), e subclasses específicas
- [ ] Imports: referencia APENAS `src/marketing/models.py`, `src/publisher_argos/models.py`, `src/analytics/models.py`
- [ ] NÃO importa: P10 (sales_crm), P14 (finance), P17 (delivery_portal)
- [ ] NÃO importa: `src/campaign_package/`, `src/campaign_auditor/`
- [ ] Padrão `dry_run: bool = True` em todos os modelos + service
- [ ] Padrão `approval_required: bool = True` em operações de campanha
- [ ] Status machine: draft → planned → in_progress → completed → analyzed → archived
- [ ] ROI calculator usa dados simulados realistas (CPM R$0,15, tickets R$350-1200)
- [ ] Budget tracker: allocated / spent / remaining com alertas
- [ ] IDs com prefixo consistente (ex: `cmp_`, `bud_`, `roi_`, `dash_`)
- [ ] `.new()` classmethod como construtor canônico
- [ ] `.to_dict()` / `.from_dict()` em todos os modelos
- [ ] `_now_iso()` helper para timestamps
- [ ] Testes isolados em `tests/campaign_manager/` — sem dependência de runtime real
- [ ] Documento skeleton em `docs/campaign_manager/P19_CAMPAIGN_MANAGER_SKELETON.md`
- [ ] Targeted tests passam: `python -m pytest tests/campaign_manager/ -q`

---

## 12. Checklist de Integração P17 + P19

Após ambos os módulos implementados, ANTES do merge:

- [ ] P17 targeted tests passam isolados
- [ ] P19 targeted tests passam isolados
- [ ] Full suite (`python -m pytest tests/ -q`) passa sem quebras
- [ ] Nenhum módulo legado foi modificado (`git diff --stat master -- src/client_delivery/ src/delivery_templates/ src/campaign_package/ src/campaign_auditor/ src/publisher/ src/argos_bridge/`)
- [ ] `git diff --stat master -- src/` mostra APENAS novos arquivos em `src/delivery_portal/` e `src/campaign_manager/`
- [ ] Nenhum import de P17 referencia P19 (e vice-versa)
- [ ] Ambos importam P8 (`publisher_argos`) sem conflito de namespace
- [ ] Número de testes acumulados aumentou (3740 + testes P17 + testes P19)
- [ ] Nenhum `# type: ignore` ou workaround suspeito nos imports
- [ ] `approval_required=True` é padrão em ambos os services

---

## 13. Critérios para Liberar Implementação

Só iniciar código quando TODOS estes forem verdade:

1. [x] Documento Control Tower aprovado pelo operador ← **AGUARDANDO**
2. [ ] Repo limpo (`git status --short` vazio exceto possíveis untracked seguros)
3. [ ] Tag `safe-before-onda6-<date>` criada
4. [ ] Bundle pré-onda6 salvo na Desktop
5. [ ] Worktrees criadas: apenas 2 (P17 + P19)
6. [ ] Cada frente recebeu cópia deste documento + checklist específico
7. [ ] Operador explicitamente autorizou: "Iniciar Onda 6 — P17 e P19"

---

## 14. Estratégia de Testes

### Por frente (targeted)

```
python -m pytest tests/delivery_portal/ -q    # P17 isolado
python -m pytest tests/campaign_manager/ -q   # P19 isolado
```

### Mínimo esperado por módulo

| Módulo | Testes mínimos | Cobertura esperada |
|---|---|---|
| P17 Delivery | ≥ 40 | Models: CRUD de DeliveryPackage, Portal, Feedback. Service: build, track, feedback loop. |
| P19 Campaign | ≥ 50 | Models: Campaign state machine, BudgetTracker, ROI calc. Service: orchestrate, track, dashboard. |

### Full suite pós cada merge

```
python -m pytest tests/ -q
```

Resultado esperado: **3740 + tests_P17 + tests_P19** passando, 0 failures.

---

## 15. Estratégia de Merge Futura

### Ordem (apenas 2 frentes)

| Ordem | Módulo | Justificativa |
|---|---|---|
| 1º | P19 Campaign Manager | P19 tem + dependências (P5+P8+P13) e + complexidade. Merge primeiro para validar que tudo integra. |
| 2º | P17 Delivery Portal | P17 é mais simples (P8+P10). Merge por último fecha a onda. |

### Protocolo (idêntico às ondas anteriores)

```
Merge 1 (P19):
  git merge --no-ff parallel/p19-campaign-manager
  python -m pytest tests/campaign_manager/ -q   # targeted
  python -m pytest tests/ -q                      # full suite

Merge 2 (P17):
  git merge --no-ff parallel/p17-delivery-portal
  python -m pytest tests/delivery_portal/ -q     # targeted
  python -m pytest tests/ -q                      # full suite
```

### Pós-merge

1. Validar legados intocados
2. Tag `onda6-complete-20260513` (anotada)
3. Bundle `omnis-onda6-complete-20260513.bundle`
4. Remover worktrees + branches parallel
5. Push master + tags (com aprovação explícita)

---

## 16. Recomendação de Worktrees para Implementação

### Número: 2

Onda 6 é a menor de todas. Apenas 2 frentes. Recomendação:

- **1 worktree por frente** (total: 2)
- NÃO usar 4 worktrees — seria ocioso
- Paralelismo real: abrir 2 abas do Claude Code simultâneas

### Nomes

| Worktree | Branch | Path |
|---|---|---|
| `omnis-p17-delivery-portal` | `parallel/p17-delivery-portal` | `../omnis-p17-delivery-portal` |
| `omnis-p19-campaign-manager` | `parallel/p19-campaign-manager` | `../omnis-p19-campaign-manager` |

### Nome do módulo (FrenteName)

```
p17-delivery-portal
p19-campaign-manager
```

### Comandos de criação

```powershell
. .\scripts\omnis_parallel.ps1
Test-OmnisClean
New-OmnisSafetyTag
Start-ClaudeWorktree -FrenteName "p17-delivery-portal"
Start-ClaudeWorktree -FrenteName "p19-campaign-manager"
Get-ClaudeWorktrees
```

---

## Apêndice A — Superfície de API das Dependências

Resumo do que P17 e P19 podem importar:

### Do P8 (`src/publisher_argos/models.py`)

```python
PublishChannel(Enum): INSTAGRAM_FEED, INSTAGRAM_STORY, INSTAGRAM_REEL
ExportStatus(Enum):    DRAFT, READY, QUEUED, EXPORTED, BLOCKED
ReadinessVerdict(Enum): PASS, FAIL, PENDING_APPROVAL
PublishTarget:         handle, profile, channel, followers, label
ArgosExportItem:       id, target, caption, media_url, media_type, tags, schedule_iso, status, approval_required
PublishReadinessCheck: item_id, verdict, checks, passed, failed, blocked, reason
PublishQueuePlan:      id, items, label, dry_run
ArgosExportPackage:    id, queue_plan, readiness_checks, label, dry_run, approval_required
PublisherHandoff:      id, package, source_module, target_system, handed_off_at, dry_run, notes
```

### Do P10 (`src/sales_crm/models.py`)

```python
PipelineStage(Enum): PROSPECTING..CLOSED_WON, CLOSED_LOST
LeadSource(Enum):    INSTAGRAM..UNKNOWN
LeadStatus(Enum):    NEW..DISQUALIFIED
DealPriority(Enum):  LOW, MEDIUM, HIGH, URGENT
ProposalStatus(Enum): DRAFT..EXPIRED
Lead:                id, name, business_name, contact_phone, contact_email, instagram_handle, source, status, score, tags, city, state, niche
Deal:                id, lead_id, package, value_brl, stage, priority, probability, expected_close_date
SalesPipeline:       id, name, description, deals, active_deals, total_value, weighted_value
ProposalRecord:      id, lead_id, deal_id, package, value_brl, status, content_summary
PipelineSummary:     pipeline_id, total_deals, active_deals, total_value, weighted_value, won_deals, won_value
```

### Do P5 (`src/marketing/models.py`)

```python
MarketingObjective:  id, name, description, objective_type, priority, target_metric, target_value
AudienceProfile:     id, name, description, demographics, interests, pain_points, platforms
ContentPillar:       id, name, description, pillar_type, topics, content_formats, frequency
ContentItem:         date, pillar_id, topic, content_format, platform, hook, cta
CampaignBrief:       id, name, objective_id, audience_id, pillar_ids, start_date, end_date, budget, key_message, call_to_action, tone
ContentPlan:         id, campaign_id, items, schedule_start, schedule_end
CampaignPackage:     id, name, brief, plan, validation_issues, validation_warnings
```

### Do P13 (`src/analytics/models.py`)

```python
MetricDefinition:    id, name, description, category, aggregation, unit, dimensions, filters, target
MetricEvent:         id, metric_id, value, timestamp, dimensions, metadata
MetricSummary:       metric_id, count, sum, avg, min, max, median, std_dev
DashboardSpec:       id, title, description, layout, widgets, refresh_interval_minutes
ReportSpec:          id, title, description, sections, format
```

---

## Apêndice B — Mapa de Legados a Preservar

Estes 4 diretórios NÃO devem ser tocados por P17 nem P19:

| Diretório | Status | Motivo |
|---|---|---|
| `src/client_delivery/` | Legado | Código antigo de entrega — P17 usa `delivery_portal/` |
| `src/delivery_templates/` | Legado | Templates antigos — P17 usa modelos internos |
| `src/campaign_package/` | Legado | Pacotes de campanha antigos — P19 usa `campaign_manager/` |
| `src/campaign_auditor/` | Legado | Auditor antigo — P19 tem validação interna |

---

*OMNIS Control Tower — Onda 6 planejada. Aguardando aprovação do operador.*
*Próximo passo: aprovação → tag segurança → 2 worktrees → implementar P17 + P19 em paralelo.*
