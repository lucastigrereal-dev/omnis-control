# P17 Delivery Portal — Architecture

**Status:** draft (corrigido após ONDA 6 review)
**Date:** 2026-05-13
**Branch:** master
**Dependencies:** P8 Publisher/ARGOS, P10 Outputs / Mission Outputs
**Review:** ONDA 6 — CORREÇÕES APLICADAS

---

## 1. Definição da P17

P17 Delivery Portal é o módulo que transforma **handoffs do publisher** em **entregas rastreáveis ao cliente**.

Ela responde à pergunta: _"Como o OMNIS entrega aquilo que publicou?"_

A P17 encapsula o `PublisherHandoff` do P8, anexa metadados de deal do P10, e gerencia o ciclo de vida da entrega do momento em que o conteúdo foi publicado até o feedback do cliente.

**P17 é skeleton.** Não publica, não gera conteúdo, não decide estratégia, não faz ZIP.

---

## 2. Problema que resolve

Hoje o OMNIS publica (P8) e vende (P10), mas não existe uma camada que:

- **Registre** o que foi entregue para qual cliente, quando, em qual deal
- **Rastreie** se o cliente visualizou, se deu feedback
- **Encapsule** o handoff do publisher com metadados de negócio (deal, cliente, valor)
- **Feche** o ciclo — da publicação à confirmação do cliente

---

## 3. O que entra no módulo

| Entrada | Origem | Formato |
|---------|--------|---------|
| `PublisherHandoff` | P8 Publisher/ARGOS | `PublisherHandoff` (modelo P8) |
| `Deal` | P10 Outputs / Mission Outputs | `Deal` (deal fechado, cliente, valor) |

---

## 4. O que sai do módulo

| Saída | Destino | Formato |
|-------|---------|---------|
| `DeliveryPackage` | In-memory / `to_dict()` | Dataclass com handoff + deal + status |
| `FeedbackItem` | In-memory / `to_dict()` | Dataclass com feedback do cliente |
| `DeliveryStatus` | State machine interna | Enum 5 estados CT |

**Skeleton:** models são in-memory. Nada é escrito em disco nesta fase.

---

## 5. O que NÃO pertence ao módulo

| Proibição | Motivo |
|-----------|--------|
| Criar campanhas | Pertence a P19 Campaign |
| Decidir estratégia de marketing | Pertence a P5 Strategy |
| Gerar conteúdo ou legenda | Pertence a P2/P3 |
| Publicar no Instagram | Pertence a P8 Publisher |
| Chamar OAuth / Meta API | Bloqueio arquitetural |
| Criar ZIP/CSV/export | Feature futura — não skeleton |
| Criar handoff próprio | Handoff é do P8 — P17 encapsula |
| Referenciar `delivery_templates` | Legado proibido |
| Referenciar `approval_center` | Legado proibido |
| Referenciar `client_delivery` | Legado proibido |
| Referenciar P19 Campaign | P17 e P19 não se conhecem |
| Referenciar P2/P3 | Dependências não autorizadas |

---

## 6. Delivery Contract

Contrato que define o que constitui um `DeliveryPackage` válido. Validado em `DeliveryPlanner.build_delivery_package()`.

```json
{
  "contract_version": "1.0.0",
  "required_inputs": [
    {"key": "handoff", "type": "PublisherHandoff", "source": "P8"},
    {"key": "deal", "type": "Deal", "source": "P10"}
  ],
  "handoff_requirements": [
    {"field": "id", "nullable": false},
    {"field": "package", "nullable": false},
    {"field": "handed_off_at", "nullable": false},
    {"field": "dry_run", "must_be": false}
  ],
  "deal_requirements": [
    {"field": "deal_id", "nullable": false},
    {"field": "client_name", "nullable": false},
    {"field": "status", "valid_values": ["closed_won"]}
  ],
  "rules": [
    {"rule": "handoff_not_dry_run", "description": "Handoff deve ser real (dry_run=False)"},
    {"rule": "deal_closed", "description": "Deal deve estar fechado (closed_won)"},
    {"rule": "handoff_complete", "description": "PublisherHandoff contém package com itens exportados"}
  ]
}
```

