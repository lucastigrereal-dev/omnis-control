# ONDA 6 — IMPLEMENTATION PLAN

> **Data:** 2026-05-13
> **Status:** APROVADO (R2) — Pronto para executar
> **Worktrees:** 2
> **Módulos:** P17 Delivery Portal, P19 Campaign Manager

---

## 1. WORKTREES

| # | Worktree Path | Branch | Módulo |
|---|---|---|---|
| 1 | `C:\Users\lucas\omnis-p17-delivery-portal` | `parallel/p17-delivery-portal` | P17 |
| 2 | `C:\Users\lucas\omnis-p19-campaign-manager` | `parallel/p19-campaign-manager` | P19 |

### Criação (PowerShell — executar da raiz do repo)

```powershell
. .\scripts\omnis_parallel.ps1
Test-OmnisClean
New-OmnisSafetyTag
Start-ClaudeWorktree -FrenteName "p17-delivery-portal"
Start-ClaudeWorktree -FrenteName "p19-campaign-manager"
Get-ClaudeWorktrees
```

---

## 2. ARQUIVOS PERMITIDOS POR FRENTE

### 2.1 P17 — Delivery Portal

```
src/delivery_portal/          # 4 arquivos
├── __init__.py
├── models.py
├── service.py
└── errors.py

tests/delivery_portal/        # 3 arquivos
├── __init__.py
├── test_models.py
├── test_service.py
└── test_errors.py            # opcional (pode fundir com test_models.py)

docs/delivery_portal/         # 1 arquivo (criado ao final)
└── P17_DELIVERY_PORTAL_SKELETON.md
```

**Total: 8 arquivos novos (máximo)**

### 2.2 P19 — Campaign Manager

```
src/campaign_manager/         # 4 arquivos
├── __init__.py
├── models.py
├── service.py
└── errors.py

tests/campaign_manager/       # 3 arquivos
├── __init__.py
├── test_models.py
├── test_service.py
└── test_contracts.py

docs/campaign_manager/        # 1 arquivo (criado ao final)
└── P19_CAMPAIGN_MANAGER_SKELETON.md
```

**Total: 8 arquivos novos (máximo)**

---

## 3. ARQUIVOS PROIBIDOS (ZERO TOQUES)

### 3.1 Legados — NUNCA modificar

```
src/client_delivery/
src/delivery_templates/
src/campaign_package/
src/campaign_auditor/
src/publisher/
src/argos_bridge/
src/execution_graph/
src/approval_center/
```

### 3.2 Módulos ativos — NUNCA modificar

```
src/publisher_argos/          # P8 — importar classes, nunca editar
src/sales_crm/                # P10 — importar classes, nunca editar
src/marketing/                # P5 — importar classes, nunca editar (só P19)
src/analytics/                # P13 — importar classes, nunca editar (só P19)
src/creative_production_v2/   # P2 — NEM importar
src/caption_approval_v2/      # P3 — NEM importar
src/observability_local/      # P16 — NEM importar
src/finance/                  # P14 — NEM importar
```

### 3.3 Runtime data — NUNCA commitar

```
data/
logs/
exports/
bundles/
```

---

## 4. CONTRATOS CONGELADOS

### 4.1 Imports P17 (exatamente estes)

```python
# Autorizados — APENAS estes 2 imports de módulos externos:
from src.publisher_argos.models import PublisherHandoff
from src.sales_crm.models import Deal

# Stdlib permitida:
import dataclasses, enum, uuid, datetime, json, hashlib, pathlib
```

### 4.2 Imports P19 (exatamente estes)

```python
# Autorizados — APENAS estes 3 imports de módulos externos:
from src.marketing.models import CampaignBrief, CampaignPackage, MarketingObjective, AudienceProfile
from src.publisher_argos.models import PublisherHandoff, ArgosExportItem, ArgosExportPackage
from src.analytics.models import MetricDefinition, MetricSummary

# Stdlib permitida:
import dataclasses, enum, uuid, datetime, json, hashlib, pathlib, collections
```

### 4.3 Imports PROIBIDOS (ambos)

