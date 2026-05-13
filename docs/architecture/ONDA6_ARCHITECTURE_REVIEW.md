# ONDA 6 — ARCHITECTURE REVIEW

> **Data:** 2026-05-13
> **Auditor:** CONTROL TOWER (automatizado)
> **Documentos fonte:**
> - `ONDA6_CONTROL_TOWER_PLAN.md` (CT)
> - `P17_DELIVERY_ARCHITECTURE.md` (P17)
> - `P19_CAMPAIGN_ARCHITECTURE.md` (P19)

---

## VEREDICT FINAL

```
██████████████████████████████████████████████████████████
█                                                        █
█   VEREDITO: BLOQUEADO — NÃO INICIAR IMPLEMENTAÇÃO      █
█                                                        █
█   Motivo: 11 desvios críticos do Control Tower Plan.   █
█   Ambos os documentos expandiram escopo unilateralmente █
█   e divergem em namespaces, dependências, estados, e    █
█   contratos. Ajustes obrigatórios listados abaixo.      █
█                                                        █
██████████████████████████████████████████████████████████
```

---

## 1. OVERLAPS — Responsabilidades Duplicadas

### OV-1: Export/Bundle ZIP (CRÍTICO)

Ambos querem ser "o exportador":
- **P17:** `DeliveryExporter` → ZIP, JSON standalone, CSV, Markdown
- **P19:** `CampaignBundle` → ZIP, JSON, CSV, MD, `exporters.py` completo

**Conflito:** Se P19 gera o bundle e P17 também exporta ZIP, quem é dono do arquivo final? Gera ZIP duplicado com namespace diferente?

**Resolução:** P8 (`publisher_argos`) já tem `export_argos_json()`. P17 encapsula handoff em `DeliveryPackage` (sem re-exportar). P19 gera campaign-level manifest (JSON), mas ZIP físico é P17. P19 só referencia path.

---

### OV-2: Asset Mapping (MÉDIO)

- **P17:** `ArtifactRecord` — artefato rastreável com hash, source_module, validated
- **P19:** `CampaignAsset` — asset rastreável com stage_ref, creative_ref, caption_ref

Ambos modelam "asset rastreável dentro de um pacote". P17 foca no artefato físico (arquivo, hash, tamanho). P19 foca no artefato lógico (qual stage, qual canal, status de aprovação).

**Resolução:** Não é duplicação — são camadas diferentes. P19 mapeia asset→stage (visão campanha). P17 rastreia arquivo→hash (visão entrega). Mas os dois precisam referenciar o mesmo `creative_ref` e `caption_ref`. Definir contrato de IDs compartilhado.

---

### OV-3: Validation (BAIXO)

- **P17:** `DeliveryContractValidator` — valida required/optional artifacts
- **P19:** `validator.py` — Contract validation + cross-module consistency

Sobreposição leve. P17 valida integridade do package (artefatos presentes, hashes OK). P19 valida integridade da campanha (contrato consistente, canais válidos). OK manter separados.

---

## 2. CONTRATOS — Incompatibilidades

### CT-1: NAMESPACE DIVERGENCE (BLOQUEADOR)

| Módulo | Control Tower | Documento P17/P19 | Delta |
|---|---|---|---|
| P17 | `src/delivery_portal/` | `src/delivery_engine/` | ❌ Divergente |
| P19 | `src/campaign_manager/` | `src/campaign_engine/` | ❌ Divergente |

**Regra violada:** CT definiu pastas para evitar conflito com legados. Ambos decidiram unilateralmente renomear.
- `delivery_portal` ≠ `client_delivery` (legado) → nome correto
- `campaign_manager` ≠ `campaign_package` (legado), ≠ `campaign_auditor` (legado) → nome correto

**Ação:** P17 renomear para `src/delivery_portal/`. P19 renomear para `src/campaign_manager/`. **Inegociável.**

---

### CT-2: DEPENDENCY LIST EXPLOSION (BLOQUEADOR)