---

## 7. Artifact Model

Modelo interno que referencia artefatos do `PublisherHandoff.package` (P8), sem redefini-los.

```json
{
  "artifact_ref": "art_4f8a2b1c",
  "source": "P8",
  "p8_export_item_id": "exp_abc123",
  "caption_snippet": "Meu post de viagem...",
  "channel": "instagram_feed",
  "handle": "lucastigrereal",
  "included_in_handoff": true
}
```

**Regra:** P17 NÃO redefine `ArtifactRecord`. Os artefatos já existem no `ArgosExportPackage` dentro do `PublisherHandoff`. A P17 referencia, não duplica.

---

## 8. Delivery Package Model

Modelo canônico da entrega. Encapsula handoff do P8 + deal do P10.

```json
{
  "package_id": "pkg_d7e3f1a9",
  "delivery_id": "dlv_9c2b4a1e",
  "status": "pending_delivery",
  "handoff": {
    "handoff_id": "ho_abc123",
    "handed_off_at": "2026-05-13T10:30:00Z",
    "package": {
      "label": "Collab Hotel Serra — @lucastigrereal",
      "items_count": 1,
      "export_status": "exported"
    }
  },
  "deal": {
    "deal_id": "deal_xyz789",
    "client_name": "Hotel Serra Bonita",
    "package_type": "growth",
    "monthly_value_brl": 990
  },
  "feedback": [],
  "created_at": "2026-05-13T10:30:00Z",
  "created_by": "local_user",
  "dry_run": false,
  "approval_required": true
}
```

---

## 9. Delivery States

Máquina de estados definida pela Control Tower. Exatamente 5 estados.

```
┌──────────────────┐
│ pending_delivery │  ← build_delivery_package()
└────────┬─────────┘
         │ handoff confirmed
         ▼
┌──────────────────┐
│    delivered     │  ← entrega enviada ao cliente
└────────┬─────────┘
         │ cliente abriu / visualizou
         ▼
┌──────────────────┐
│     viewed       │  ← cliente visualizou
└────────┬─────────┘
         │ cliente respondeu
         ▼
┌──────────────────┐
│ feedback_received│  ← feedback registrado
└────────┬─────────┘
         │ ciclo encerrado
         ▼
┌──────────────────┐
│     closed       │  ← entrega finalizada
└──────────────────┘
```

| Estado | Descrição | Quem transita |
|--------|-----------|---------------|
| `pending_delivery` | Package criado, handoff validado, aguardando confirmação de envio | `build_delivery_package()` |
| `delivered` | Enviado ao cliente (whatsapp, e-mail, link) | Operador / P8 |
| `viewed` | Cliente visualizou a entrega | Operador registra |
| `feedback_received` | Cliente deu feedback (positivo, ajuste, reclamação) | Operador registra `FeedbackItem` |
| `closed` | Ciclo encerrado (aprovado ou arquivado) | Operador |

### O que NÃO são estados:
- **Dry-run** — é operação de validação, não estado
- **Failed** — falhas são tratadas via retry, não como estado persistido
- **Exported** — export é ação, não estado
- **Archived** — archive é operação de infra, não estado de negócio

---

## 10. Relação com P8 Publisher/ARGOS

A P17 **encapsula** o `PublisherHandoff` do P8. Não redefine, não estende.

```
P8 Publisher/ARGOS                    P17 Delivery Portal
──────────────────                    ────────────────────
PublisherHandoff                      DeliveryPackage
├── id              ─────────────►    .handoff (objeto inteiro)
├── package                          .handoff.package
├── handed_off_at                    .handoff.handed_off_at
├── source_module                    .handoff.source_module
├── target_system                    .handoff.target_system
├── dry_run                          .handoff.dry_run
├── notes                            .handoff.notes
├── approval_required                .handoff.approval_required
└── approved_by                      .handoff.approved_by
```