```python
# Se qualquer um destes aparecer, FAIL imediato:
from src.creative_production_v2 import ...    # P2
from src.caption_approval_v2 import ...        # P3
from src.client_delivery import ...            # legado
from src.delivery_templates import ...         # legado
from src.campaign_package import ...           # legado
from src.campaign_auditor import ...           # legado
from src.execution_graph import ...            # legado
from src.approval_center import ...            # legado
from src.observability_local import ...        # P16
from src.finance import ...                    # P14
from src.delivery_portal import ...            # cross P17↔P19
from src.campaign_manager import ...           # cross P17↔P19
```

---

## 5. MODELOS E CLASSES POR FRENTE

### 5.1 P17 — Delivery Portal

#### Enum

```python
class DeliveryStatus(str, Enum):
    PENDING_DELIVERY = "pending_delivery"
    DELIVERED = "delivered"
    VIEWED = "viewed"
    FEEDBACK_RECEIVED = "feedback_received"
    CLOSED = "closed"
```

#### Dataclasses

| Classe | ID Prefix | Campos |
|---|---|---|
| `DeliveryPackage` | `pkg_` / `dlv_` | package_id, delivery_id, status, handoff (PublisherHandoff), deal (Deal), feedback (list[FeedbackItem]), created_at, created_by, dry_run, approval_required |
| `FeedbackItem` | `fbk_` | feedback_id, delivery_id, feedback_type (approved/adjustment/complaint/ack), comment, requires_revision, recorded_at, recorded_by |

#### Service

```python
class DeliveryPlanner:
    def __init__(self, dry_run: bool = True): ...
    def build_delivery_package(self, handoff: PublisherHandoff, deal: Deal) -> DeliveryPackage: ...
    def add_feedback(self, pkg: DeliveryPackage, feedback_type: str, comment: str) -> DeliveryPackage: ...
    def transition_state(self, pkg: DeliveryPackage, target: DeliveryStatus) -> DeliveryPackage: ...
```

#### Errors

```python
class DeliveryError(Exception): ...                    # base
class InvalidStateTransitionError(DeliveryError): ...  # transição inválida
class HandoffRejectedError(DeliveryError): ...         # handoff não validado
class DealNotClosedError(DeliveryError): ...           # deal != closed_won
```

### 5.2 P19 — Campaign Manager

#### Enum

```python
class CampaignStatus(str, Enum):
    DRAFT = "draft"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ANALYZED = "analyzed"
    ARCHIVED = "archived"
```

#### Dataclasses

| Classe | ID Prefix | Campos |
|---|---|---|
| `Campaign` | `cmp_` | campaign_id, campaign_name, brief_ref, status, channels, budget (BudgetTracker), roi (ROICalculation), metrics_plan, timeline, publish_queue_plan_ref, dry_run, approval_required, retry_count, error_message, tags |
| `BudgetTracker` | `bud_` | budget_id, campaign_ref, total_budget_brl, allocated_brl, spent_brl, breakdown (list[dict]), currency |
| `ROICalculation` | `roi_` | roi_id, campaign_ref, projected_revenue_brl, projected_cost_brl, projected_roi_percent, actual_revenue_brl, actual_cost_brl, actual_roi_percent, formula, calculated_at, notes |

#### Service

```python
class CampaignOrchestrator:
    def __init__(self, dry_run: bool = True): ...
    
    @staticmethod
    def orchestrate_campaign(brief: CampaignBrief) -> Campaign: ...
    
    @staticmethod
    def allocate_budget(campaign: Campaign, total: float, breakdown: list[dict]) -> BudgetTracker: ...
    
    @staticmethod
    def calculate_roi(campaign: Campaign, metrics: MetricSummary) -> ROICalculation: ...
    
    @staticmethod
    def transition_state(campaign: Campaign, target: CampaignStatus) -> Campaign: ...
    
    @staticmethod
    def build_publish_queue_plan(campaign: Campaign) -> dict: ...
    
    @staticmethod
    def generate_manifest(campaign: Campaign) -> dict: ...
```