| Módulo | Control Tower (deps permitidas) | Documento (deps declaradas) | Deltas |
|---|---|---|---|
| P17 | P8 + P10 | P2 + P3 + P8 + P10 | +P2, +P3 ❌ |
| P19 | P5 + P8 + P13 | P2 + P3 + P5 + P8 + P13 | +P2, +P3 ❌ |

Ambos adicionaram P2 (Creative Production) e P3 (Caption Approval) como dependências diretas. A CT explicitamente **NÃO** listou P2 e P3 porque:
- P17: recebe outputs já empacotados via P8 `PublisherHandoff`. Não precisa acessar P2/P3 direto.
- P19: orquestra via contratos (brief do P5 → plano → publish via P8). Não precisa acessar P2/P3 direto.

**Ação:** Remover P2 e P3 das dependências diretas. Se o fluxo exige dados do P2/P3, eles chegam via P8 (`ArgosExportItem` já contém caption, media_url) ou P5 (`CampaignBrief` já contém tudo que P19 precisa).

---

### CT-3: STATE MACHINE DIVERGENCE (CRÍTICO)

#### P17 States

| Fonte | Estados |
|---|---|
| **CT** | `pending_delivery → delivered → viewed → feedback_received → closed` (5) |
| **P17** | `draft → ready → exported → failed → delivered → accepted → rejected → archived` (8) |

**Divergências:**
1. CT não tem `exported` como estado separado — export é ação, não estado
2. CT não tem `failed` — failures são tratados via retry, não como estado persistido
3. CT tem `viewed` e `feedback_received` — P17 não tem
4. CT não tem `accepted/rejected` como estados do Delivery — isso é Feedback
5. CT não tem `archived` — archive é operação de infra, não estado de negócio

#### P19 States

| Fonte | Estados |
|---|---|
| **CT** | `draft → planned → in_progress → completed → analyzed → archived` (6) |
| **P19** | `draft, planning, staged, dry_run_ok, dry_run_failed, running, paused, failed, complete, cancelled, archived` (11) |

**Divergências:**
1. CT tem `analyzed` — P19 não tem (fundiu com `complete`)
2. CT não tem `dry_run_ok/dry_run_failed` como estados persistidos — dry-run é validação, não ciclo de vida
3. CT não tem `paused` — pausa é operacional, não estado de campanha
4. CT não tem `cancelled` — é `archived` com motivo
5. CT não tem `staged` — é sub-estado do `planned`

**Ação:** Ambos alinharem com CT. Dry-run, retry, pause são **operações sobre estados**, não estados em si.

---

### CT-4: P10 NAMING ERROR (CRÍTICO)

P17 repetidamente chama P10 de "Approval Center":
- Linha 6: `P10 Approval Center`
- Linha 44: `P10 Approval Center`
- Seção 11: "Relação com Approval Center (P10)"

**Erro:** P10 é **Sales CRM** (`src/sales_crm/`). O módulo `src/approval_center/` é um legado separado, NÃO é o P10.

Isso causa confusão grave: P17 acha que está falando com um "approval_center" quando na verdade está falando com o CRM. O CRM gerencia Deals e Leads, não tokens de aprovação.

**Ação:** Corrigir todas as referências. P17 depende de P10 (Sales CRM) para `Deal` + `Lead`. Tokens de aprovação são modelados internamente no P17 como `approval_token` (string opaca simulada), não consumidos de módulo externo.

---

### CT-5: P19 DEPENDENCY NAMING ERROR (MÉDIO)

P19 header diz: `P8 (Execution Graph)`. Mas P8 no roadmap é **Publisher / ARGOS Export** (`src/publisher_argos/`).

O módulo `src/execution_graph/` é um componente legado separado, NÃO é P8.

P19 Seção 16 tenta resolver isso mencionando "P8 Lite (atual)" vs "P8 Publisher (futuro)", mas isso cria uma distinção que não existe formalmente. Só existe UM P8 integrado: `publisher_argos/`.

**Ação:** P19 referenciar P8 como `src/publisher_argos/` apenas. Se precisar de DAG, usar algoritmo de Kahn internamente (como o P8 já faz), sem acoplar ao `execution_graph/` legado.

---

### CT-6: SCHEMA INCOMPATIBILITY NO HANDOFF (CRÍTICO)