### Import autorizado:

```python
from src.publisher_argos.models import PublisherHandoff
```

### Regras:
- P17 NUNCA modifica o `PublisherHandoff`
- P17 NUNCA cria handoff próprio
- `handoff.dry_run == True` → rejeita (só handoffs reais viram delivery)
- `handoff.approval_required == False` → rejeita
- `handoff.approved_by is None` → rejeita

---

## 11. Relação com P10 Outputs / Mission Outputs

A P17 **consome** `Deal` do P10 para anexar contexto de negócio ao delivery.

```
P10 Outputs / Mission Outputs         P17 Delivery Portal
────────────────────────────────      ────────────────────
Deal                                  DeliveryPackage
├── deal_id         ─────────────►    .deal.deal_id
├── client_name     ─────────────►    .deal.client_name
├── package_type    ─────────────►    .deal.package_type
├── value_brl       ─────────────►    .deal.monthly_value_brl
└── status          ─────────────►    check: status == "closed_won"
```

### Import autorizado:

```python
from src.sales_crm.models import Deal
```

### Regras:
- Só deals com `status == "closed_won"` geram delivery
- P17 NUNCA modifica o Deal
- P17 NUNCA cria deals
- O CRM gerencia Leads e Deals; a P17 apenas referencia

---

## 12. Pastas sugeridas

Estrutura skeleton — 4 arquivos core.

```
src/delivery_portal/
├── __init__.py          # exports: DeliveryPlanner, DeliveryPackage, DeliveryStatus, FeedbackItem
├── models.py            # DeliveryPackage, FeedbackItem, enums (DeliveryStatus)
├── service.py           # DeliveryPlanner — build_delivery_package(), add_feedback(), transition_state()
└── errors.py            # DeliveryError, InvalidStateTransitionError, HandoffRejectedError

tests/delivery_portal/
├── test_models.py       # 15-20 testes — instanciação, factories, to_dict/from_dict, enums
├── test_service.py      # 15-20 testes — build, feedback, state transitions
└── test_errors.py       # 5-10 testes — exceções, mensagens
```

**⚠️ aguardar validação da Control Tower** — Path `tests/delivery_portal/` (não `tests/test_delivery_portal.py`). Depende de decisão global de estrutura de tests/.

---

## 13. Classes sugeridas

### 13.1 Enum

```python
class DeliveryStatus(str, Enum):
    PENDING_DELIVERY = "pending_delivery"
    DELIVERED = "delivered"
    VIEWED = "viewed"
    FEEDBACK_RECEIVED = "feedback_received"
    CLOSED = "closed"
```

### 13.2 Data Classes (stdlib `dataclasses`)

| Classe | Descrição | Campos principais | ID prefix |
|--------|-----------|-------------------|-----------|
| `DeliveryPackage` | Entrega rastreável | `package_id`, `delivery_id`, `status: DeliveryStatus`, `handoff: PublisherHandoff`, `deal: Deal`, `feedback: list[FeedbackItem]`, `created_at`, `created_by`, `dry_run`, `approval_required` | `pkg_` / `dlv_` |
| `FeedbackItem` | Um feedback do cliente | `feedback_id`, `delivery_id`, `feedback_type`, `comment`, `requires_revision`, `recorded_at`, `recorded_by` | `fbk_` |

### 13.3 Services

| Classe | Método principal | Descrição |
|--------|-----------------|-----------|
| `DeliveryPlanner` | `build_delivery_package(handoff: PublisherHandoff, deal: Deal) → DeliveryPackage` | Valida contrato, constrói package, estado inicial = `pending_delivery` |
| `DeliveryPlanner` | `add_feedback(pkg: DeliveryPackage, feedback_type: str, comment: str) → DeliveryPackage` | Adiciona `FeedbackItem`, transita para `feedback_received` |
| `DeliveryPlanner` | `transition_state(pkg: DeliveryPackage, target: DeliveryStatus) → DeliveryPackage` | Valida transição, aplica novo estado |