#### Errors

```python
class CampaignError(Exception): ...              # base
class StateTransitionError(CampaignError): ...    # transição inválida
class BudgetError(CampaignError): ...             # budget inválido
class ROIError(CampaignError): ...                # ROI sem métricas
```

---

## 6. TESTES MÍNIMOS

| Módulo | Alvo | Arquivos de teste | Distribuição |
|---|---|---|---|
| P17 | **≥ 40** | 3 | test_models (15-20) + test_service (15-20) + test_errors (5-10) |
| P19 | **≥ 60** | 3 | test_models (25) + test_service (20) + test_contracts (15) |

### Comandos de validação

```powershell
# Dentro de cada worktree:
python -m pytest tests/delivery_portal/ -q     # P17 isolated (≥ 40)
python -m pytest tests/campaign_manager/ -q    # P19 isolated (≥ 60)
python -m pytest tests/ -q                      # Full suite no merge
```

---

## 7. ORDEM DE IMPLEMENTAÇÃO

### 7.1 Dentro de cada módulo (sequencial)

| Milestone | P17 | P19 |
|---|---|---|
| M1 | `models.py` + `errors.py` + `test_models.py` | `models.py` + `errors.py` + `test_models.py` |
| M2 | `service.py` + `test_service.py` | `service.py` + `test_service.py` |
| M3 | `__init__.py` + edge case tests | `__init__.py` + `test_contracts.py` |
| M4 | Skeleton doc + targeted suite | Skeleton doc + targeted suite |

### 7.2 Ordem de merge (sequencial, NUNCA paralelo)

| Ordem | Módulo | Justificativa |
|---|---|---|
| **1º** | P19 Campaign Manager | + dependências (3), + complexidade, + testes. Validar primeiro. |
| **2º** | P17 Delivery Portal | Mais simples (2 deps). Fecha a onda. |

### 7.3 Protocolo de merge

```
Merge 1 (P19):
  git checkout master
  git merge --no-ff parallel/p19-campaign-manager
  python -m pytest tests/campaign_manager/ -q   # targeted
  python -m pytest tests/ -q                      # full suite (deve passar sem quebras)

Merge 2 (P17):
  git checkout master
  git merge --no-ff parallel/p17-delivery-portal
  python -m pytest tests/delivery_portal/ -q     # targeted
  python -m pytest tests/ -q                      # full suite (deve passar sem quebras)
```

---

## 8. COMANDOS DE VALIDAÇÃO (POST-IMPLEMENTAÇÃO)

### Verificação de escopo

```powershell
# Confirmar que só delivery_portal/ e campaign_manager/ foram adicionados
git diff --stat master -- src/

# Confirmar que NENHUM legado foi tocado
git diff --stat master -- src/client_delivery/ src/delivery_templates/ src/campaign_package/ src/campaign_auditor/ src/publisher/ src/argos_bridge/ src/execution_graph/ src/approval_center/

# Confirmar que módulos ativos não foram modificados
git diff --stat master -- src/publisher_argos/ src/sales_crm/ src/marketing/ src/analytics/ src/creative_production_v2/ src/caption_approval_v2/
```

### Verificação de imports proibidos

```powershell
# P17 — NÃO deve conter referências a P2, P3, P5, P13, P19
Select-String -Path "src\delivery_portal\*.py" -Pattern "creative_production_v2|caption_approval_v2|marketing|analytics|campaign_manager|client_delivery|delivery_templates|approval_center|execution_graph"

# P19 — NÃO deve conter referências a P2, P3, P10, P17
Select-String -Path "src\campaign_manager\*.py" -Pattern "creative_production_v2|caption_approval_v2|sales_crm|delivery_portal|campaign_package|campaign_auditor|approval_center|execution_graph"
```

### Verificação de state machines

```powershell
# P17 — Deve conter exatamente 5 estados
Select-String -Path "src\delivery_portal\models.py" -Pattern "PENDING_DELIVERY|DELIVERED|VIEWED|FEEDBACK_RECEIVED|CLOSED"

# P19 — Deve conter exatamente 6 estados
Select-String -Path "src\campaign_manager\models.py" -Pattern "DRAFT|PLANNED|IN_PROGRESS|COMPLETED|ANALYZED|ARCHIVED"
```