**P8 `PublisherHandoff`** (real, integrado):
```
id, package (ArgosExportPackage), source_module, target_system,
handed_off_at, dry_run, notes, approval_required, approved_by
```

**P17 `HandoffReceipt`** (proposto):
```
handoff_id, package_id, status (HandoffStatus), artifacts_ready,
approval_valid, export_formats_available, warnings,
requires_manual_review, reviewed_by, acknowledged_at
```

**Problemas:**
1. Nomes diferentes para o mesmo conceito (`handoff_id` vs `id`)
2. P17 adiciona campos que P8 não tem (`artifacts_ready`, `export_formats_available`, `acknowledged_at`)
3. P17 omite campos que P8 tem (`source_module`, `target_system`, `approved_by`, `package`)
4. P17 referencia `package_id` (string) enquanto P8 referencia `package` (objeto `ArgosExportPackage` inteiro)

**Ação:** P17 NÃO deve criar novo modelo de handoff. Deve **encapsular** `PublisherHandoff` do P8 dentro de `DeliveryPackage.handoff_ref`. O handoff é propriedade do P8 — P17 só referencia.

---

### CT-7: DELIVERY_TEMPLATES REFERENCE (BLOQUEADOR)

CT seção 5.5: "NÃO tocar `src/delivery_templates/`".

P17 seção 3 lista como entradas opcionais:
```
brand_kit (opcional)    → delivery_templates → BrandKit
delivery_template (opcional) → delivery_templates → DeliveryTemplate
```

**Violação direta.** P17 referencia módulo legado que deveria permanecer intocado.

**Ação:** Remover `brand_kit` e `delivery_template` do input contract. Templates são definidos internamente.

---

## 3. ACOPLAMENTO

### AC-1: P17 ↔ P19 via campaign delivery (MÉDIO)

P17 seção 15 ("Relação futura com P19 Campaign") define métodos:
- `build_campaign_delivery(campaign_id)`
- `export_campaign_zip(campaign_id)`
- `campaign_delivery_report(campaign_id)`

Isso cria acoplamento conceitual: P17 sabe que "campanha" existe e oferece API para ela. A CT explicitamente diz que P17 e P19 NÃO se conhecem.

**Ação:** Remover seção 15 inteira. Quando P20 Supreme existir, ele fará a ponte. P17 entrega packages individuais. Fim.

---

### AC-2: P19 → P17 via delivery package (MÉDIO)

P19 seção 17 define contrato P17↔P19:
```
P19 → P17: CampaignBundle completo (contrato + assets + legendas + calendário)
P17 → P19: Confirmação de entrega, feedback, métricas
```

Isso também viola a regra de isolamento. P19 modela o que P17 "deveria retornar" sem P17 existir.

**Ação:** Remover. P19 emite `CampaignBundle` para `exports/campaigns/`. Fim. O operador ou P20 decide se isso vai para P17.

---

### AC-3: Risco de God Object — CampaignPlanner (BAIXO)

P19 `CampaignPlanner` tem 12 métodos cobrindo: contract, stages, CTA, channels, calendar, assets, graph, dry-run, metrics, bundle, full pipeline.

Isso é um `CampaignPlanner` ou um `CampaignOrchestrator`? Nome sugere planejamento, mas escopo cobre execução, tracking, e export.

**Ação:** Dividir. `CampaignPlanner` (planejamento: contract, stages, calendar, metrics_plan) + `CampaignTracker` (execução: status, progresso). Ou manter nome mais honesto: `CampaignOrchestrator`.

---

### AC-4: P19 → execution_graph legado (BAIXO)

P19 seção 13 referencia "padrão P8 Execution Graph (Kahn topological sort)". Se P19 implementa Kahn internamente (stdlib, sem import), OK. Se importa `src/execution_graph/`, é acoplamento com legado não autorizado.

**Ação:** Esclarecer que ordenação topológica é implementada inline (stdlib `collections.deque`), sem import de módulo externo.

---

## 4. FLUXO OPERACIONAL

Diagrama validado (consistente entre CT e módulos):