### 13.4 Errors

| Classe | Descrição |
|--------|-----------|
| `DeliveryError` | Base exception |
| `InvalidStateTransitionError` | Transição de estado inválida |
| `HandoffRejectedError` | Handoff não passa validação (dry_run, sem aprovação) |
| `DealNotClosedError` | Deal não está em `closed_won` |

---

## 14. Fluxo operacional

Diagrama validado pela Control Tower (ONDA 6 §4):

```
P10 (Deal fechado) ──→ P8 (PublisherHandoff) ──→ P17 (DeliveryPackage)
    │                        │                          │
    └─ closed_won            └─ handed_off              └─ pending_delivery
                               └─ dry_run=False           └─ + Deal metadata
                               └─ approval_required       └─ + feedback loop
                               └─ approved_by != None

Ordem de execução: P10 (vender) → P8 (publicar) → P17 (entregar).
```

---

## 15. Feedback Model

`FeedbackItem` registra a resposta do cliente à entrega.

```json
{
  "feedback_id": "fbk_3a7c1e2d",
  "delivery_id": "dlv_9c2b4a1e",
  "feedback_type": "approved",
  "comment": "Ficou ótimo! Pode publicar mais 2 esse mês.",
  "requires_revision": false,
  "recorded_at": "2026-05-14T15:00:00Z",
  "recorded_by": "local_user"
}
```

### Feedback types

| Type | Descrição | Efeito |
|------|-----------|--------|
| `approved` | Cliente aprovou | Estado → `feedback_received`, sem revisão |
| `adjustment` | Cliente pede ajuste | Estado → `feedback_received`, `requires_revision=True` |
| `complaint` | Cliente reclamou | Estado → `feedback_received`, escalar |
| `ack` | Cliente acusou recebimento | Estado → `feedback_received`, neutro |

---

## 16. Dry-run strategy

Dry-run é **operação**, não estado.

### Comportamento no skeleton:
- `DeliveryPlanner.build_delivery_package()` aceita parâmetro `dry_run: bool = True`
- Quando `dry_run=True`:
  - Valida handoff + deal (contrato)
  - Constrói `DeliveryPackage` em memória com `dry_run=True`
  - Imprime resumo da validação
  - NÃO persiste, NÃO exporta, NÃO transita estado
- Quando `dry_run=False`:
  - Mesmo fluxo, mas `dry_run=False` no modelo
  - Estado inicial: `pending_delivery`

### Exemplo de output dry-run:

```
=== DRY-RUN: dlv_9c2b4a1e ===

Inputs:
  handoff:  ho_abc123  [VALID]  handed_off_at=2026-05-13T10:30:00Z
  deal:     deal_xyz789 [VALID]  status=closed_won, client=Hotel Serra Bonita

Contract checks:
  [PASS] handoff.package != None
  [PASS] handoff.dry_run == False
  [PASS] handoff.approval_required == True
  [PASS] handoff.approved_by == "local_user"
  [PASS] deal.status == "closed_won"

Initial state: pending_delivery
Feedback items: 0

=== DRY-RUN PASSED ===
```

---

## 17. Edge cases

| # | Cenário | Comportamento esperado |
|---|---------|----------------------|
| 1 | Handoff com `dry_run=True` | `HandoffRejectedError` — só handoff real vira delivery |
| 2 | Handoff sem `approved_by` | `HandoffRejectedError` — exige aprovação |
| 3 | Deal não está `closed_won` | `DealNotClosedError` — só deal fechado gera delivery |
| 4 | Transição `pending_delivery → viewed` (pula delivered) | `InvalidStateTransitionError` |
| 5 | Transição `closed → feedback_received` | `InvalidStateTransitionError` — fechado não reabre |
| 6 | Múltiplos feedbacks no mesmo delivery | OK — `feedback` é lista |
| 7 | Mesmo handoff + deal buildado 2x | OK — `delivery_id` único, `package_id` compartilhado |
| 8 | Feedback com `requires_revision=True` | Não transita para `closed` — aguarda novo handoff |
| 9 | `DeliveryPackage.to_dict()` com objetos aninhados | Serializa handoff e deal via `.to_dict()` deles |