---

## 9. CRITÉRIOS DE MERGE

Só executar merge quando TODOS forem verdade:

- [ ] P19 targeted tests ≥ 60 passando
- [ ] P17 targeted tests ≥ 40 passando
- [ ] Nenhum import proibido em P17 (`grep` limpo)
- [ ] Nenhum import proibido em P19 (`grep` limpo)
- [ ] Nenhum legado modificado (`git diff` limpo)
- [ ] Nenhum módulo ativo modificado (`git diff` limpo)
- [ ] State machines com contagem exata de estados (5 P17, 6 P19)
- [ ] dry_run=True e approval_required=True como defaults
- [ ] IDs com prefixos corretos (dlv_/pkg_/fbk_ para P17, cmp_/bud_/roi_ para P19)
- [ ] .new() + .to_dict() + .from_dict() + _now_iso() em todos os modelos
- [ ] Working tree limpo em cada worktree (commitado)
- [ ] Nenhum runtime data nos commits (data/, logs/, exports/, bundles/)

---

## 10. RISCOS RESTANTES

| # | Risco | Impacto | Mitigação |
|---|---|---|---|
| 1 | `PublisherHandoff.to_dict()` pode não serializar objetos aninhados como esperado | P17 build_delivery_package falha | Testar round-trip com handoff real do P8 no M2 |
| 2 | `CampaignBrief` pode não ter campo `channels` | P19 orchestrate_campaign precisa definir channels | Definir channels via argumento separado no service |
| 3 | `MetricSummary` pode não ter campos `avg`, `sum`, `count` como esperado | ROI calculation quebra | Verificar campos reais no `src/analytics/models.py` |
| 4 | Discrepância entre `datetime.utcnow()` deprecation warnings | Ruído no pytest output | Usar `datetime.now(timezone.utc)` como padrão |
| 5 | Worktrees não limpam corretamente no Windows (recorrente) | Bloqueia remoção pós-merge | `Remove-Item -Recurse -Force` + `git worktree prune` |

---

## 11. HANDOFF PARA CADA ABA DO CLAUDE CODE

### 11.1 Prompt — Aba P17 (Delivery Portal)

```
MISSÃO: Implementar skeleton do P17 Delivery Portal.

WORKTREE: C:\Users\lucas\omnis-p17-delivery-portal
BRANCH: parallel/p17-delivery-portal
DOCS DE REFERÊNCIA:
- docs/architecture/P17_DELIVERY_ARCHITECTURE.md
- docs/architecture/ONDA6_CONTROL_TOWER_PLAN.md (seções 3, 5, 10)
- docs/implementation/ONDA6_IMPLEMENTATION_PLAN.md

CRIAR ARQUIVOS (4 source + 3 test):

Source:
  src/delivery_portal/__init__.py
  src/delivery_portal/models.py
  src/delivery_portal/service.py
  src/delivery_portal/errors.py

Tests:
  tests/delivery_portal/__init__.py
  tests/delivery_portal/test_models.py
  tests/delivery_portal/test_service.py

IMPORTS AUTORIZADOS:
  from src.publisher_argos.models import PublisherHandoff
  from src.sales_crm.models import Deal

IMPORTS PROIBIDOS: P2, P3, P5, P13, P14, P16, P19, client_delivery, delivery_templates, approval_center, execution_graph

MODELS: DeliveryPackage (pkg_/dlv_), FeedbackItem (fbk_), DeliveryStatus enum (5 estados)
SERVICE: DeliveryPlanner com build_delivery_package(), add_feedback(), transition_state()
ERRORS: DeliveryError, InvalidStateTransitionError, HandoffRejectedError, DealNotClosedError

TESTES: ≥ 40 (models 15-20 + service 15-20 + errors 5-10)
PADRÃO: dry_run=True default, approval_required=True, .new() factory, to_dict()/from_dict(), _now_iso()

NÃO: criar handoff próprio, escrever em disco, criar ZIP/CSV, referenciar P19
```