```
P10 (Deal fechado) ──→ P19 (Campaign) ──→ P8 (PublisherHandoff) ──→ P17 (DeliveryPackage)
                         │                    │                          │
                     consome P5           gera handoff              encapsula handoff
                     (CampaignBrief)      ┌─ ArgosExportItem        └─ + Deal metadata
                     consome P13          └─ PublishReadinessCheck     + feedback loop
                     (MetricDefinition)
```

**Handoff points confirmados:**
1. **P5 → P19:** `CampaignBrief` + `CampaignPackage` (marketing define, campaign orquestra)
2. **P19 → P8:** campanha gera `PublishQueuePlan` via `PublisherArgosPlanner`
3. **P8 → P17:** `PublisherHandoff` (pacote publicado) → P17 encapsula em `DeliveryPackage`

**Ordem de execução:** P19 (planejar campanha) → P8 (publicar) → P17 (entregar ao cliente).

Implementação: P19 primeiro (depende de 3 módulos já estáveis). P17 segundo (depende de P8 + P10).

---

## 5. INTEGRAÇÃO COM MÓDULOS EXISTENTES

### P2 Creative Production V2 (`src/creative_production_v2/`)
- **Status:** NÃO deve ser referenciado por P17 nem P19
- **Risco:** Ambos os documentos adicionaram P2 como dependência (violação)
- **Ação:** Remover

### P3 Caption Approval V2 (`src/caption_approval_v2/`)
- **Status:** NÃO deve ser referenciado por P17 nem P19
- **Risco:** Ambos os documentos adicionaram P3 como dependência (violação)
- **Ação:** Remover

### P8 Publisher ARGOS (`src/publisher_argos/`)
- **Status:** Referência autorizada para AMBOS
- **Risco:** Ambos criaram modelos de handoff próprios em vez de encapsular `PublisherHandoff`
- **Ação:** P17 e P19 devem importar e encapsular `PublisherHandoff`, não redefini-lo

### P10 Sales CRM (`src/sales_crm/`)
- **Status:** Referência autorizada para P17 apenas
- **Risco:** P17 chama de "Approval Center" (nome errado)
- **Ação:** Corrigir nomenclatura

### P13 Analytics (`src/analytics/`)
- **Status:** Referência autorizada para P19 apenas
- **Risco:** P19 pode querer importar mais do que `MetricDefinition` + `MetricSummary`
- **Ação:** Auditoria de imports na revisão de código

### P16 Observability (`src/observability_local/`)
- **Status:** NÃO listado como dependência no CT
- **Observação:** Ambos P17 e P19 propõem `observability.py` / logs estruturados com trace_id. Isso é OK como implementação interna (stdlib `logging` / JSONL), desde que não importem `src/observability_local/`.
- **Ação:** Logs estruturados internamente, sem depender de P16

---

## 6. ESTRATÉGIA DE IMPLEMENTAÇÃO

### O que o CT definiu (mantido):

| Parâmetro | Valor |
|---|---|
| Worktrees | 2 |
| Ordem merge | P19 → P17 |
| Paralelismo | 2 abas Claude Code simultâneas |

### O que precisa ser ajustado ANTES de criar worktrees:

1. **Alinhar namespaces:** `delivery_portal/` e `campaign_manager/`
2. **Congelar contratos de import:** P17 só importa P8+P10. P19 só importa P5+P8+P13.
3. **Congelar state machines:** CT define os estados canônicos. Módulos implementam exatamente esses.
4. **Reduzir escopo de arquivos:** Cada módulo = 4 arquivos core (models, service, errors, `__init__`). Nada de `builder.py`, `exporter.py`, `handoff.py`, `registry.py`, `scheduler.py`, `cta_chain.py`, `dry_run.py`, `archiver.py`, `retry.py`, `observability.py` na fase skeleton.
5. **Eliminar referências a legados:** Zero imports de `client_delivery/`, `delivery_templates/`, `campaign_package/`, `campaign_auditor/`, `execution_graph/`, `approval_center/`.

### Estrutura alvo (skeleton — corrigida):