---

## 18. Test strategy

### Alvo: 40-50 testes (skeleton)

| Categoria | Quantidade | Foco |
|-----------|------------|------|
| **Model tests** | 15-20 | `DeliveryPackage.new()`, `.to_dict()`, `.from_dict()`, defaults; `FeedbackItem`; `DeliveryStatus` enum |
| **Service tests** | 15-20 | `build_delivery_package()` com handoff+deal válidos; rejeição de handoff dry-run; rejeição de deal não fechado; `add_feedback()`; `transition_state()` |
| **Error tests** | 5-10 | Todas as exceções com mensagens; cobertura de construtores |

### Princípios:
- Zero dependências externas
- Mocks: `PublisherHandoff` e `Deal` instanciados via `.new()` nos testes
- State machine testada para todas as transições válidas **e** inválidas
- Dry-run testado verificando que `dry_run=True` no modelo, sem side effects
- NUNCA usar API real, disco, ou rede

---

## 19. Critérios de aceite

- [ ] Pasta `src/delivery_portal/` (nome exato)
- [ ] Models: `DeliveryPackage`, `DeliveryStatus` (enum 5 estados CT), `FeedbackItem`
- [ ] Service: `DeliveryPlanner` com `build_delivery_package(handoff: PublisherHandoff, deal: Deal) → DeliveryPackage`
- [ ] Imports: APENAS `src/publisher_argos/models.py` + `src/sales_crm/models.py`
- [ ] NÃO importa: P2, P3, P5, P13, P19, `client_delivery`, `delivery_templates`, `approval_center`, `execution_graph`
- [ ] `dry_run: True`, `approval_required: True`
- [ ] IDs prefixo `dlv_`, `pkg_`, `fbk_`
- [ ] `.new()` + `.to_dict()` + `.from_dict()` + `_now_iso()`
- [ ] Testes: ≥ 40 passando em `tests/delivery_portal/`
- [ ] State machine: 5 estados exatos, transições válidas e bloqueio de inválidas
- [ ] Nenhuma escrita em disco (models in-memory no skeleton)

---

## 20. Plano incremental de implementação

### Milestone 1: Models + Enums + Errors (dia 1)
- `models.py` — `DeliveryPackage`, `FeedbackItem`, `DeliveryStatus`
- `errors.py` — 4 exceções
- Testes: 15-20 model tests + 5-10 error tests
- **Dependências:** P8 (`PublisherHandoff`), P10 (`Deal`)

### Milestone 2: Service + State Machine (dia 2)
- `service.py` — `DeliveryPlanner` com 3 métodos
- State machine interna: valida transições, bloqueia inválidas
- Testes: 15-20 service tests
- **Dependências:** M1

### Milestone 3: Dry-run + Integração (dia 3)
- Dry-run executado via `build_delivery_package(dry_run=True)`
- Teste de integração: fluxo build → feedback → close
- Testes adicionais: 5-10
- **Dependências:** M2

### Milestone 4: Test Suite Final + Seal (dia 4)
- Suite completa: 40-50 testes passando
- Cobertura de state machine = 100% (transições válidas + inválidas)
- Arquivo `P17_FINAL_SEAL_REPORT.md`

---

## 21. Resubmission Notes

### O que foi corrigido (11 correções obrigatórias aplicadas):