### 11.2 Prompt — Aba P19 (Campaign Manager)

```
MISSÃO: Implementar skeleton do P19 Campaign Manager.

WORKTREE: C:\Users\lucas\omnis-p19-campaign-manager
BRANCH: parallel/p19-campaign-manager
DOCS DE REFERÊNCIA:
- docs/architecture/P19_CAMPAIGN_ARCHITECTURE.md
- docs/architecture/ONDA6_CONTROL_TOWER_PLAN.md (seções 4, 6, 11)
- docs/implementation/ONDA6_IMPLEMENTATION_PLAN.md

CRIAR ARQUIVOS (4 source + 3 test):

Source:
  src/campaign_manager/__init__.py
  src/campaign_manager/models.py
  src/campaign_manager/service.py
  src/campaign_manager/errors.py

Tests:
  tests/campaign_manager/__init__.py
  tests/campaign_manager/test_models.py
  tests/campaign_manager/test_service.py
  tests/campaign_manager/test_contracts.py

IMPORTS AUTORIZADOS:
  from src.marketing.models import CampaignBrief, CampaignPackage, MarketingObjective, AudienceProfile
  from src.publisher_argos.models import PublisherHandoff, ArgosExportItem, ArgosExportPackage
  from src.analytics.models import MetricDefinition, MetricSummary

IMPORTS PROIBIDOS: P2, P3, P10, P14, P16, P17, campaign_package, campaign_auditor, execution_graph, approval_center

MODELS: Campaign (cmp_), BudgetTracker (bud_), ROICalculation (roi_), CampaignStatus enum (6 estados)
SERVICE: CampaignOrchestrator (static methods) com orchestrate_campaign(), allocate_budget(), calculate_roi(), transition_state(), build_publish_queue_plan(), generate_manifest()
ERRORS: CampaignError, StateTransitionError, BudgetError, ROIError

TESTES: ≥ 60 (models 25 + service 20 + contracts 15)
PADRÃO: dry_run=True default, approval_required=True, .new() factory, to_dict()/from_dict(), _now_iso()
TOPOLOGICAL SORT: collections.deque stdlib inline (sem import de execution_graph)

NÃO: criar handoff próprio, importar P2/P3/P10/P17, criar ZIP, CLI commands, scheduler separado
```

---

## 12. PÓS-MERGE CLEANUP

```powershell
# 1. Validar legados intocados
git diff --stat master -- src/client_delivery/ src/delivery_templates/ src/campaign_package/ src/campaign_auditor/ src/publisher/ src/argos_bridge/

# 2. Criar tag final
git tag -a onda6-complete-20260513 -m "ONDA 6 complete: P17 Delivery Portal + P19 Campaign Manager skeletons"

# 3. Bundle
git bundle create bundles/omnis-onda6-complete-20260513.bundle master --tags

# 4. Remover worktrees (no Windows, usar force remove)
Remove-Item -Recurse -Force C:\Users\lucas\omnis-p17-delivery-portal -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force C:\Users\lucas\omnis-p19-campaign-manager -ErrorAction SilentlyContinue
git worktree prune

# 5. Remover branches
git branch -d parallel/p17-delivery-portal
git branch -d parallel/p19-campaign-manager

# 6. Push (COM APROVAÇÃO EXPLÍCITA)
git push origin master --tags
```

---

## 13. PROGRESSÃO ESPERADA

| Momento | Testes acumulados | Módulos | % |
|---|---|---|---|
| Pré-Onda 6 | 3740 | 18/20 | 90% |
| Pós-merge P19 | 3740 + ~60 = ~3800 | 19/20 | 95% |
| Pós-merge P17 | 3740 + ~60 + ~40 = ~3840 | 19/20 | 95% |
| **Pós-Onda 6** | **~3840** | **19/20** | **95%** |

---

*OMNIS Control Tower — Plano de implementação.*
*Pronto para executar. Aguardando comando: "Iniciar Onda 6 — P17 e P19."*