```
src/delivery_portal/
├── __init__.py
├── models.py     # DeliveryPackage, DeliveryStatus (enum), FeedbackItem
├── service.py    # DeliveryPlanner
├── errors.py     # DeliveryError, etc.

src/campaign_manager/
├── __init__.py
├── models.py     # Campaign, CampaignStatus (enum), BudgetTracker, ROICalculation
├── service.py    # CampaignPlanner
├── errors.py     # CampaignError, etc.
```

---

## 7. ESTRATÉGIA DE TESTES

### Recomendação (alinhada ao CT, reduzida do proposto):

| Módulo | Mínimo CT | Proposto | Recomendado |
|---|---|---|---|
| P17 | ≥ 40 | 160-200 | **50-70** — models + service + state machine + contratos |
| P19 | ≥ 50 | 120-150 | **60-80** — models + service + budget + ROI + contratos |

**Princípios:**
- Skeleton é stdlib-only, determinístico, sem side effects
- Foco em: instanciação de modelos, `.new()` factories, state transitions, `to_dict()`/`from_dict()`, validações de contrato
- NÃO testar: ZIP, CSV, CLI, logs, retry, dry-run — isso é feature, não skeleton

---

## 8. RISCOS

| # | Risco | Severidade | Status após review |
|---|---|---|---|
| R1 | Módulos divergem namespaces definidos pelo CT | **BLOQUEADOR** | ❌ Exige correção antes de iniciar |
| R2 | Dependências adicionadas (P2, P3) sem autorização | **BLOQUEADOR** | ❌ Exige remoção antes de iniciar |
| R3 | State machines não alinhadas com CT | **CRÍTICO** | ❌ Exige alinhamento |
| R4 | P10 referenciado com nome errado ("Approval Center") | **CRÍTICO** | ❌ Exige correção |
| R5 | P17 referencia `delivery_templates` (legado proibido) | **BLOQUEADOR** | ❌ Exige remoção |
| R6 | Modelos de handoff incompatíveis com P8 `PublisherHandoff` | **CRÍTICO** | ❌ Exige encapsulamento, não redefinição |
| R7 | P17↔P19 acoplamento conceitual via campaign delivery | **MÉDIO** | ⚠️ Exige remoção das seções cross |
| R8 | P19 referencia `execution_graph` (nome confuso com P8) | **MÉDIO** | ⚠️ Exige esclarecimento |
| R9 | Escopo de arquivos 3x maior que padrão skeleton | **MÉDIO** | ⚠️ Exige redução para 4 arquivos core |
| R10 | Ambos querem escrever em `data/` (runtime paths) | **BAIXO** | ⚠️ Models in-memory, sem write em disco no skeleton |
| R11 | Test count inflado (160-200 vs 40-50) sinaliza scope creep | **BAIXO** | ⚠️ Reduzir para faixa 50-80 |

---

## 9. CRITÉRIOS DE ACEITE (CORRIGIDOS)

### P17 — Delivery Portal

- [ ] Pasta `src/delivery_portal/` (nome exato)
- [ ] Models: `DeliveryPackage`, `DeliveryStatus` (enum 5 estados CT), `FeedbackItem`
- [ ] Service: `DeliveryPlanner` com `build_delivery_package(handoff: PublisherHandoff, deal: Deal) → DeliveryPackage`
- [ ] Imports: APENAS `src/publisher_argos/models.py` + `src/sales_crm/models.py`
- [ ] NÃO importa: P2, P3, P5, P13, P14, P19, `client_delivery`, `delivery_templates`, `approval_center`, `execution_graph`
- [ ] `dry_run: True`, `approval_required: True`
- [ ] IDs prefixo `dlv_`, `pkg_`, `fbk_`
- [ ] `.new()` + `.to_dict()` + `.from_dict()` + `_now_iso()`
- [ ] Targeted tests: ≥ 40 passando em `tests/delivery_portal/`

### P19 — Campaign Manager