| # | Correção | Status |
|---|----------|--------|
| 1 | Namespace: `delivery_engine` → `delivery_portal` | ✅ `src/delivery_portal/` |
| 2 | Dependências: removidas P2, P3 — apenas P8 + P10 | ✅ |
| 3 | Removida toda referência a `delivery_templates` | ✅ Zero menções |
| 4 | P10 renomeado: "Approval Center" → "Outputs / Mission Outputs" | ✅ |
| 5 | State machine: 8 estados → 5 estados CT (`pending_delivery → delivered → viewed → feedback_received → closed`) | ✅ |
| 6 | Handoff: removido `HandoffReceipt` próprio → encapsula `PublisherHandoff` do P8 | ✅ |
| 7 | Escopo: 12 arquivos → 4 arquivos core (models, service, errors, `__init__`) | ✅ |
| 8 | Testes: 160-200 → 40-50 | ✅ |
| 9 | Removida seção 15 (P19 Campaign) — P17 não conhece Campaign | ✅ |
| 10 | Removida seção CLI commands (feature, não skeleton) | ✅ |
| 11 | Removido acoplamento `delivery_templates` (brand_kit, delivery_template) | ✅ |

### O que foi removido:

- Seção "Relação com P2 Creative Production" (inteira)
- Seção "Relação com P3 Caption Approval" (inteira)
- Seção "Relação futura com P19 Campaign" (inteira)
- Seção "CLI commands sugeridos" (inteira)
- Seção "Logs e observabilidade" (reduzida — logs são feature)
- Seção "Failure/retry model" (reduzida — retry é feature)
- Modelos: `ArtifactRecord`, `ExportManifest`, `DeliverySource`, `DeliveryTarget`, `HandoffReceipt`, `DeliveryContract`, `ContractViolation`, `RetryPolicy`, `ExportResult`, `DryRunReport`, `DeliveryLogEntry`
- Services: `DeliveryContractValidator`, `DeliveryBuilder`, `DeliveryExporter`, `HandoffManager`, `ArtifactRegistry`, `DeliveryStateMachine`, `RetryRunner`, `DeliveryArchiver`, `DryRunRunner`, `DeliveryLogger`
- Enums: `ArtifactType`, `DeliveryFormat`, `ExportFormat`, `HandoffStatus`
- Todos os paths de `data/deliveries/`
- Todos os paths de `data/exports/`

### Decisões que aguardam a Control Tower:

| # | Decisão | Impacto |
|---|---------|---------|
| 1 | Schema final do `PublisherHandoff` (P8 em auditoria) | Afeta `DeliveryPlanner.build_delivery_package()` |
| 2 | Schema final do `Deal` (P10 em auditoria) | Afeta validação `deal.status == "closed_won"` |
| 3 | Estrutura de `tests/` (módulo vs. arquivo único) | Afeta path `tests/delivery_portal/` |
| 4 | Contrato de IDs compartilhados (P8, P10, P17) | Afeta prefixos `dlv_`, `pkg_`, `fbk_` |
| 5 | P20 Supreme — ponte P17↔P19 futura | P17 e P19 permanecem isolados |

---

## Resumo pós-correção

**Arquivo:** `docs/architecture/P17_DELIVERY_ARCHITECTURE.md`

**Principais mudanças:**
- Namespace `delivery_portal` (exato CT)
- Dependências reduzidas a P8 + P10 apenas
- State machine de 5 estados CT (sem exported, failed, archived, accepted/rejected)
- `PublisherHandoff` encapsulado, não redefinido
- Escopo skeleton: 4 arquivos, 40-50 testes, zero escrita em disco
- Todo acoplamento com P2, P3, P19, delivery_templates, approval_center removido

**Riscos remanescentes:**
- 5 decisões aguardam consolidação da Control Tower (schemas P8/P10, tests/, IDs, P20)
- P10 como "Outputs / Mission Outputs" vs. "Sales CRM" — nome conceitual aguarda alinhamento final

**Próximo passo:**
Re-submeter à Control Tower para aprovação pós-correção.