- [ ] Pasta `src/campaign_manager/` (nome exato)
- [ ] Models: `Campaign`, `CampaignStatus` (enum 6 estados CT), `BudgetTracker`, `ROICalculation`
- [ ] Service: `CampaignPlanner` com `orchestrate_campaign(brief: CampaignBrief) → Campaign`
- [ ] Imports: APENAS `src/marketing/models.py` + `src/publisher_argos/models.py` + `src/analytics/models.py`
- [ ] NÃO importa: P2, P3, P10, P14, P17, `campaign_package`, `campaign_auditor`, `execution_graph`, `approval_center`
- [ ] `dry_run: True`, `approval_required: True`
- [ ] IDs prefixo `cmp_`, `bud_`, `roi_`
- [ ] `.new()` + `.to_dict()` + `.from_dict()` + `_now_iso()`
- [ ] Targeted tests: ≥ 50 passando em `tests/campaign_manager/`

### P20 Unlock

- [ ] 19/20 módulos integrados
- [ ] Full suite: 3740 + P17_tests + P19_tests passando
- [ ] P17 e P19 isolados (zero imports cruzados)
- [ ] 4 legados preservados (client_delivery, delivery_templates, campaign_package, campaign_auditor)
- [ ] 2 legados adicionais preservados (publisher, argos_bridge)

---

## 10. RESUMO DE AÇÕES

### OBRIGATÓRIAS (11 — sem estas, NÃO iniciar)

| # | Ação | Dono |
|---|---|---|
| 1 | Renomear P17 para `src/delivery_portal/` | P17 |
| 2 | Renomear P19 para `src/campaign_manager/` | P19 |
| 3 | P17 remover P2 e P3 das dependências | P17 |
| 4 | P19 remover P2 e P3 das dependências | P19 |
| 5 | P17 alinhar DeliveryStatus com 5 estados do CT | P17 |
| 6 | P19 alinhar CampaignStatus com 6 estados do CT | P19 |
| 7 | P17 corrigir "P10 Approval Center" → "P10 Sales CRM" | P17 |
| 8 | P17 remover referências a `delivery_templates` | P17 |
| 9 | P17 encapsular `PublisherHandoff` do P8 (não redefinir) | P17 |
| 10 | P19 corrigir referência "P8 Execution Graph" → "P8 Publisher ARGOS" | P19 |
| 11 | Ambos remover acoplamento cruzado (P17 §15, P19 §17) | P17 + P19 |

### RECOMENDADAS (5 — melhoram qualidade, não bloqueiam)

| # | Ação | Dono |
|---|---|---|
| 12 | Reduzir arquivos para 4 core (models, service, errors, __init__) | Ambos |
| 13 | Reduzir testes para faixa 50-80 (P17) e 60-80 (P19) | Ambos |
| 14 | Remover planejamento de CLI commands (fase feature, não skeleton) | Ambos |
| 15 | P19 renomear `CampaignPlanner` → considerar `CampaignOrchestrator` | P19 |
| 16 | P19 esclarecer que topological sort é inline, sem import de `execution_graph` | P19 |

---

## 11. LISTA DE VERIFICAÇÃO PÓS-CORREÇÃO

Antes de re-submeter para aprovação:

- [ ] `grep -r "delivery_engine" docs/architecture/P17_*.md` retorna VAZIO
- [ ] `grep -r "campaign_engine" docs/architecture/P19_*.md` retorna VAZIO
- [ ] `grep -r "Approval Center" docs/architecture/P17_*.md` retorna VAZIO
- [ ] `grep -r "Execution Graph" docs/architecture/P19_*.md` retorna VAZIO
- [ ] `grep -r "delivery_templates" docs/architecture/P17_*.md` retorna VAZIO
- [ ] `grep "deps\|dependências\|Dependencies" docs/architecture/P17_*.md` mostra apenas P8 + P10
- [ ] `grep "deps\|dependências\|Dependencies" docs/architecture/P19_*.md` mostra apenas P5 + P8 + P13
- [ ] Ambas state machines implementam exatamente os estados do CT
- [ ] Nenhum documento referencia "P2" ou "P3" como dependência
- [ ] P8 `PublisherHandoff` é referenciado por nome exato em ambos

---

*OMNIS Control Tower — Revisão concluída.*
*Status: BLOQUEADO. Aguardando correções dos documentos P17 e P19 antes de nova submissão.*
