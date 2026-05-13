# P20 — OMNIS SUPREME ACTIVATION ARCHITECTURE

> **Data:** 2026-05-13
> **Status:** DRAFT — Aguardando revisão
> **Onda:** Final (pós-Onda 6)
> **Base:** master `de22369` (20/20 módulos, 3938 testes)

---

## 1. DEFINIÇÃO DA P20

P20 OMNIS Supreme é a **camada de orquestração fina** que transforma 20 módulos isolados em um fluxo de execução por missão. Ela NÃO é um módulo de domínio — é um **condutor de orquestra** que recebe uma requisição em linguagem natural do operador e roteia pelos módulos existentes sem duplicar lógica de negócio.

```
User Request → Supreme Intake → Supreme Plan → Supreme Execute → Supreme Report
```

Diferente dos módulos P1-P19 (que modelam domínios: conteúdo, CRM, publishing, etc.), a P20 modela o **ciclo de vida de uma missão**.

---

## 2. O QUE A P20 DEVE FAZER

1. **Mission Intake** — receber requisição em linguagem natural, classificar intenção, setor, objetivo
2. **Context Builder** — montar contexto multi-fonte (memória, analytics, briefing, campanhas ativas)
3. **Mission Planner** — decompor requisição em passos, dependências, módulos necessários
4. **Capability/Skill Matcher** — mapear intenção → capabilities disponíveis nos 20 módulos
5. **Squad/Module Selection** — selecionar quais módulos participam da missão
6. **Execution Plan** — gerar DAG de passos com dependências (via execution_graph)
7. **Dry Run** — executar plano em modo simulação, gerar previsão de outputs
8. **Approval Gate** — submeter plano ao operador para aprovação (via governance)
9. **Execute** — executar passos aprovados, capturar outputs
10. **Delivery Package** — empacotar outputs para entrega (via delivery_portal)
11. **Campaign/Publisher/Handoff** — quando aplicável, orquestrar campanha → publishing (P19→P8→P17)
12. **Observability** — traçar cada passo, métricas, logs (via observability_local)
13. **Final Report** — gerar relatório consolidado da missão
14. **Learning Notes** — persistir aprendizados para memória (via memory_pack)

---

## 3. O QUE A P20 NÃO DEVE FAZER

| PROIBIDO | Motivo |
|---|---|
| Criar modelos de campanha próprios | P19 já tem `Campaign`, `BudgetTracker`, `ROICalculation` |
| Criar modelos de entrega próprios | P17 já tem `DeliveryPackage`, `FeedbackItem` |
| Criar modelos de publishing próprios | P8 já tem `PublisherHandoff`, `ArgosExportPackage` |
| Criar approval engine próprio | P18 já tem `ApprovalPolicyEngine`, `ScopeGuard` |
| Criar observability do zero | P16 já tem `TraceEvent`, `MetricPoint`, `ObservabilitySnapshot` |
| Criar memory/context do zero | P4 já tem `ContextPack`, `MissionMemoryRecord` |
| Criar CRM próprio | P10 já tem `Deal`, `Lead`, `SalesPipeline` |
| Criar analytics próprio | P13 já tem `MetricDefinition`, `MetricSummary` |
| Tornar-se um God Module | P20 deve ter < 500 linhas de lógica própria |
| Acoplar módulos diretamente | Sempre via contratos (imports de models, nunca edição) |
| Tocar em OAuth real | Sem credenciais, sem tokens |
| Publicar sem approval | `approval_required=True` como default inegociável |
| Quebrar boundaries dos módulos | P20 lê exports, nunca importa módulos internos |

---

## 4. FLUXO SUPREME END-TO-END

```
┌─────────────────────────────────────────────────────────────────────┐
│                    P20 SUPREME MISSION FLOW                         │
│                                                                     │
│  [1] User Request (natural language)                                │
│       │                                                             │
│       ▼                                                             │
│  [2] SupremeIntake.parse(request) → MissionIntent                  │
│       │                                                             │
│       ▼                                                             │
│  [3] SupremeContext.build(intent) → SupremeContext                 │
│       │  ├─ memory_pack (P4): top hooks, padrões virais            │
│       │  ├─ analytics (P13): métricas recentes                     │
│       │  └─ marketing (P5): briefings ativos, audiências          │
│       │                                                             │
│       ▼                                                             │
│  [4] SupremePlanner.plan(context) → SupremePlan                    │
│       │  ├─ Decompõe em passos                                     │
│       │  ├─ Seleciona módulos (squad)                              │
│       │  └─ Gera DAG (execution_graph)                             │
│       │                                                             │
│       ▼                                                             │
│  [5] SupremeExecutor.dry_run(plan) → DryRunReport                  │
│       │  ├─ Simula cada passo                                      │
│       │  ├─ Gera previsão de outputs                               │
│       │  └─ Detecta blockers/warnings                              │
│       │                                                             │
│       ▼                                                             │
│  [6] SupremeApprovalGate.submit(plan, dry_run) → Decision          │
│       │  ├─ governance (P18): ApprovalPolicyEngine                 │
│       │  └─ Operador aprova/rejeita/ajusta                         │
│       │                                                             │
│       ▼ (se aprovado)                                              │
│  [7] SupremeExecutor.execute(plan) → ExecutionResult               │
│       │  ├─ Passo a passo com tracing                              │
│       │  ├─ observability_local (P16): TraceEvent por passo        │
│       │  └─ Captura outputs de cada módulo                         │
│       │                                                             │
│       ▼                                                             │
│  [8] SupremeDelivery.build(result) → DeliveryPackage               │
│       │  └─ delivery_portal (P17): DeliveryPlanner                 │
│       │                                                             │
│       ▼                                                             │
│  [9] SupremeReporter.generate(result) → MissionReport              │
│       │  ├─ Métricas, outputs, decisões                            │
│       │  └─ Learning notes → memory_pack (P4)                      │
│       │                                                             │
│       ▼                                                             │
│  [10] COMPLETE ──→ Próxima missão                                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. CONTRATO DE MISSÃO SUPREMA

### 5.1 SupremeMission (modelo central)

```python
@dataclass
class SupremeMission:
    mission_id: str          # "spr_<8hex>"
    request_text: str        # "cria campanha de viagem fim de ano"
    intent: str              # "create_campaign" | "publish_content" | "deliver_to_client" | ...
    sector: str              # "midia", "comercial", "vendas", ...
    status: SupremeStatus    # enum (7 estados — ver seção 14)
    context: dict            # SupremeContext serializado
    plan: dict               # SupremePlan serializado (DAG)
    execution: dict          # ExecutionResult serializado
    delivery: Optional[dict] # DeliveryPackage serializado
    report: Optional[dict]   # MissionReport serializado
    trace_events: list[dict] # TraceEvent[] do P16
    approval_decisions: list[dict]  # GovernanceDecision[] do P18
    warnings: list[str]
    blockers: list[str]
    dry_run: bool            # default True
    approval_required: bool  # default True
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
```

### 5.2 Contrato de imports (congelado)

```python
# AUTORIZADOS — apenas estes 6 módulos:
from src.mission.models import MissionContext, MissionPackage
from src.marketing.models import CampaignBrief, CampaignPackage
from src.publisher_argos.models import PublisherHandoff, PublishQueuePlan
from src.delivery_portal.models import DeliveryPackage, FeedbackItem
from src.campaign_manager.models import Campaign, CampaignStatus
from src.governance.models import ApprovalPolicy, GovernanceDecision
from src.observability_local.models import TraceEvent, MetricPoint
from src.memory_pack.models import ContextPack, MissionMemoryRecord
from src.analytics.models import MetricSummary

# PROIBIDOS — NUNCA importar:
from src.creative_production_v2 import ...   # P2 — domínio criativo
from src.caption_approval_v2 import ...       # P3 — domínio caption
from src.sales_crm import ...                 # P10 — domínio vendas (P17 já encapsula)
from src.finance import ...                   # P14 — domínio financeiro (P19 já encapsula)
from src.computer_ops import ...              # P15 — domínio infra
from src.content_scheduler import ...         # P1 — domínio conteúdo
# ... e qualquer módulo não listado nos autorizados
```

---

## 6. SUPREME EXECUTION PLAN

O plano de execução é um **DAG de passos** onde cada nó representa uma operação atômica em um módulo existente.

```python
@dataclass
class SupremePlan:
    plan_id: str               # "plan_<8hex>"
    mission_id: str
    steps: list[SupremeStep]   # nós do DAG
    edges: list[tuple[str, str]]  # (from_step_id, to_step_id)
    selected_modules: list[str]   # ["P5", "P19", "P8", "P17"]
    estimated_duration: str       # "15min"
    dry_run: bool
    generated_at: str

@dataclass
class SupremeStep:
    step_id: str               # "step_<6hex>"
    module_ref: str            # "P19" | "P17" | "P8" | "P5" | ...
    operation: str             # "orchestrate_campaign" | "build_delivery_package" | ...
    input_from: list[str]      # step_ids de entrada
    output_to: list[str]       # step_ids que consomem este output
    status: str                # pending | ready | running | done | failed | skipped
    config: dict               # parâmetros da operação
    result: Optional[dict]     # output da operação
```

### Exemplo de plano para "criar campanha de Natal para Cliente X":

```
Step 1: P5  — build_campaign_brief      → brief
Step 2: P19 — orchestrate_campaign      ← brief  → campaign
Step 3: P19 — allocate_budget            ← campaign → budget
Step 4: P19 — build_publish_queue_plan   ← campaign → queue_plan
Step 5: P8  — validate_publish_readiness ← queue_plan → readiness
Step 6: P17 — build_delivery_package     ← campaign, queue_plan → delivery
Step 7: P17 — add_feedback (se aplicável)
```

---

## 7. RELAÇÃO COM OS 20 MÓDULOS

P20 conhece cada módulo **apenas pela superfície pública** (`__init__.py` exports). Nunca acessa internals.

| Módulo | Como P20 usa | Método de integração |
|---|---|---|
| P1 content_scheduler | Define janelas de publicação | Importa models, chama Planner |
| P2 creative_production_v2 | NUNCA diretamente | Via P19 (campaign → criativos) |
| P3 caption_approval_v2 | NUNCA diretamente | Via P19 (campaign → captions) |
| P4 memory_pack | Constrói contexto, salva aprendizados | `ContextPack`, `MissionMemoryRecord` |
| P5 marketing | Fonte de briefings, audiências | `CampaignBrief`, `AudienceProfile` |
| P6 design_art | NUNCA diretamente | Via P19 |
| P7 video_studio | NUNCA diretamente | Via P19 |
| P8 publisher_argos | Valida readiness, handoff final | `PublisherHandoff`, `PublishQueuePlan` |
| P9 commercial_sdr | Contexto de prospecção (leitura) | `SDRPlan` (read-only) |
| P10 sales_crm | Contexto de deals (leitura) | Via P17 (P17 encapsula P10) |
| P11 app_factory | NUNCA diretamente | Fora do escopo Supreme |
| P12 automation | NUNCA diretamente | Workflows são domain-specific |
| P13 analytics | Métricas para contexto e ROI | `MetricSummary`, `MetricDefinition` |
| P14 finance | NUNCA diretamente | Via P19 (budget/ROI) |
| P15 computer_ops | NUNCA diretamente | Infra, não missão |
| P16 observability_local | Tracing de cada passo | `TraceEvent`, `MetricPoint`, `ObservabilitySnapshot` |
| P18 governance | Approval gates, política de risco | `ApprovalPolicyEngine`, `ScopeGuard`, `GovernanceDecision` |
| P17 delivery_portal | Empacotar outputs para cliente | `DeliveryPlanner`, `DeliveryPackage` |
| P19 campaign_manager | Orquestrar campanhas | `CampaignOrchestrator`, `Campaign` |

**Regra de ouro:** P20 só conhece P5, P8, P13, P17, P19, P4, P16, P18 diretamente. Os 12 módulos restantes são acessados **via delegação** (P19 orquestra P2/P3/P6/P7, P17 encapsula P10).

---

## 8. COMO P20 CHAMA MÓDULOS SEM ACOPLAR DEMAIS

### Padrão: Adapter Method em cada step

P20 nunca chama `CampaignOrchestrator.orchestrate_campaign()` diretamente no corpo da Supreme. Em vez disso, cada step tem um **adapter method** que traduz o contrato do step para a chamada real do módulo:

```python
class SupremeExecutor:
    """Executa um SupremePlan passo a passo."""

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.tracer = ObservabilityTracer()  # wrapper P16

    def execute_step(self, step: SupremeStep, context: dict) -> dict:
        # 1. Traduz step → chamada real
        adapter = self._get_adapter(step.module_ref, step.operation)

        # 2. Traça início
        trace = self.tracer.start_span(step.step_id, step.operation)

        try:
            # 3. Executa (dry ou real)
            result = adapter(step.config, context)

            # 4. Traça sucesso
            trace.ok(result)
            return result

        except Exception as e:
            # 5. Traça falha
            trace.fail(e)
            raise

    def _get_adapter(self, module_ref: str, operation: str):
        """Registry de adapters — um por operação suportada."""
        return ADAPTER_REGISTRY[(module_ref, operation)]


# Registry centralizado (extensível)
ADAPTER_REGISTRY = {
    ("P5", "build_campaign_brief"): lambda cfg, ctx: MarketingPlanner.build_campaign_brief(**cfg),
    ("P19", "orchestrate_campaign"): lambda cfg, ctx: CampaignOrchestrator.orchestrate_campaign(cfg["brief"]),
    ("P19", "allocate_budget"): lambda cfg, ctx: CampaignOrchestrator.allocate_budget(cfg["campaign"], cfg["total"], cfg["breakdown"]),
    ("P19", "calculate_roi"): lambda cfg, ctx: CampaignOrchestrator.calculate_roi(cfg["campaign"], cfg["metrics"]),
    ("P8", "validate_publish_readiness"): lambda cfg, ctx: PublisherArgosPlanner.validate_readiness(cfg["handoff"]),
    ("P17", "build_delivery_package"): lambda cfg, ctx: DeliveryPlanner(dry_run=cfg.get("dry_run", True)).build_delivery_package(cfg["handoff"], cfg["deal"]),
    # ... extensível para novas operações
}
```

**Por que adapters em vez de chamadas diretas?**
- Desacopla P20 da API interna de cada módulo
- Permite mock/teste isolado de cada step
- Facilita trocar módulo sem reescrever P20
- Registro centralizado = visibilidade total do que P20 pode fazer

---

## 9. COMO USAR P17 DELIVERY PORTAL

P20 chama P17 apenas na **fase final** da missão, quando há outputs para entregar a um cliente/deal.

```python
# Fluxo: P20 → P17 (via adapter)
def _build_delivery_from_mission(mission: SupremeMission) -> DeliveryPackage:
    """Constrói DeliveryPackage a partir de uma SupremeMission completa."""
    planner = DeliveryPlanner(dry_run=mission.dry_run)

    # P20 prepara os inputs que P17 exige
    handoff = _extract_handoff_from_plan(mission.plan)  # PublisherHandoff do P8
    deal = _extract_deal_from_context(mission.context)    # Deal do P10

    pkg = planner.build_delivery_package(handoff=handoff, deal=deal)

    # Se missão tem resultado de campanha, anexa como contexto
    if mission.plan.get("campaign_result"):
        pkg.metadata["campaign_context"] = mission.plan["campaign_result"]

    return pkg
```

**P20 NUNCA:**
- Cria `DeliveryPackage` diretamente (`.new()` é do P17)
- Define estados de entrega (P17 é dono da state machine)
- Gera ZIP/CSV (P17 pode fazer isso no futuro)
- Referencia P19 dentro do contexto de P17 (isolamento mantido)

---

## 10. COMO USAR P19 CAMPAIGN MANAGER

P20 chama P19 quando a missão envolve **criação/gestão de campanha**.

```python
# Fluxo: P20 → P19 (via adapter)
def _orchestrate_campaign_from_mission(mission: SupremeMission) -> Campaign:
    """Orquestra campanha a partir de uma SupremeMission."""
    brief = _extract_brief_from_context(mission.context)  # CampaignBrief do P5

    # P19 faz toda a orquestração interna
    campaign = CampaignOrchestrator.orchestrate_campaign(brief=brief)

    # P20 NÃO interfere no ciclo de vida da campanha
    # P19 é dono dos estados: DRAFT → PLANNED → ... → ARCHIVED

    # P20 apenas gera o manifest para consumo downstream
    manifest = CampaignOrchestrator.generate_manifest(campaign)
    mission.plan["campaign_manifest"] = manifest

    return campaign
```

**P20 NUNCA:**
- Gerencia transições de estado da campanha (P19 é dono)
- Aloca budget diretamente (chama `allocate_budget()` do P19)
- Calcula ROI diretamente (chama `calculate_roi()` do P19)
- Cria briefings (P5 é dono dos briefings)

---

## 11. COMO USAR CAPABILITY FORGE

A P20 NÃO integra o Capability Forge diretamente no fluxo principal. O Forge é uma ferramenta de **desenvolvimento** (cria novas capabilities), não de **execução** (usa capabilities existentes).

```python
# Integração FUTURA (pós-skeleton):
# Quando SupremePlanner encontra uma intenção sem módulo correspondente:
if not matched_modules:
    gap = CapabilityGap(
        intent=mission.intent,
        description=f"Nenhum módulo cobre '{mission.request_text}'",
        suggested_capability=mission.request_text,
    )
    mission.warnings.append(f"Capability gap detectado: {gap.description}")
    mission.suggested_gap_ids.append(gap.gap_id)
    # NÃO chama o Forge automaticamente — operador decide
```

**Para o skeleton:**
- Forge NÃO é importado
- Gaps são registrados como warnings
- Resolução de gaps é manual (operador decide criar capability)

---

## 12. COMO USAR OBSERVABILIDADE

P16 `observability_local` fornece tracing e métricas. P20 cria um **wrapper fino** que instrumenta cada step:

```python
class ObservabilityTracer:
    """Wrapper P16 para tracing de passos Supreme."""

    def __init__(self, mission_id: str):
        self.mission_id = mission_id
        self.events: list[TraceEvent] = []

    def start_span(self, step_id: str, operation: str) -> "Span":
        event = TraceEvent.new(
            trace_id=f"trace_{self.mission_id}",
            span_id=step_id,
            parent_span_id=None,  # root span
            operation=operation,
            module="P20",
        )
        return Span(event, self)

    def flush(self) -> ObservabilitySnapshot:
        return ObservabilitySnapshot(
            snapshot_id=f"snap_{_now_iso()}",
            mission_id=self.mission_id,
            events=self.events,
            metrics=[],  # preenchido durante execução
        )


class Span:
    def __init__(self, event: TraceEvent, tracer: ObservabilityTracer):
        self.event = event
        self.tracer = tracer
        self.event.metadata["started_at"] = _now_iso()

    def ok(self, result: dict) -> None:
        self.event.metadata["status"] = "ok"
        self.event.metadata["completed_at"] = _now_iso()
        self.tracer.events.append(self.event)

    def fail(self, error: Exception) -> None:
        self.event.metadata["status"] = "failed"
        self.event.metadata["error"] = str(error)
        self.event.metadata["completed_at"] = _now_iso()
        self.tracer.events.append(self.event)
```

---

## 13. COMO USAR APPROVAL GATES

P18 `governance` fornece o motor de políticas. P20 integra approval em **2 pontos**:

### Gate 1: Pré-execução (aprovação do plano)
```python
def _gate_plan_approval(plan: SupremePlan, context: dict) -> GovernanceDecision:
    engine = ApprovalPolicyEngine()
    scope = ScopeGuard(
        allowed_modules=plan.selected_modules,
        blocked_modules=[],
    )

    # Classifica risco do plano
    risk = RiskClassifier.classify(
        action_types=["write", "send"],
        modules_involved=plan.selected_modules,
    )

    # Avalia contra políticas
    decision = engine.evaluate(
        action="execute_mission",
        risk_level=risk.level,
        scope=scope,
        dry_run=plan.dry_run,
    )

    return decision  # approved | denied | requires_approval
```

### Gate 2: Pré-entrega (antes de gerar DeliveryPackage)
```python
def _gate_delivery_approval(result: ExecutionResult) -> GovernanceDecision:
    engine = ApprovalPolicyEngine()

    # Entrega é risco HIGH (ação SEND)
    decision = engine.evaluate(
        action="send",
        risk_level=RISK_HIGH,
        scope=ScopeGuard(allowed_modules=["P17"], blocked_modules=[]),
        dry_run=result.dry_run,
    )

    return decision
```

**Fluxo de approval:**
```
Plan Gerado → Gate 1 → [APPROVED] → Execute → [DONE] → Gate 2 → [APPROVED] → Delivery
                     → [DENIED] → abortar missão                  → [DENIED] → volta pra ajustes
                     → [REQUIRES_APPROVAL] → solicita operador
```

---

## 14. ESTADOS DA SUPREME MISSION

```python
class SupremeStatus(str, Enum):
    INTAKE = "intake"              # Requisição recebida, classificando
    CONTEXT_BUILDING = "context_building"  # Montando contexto
    PLANNING = "planning"          # Gerando plano
    DRY_RUN = "dry_run"            # Simulando execução
    AWAITING_APPROVAL = "awaiting_approval"  # Plano submetido ao operador
    EXECUTING = "executing"        # Executando passos aprovados
    COMPLETED = "completed"        # Missão concluída
    FAILED = "failed"              # Falha irrecuperável
    CANCELLED = "cancelled"        # Cancelada pelo operador

VALID_SUPREME_TRANSITIONS = {
    SupremeStatus.INTAKE: {SupremeStatus.CONTEXT_BUILDING, SupremeStatus.CANCELLED},
    SupremeStatus.CONTEXT_BUILDING: {SupremeStatus.PLANNING, SupremeStatus.FAILED},
    SupremeStatus.PLANNING: {SupremeStatus.DRY_RUN, SupremeStatus.FAILED},
    SupremeStatus.DRY_RUN: {SupremeStatus.AWAITING_APPROVAL, SupremeStatus.PLANNING, SupremeStatus.FAILED},
    SupremeStatus.AWAITING_APPROVAL: {SupremeStatus.EXECUTING, SupremeStatus.PLANNING, SupremeStatus.CANCELLED},
    SupremeStatus.EXECUTING: {SupremeStatus.COMPLETED, SupremeStatus.FAILED},
    SupremeStatus.COMPLETED: set(),        # terminal
    SupremeStatus.FAILED: {SupremeStatus.PLANNING},   # retry via replan
    SupremeStatus.CANCELLED: set(),        # terminal
}
```

**9 estados, transições validadas.** Estados terminais: COMPLETED, CANCELLED. FAILED permite retry.

---

## 15. ESTRUTURA DE PASTAS SUGERIDA

```
src/omnis_supreme/              # P20 namespace
├── __init__.py                 # exports públicos
├── models.py                   # SupremeMission, SupremePlan, SupremeStep, SupremeStatus
├── service.py                  # SupremeIntake, SupremePlanner, SupremeExecutor
├── adapters.py                 # ADAPTER_REGISTRY — ponte para P5/P8/P17/P19
├── tracer.py                   # ObservabilityTracer (wrapper P16)
├── approval_gate.py            # Integração com P18 governance
├── reporter.py                 # SupremeReporter — gera MissionReport
└── errors.py                   # SupremeError, PlanError, ExecutionError, ApprovalDeniedError

tests/omnis_supreme/
├── __init__.py
├── test_models.py              # 30+ testes (estados, transições, serialização)
├── test_service.py             # 25+ testes (intake, planner, executor)
├── test_adapters.py            # 20+ testes (adapters com módulos mockados)
├── test_approval_gate.py       # 15+ testes (fluxos de aprovação)
└── test_e2e_supreme.py         # 10+ testes (missão completa mockada)

docs/omnis_supreme/
└── P20_SUPREME_ACTIVATION_SKELETON.md  # criado ao final
```

**Total: 7 source + 5 test = 12 arquivos**

---

## 16. CLASSES SUGERIDAS

### 16.1 models.py

| Classe | Prefixo | Descrição |
|---|---|---|
| `SupremeMission` | `spr_` | Missão suprema — entidade central |
| `SupremePlan` | `plan_` | Plano de execução (DAG) |
| `SupremeStep` | `step_` | Passo atômico no plano |
| `SupremeStatus` | — | Enum 9 estados |
| `MissionReport` | `rpt_` | Relatório final da missão |

### 16.2 service.py

```python
class SupremeOrchestrator:
    """Ponto de entrada único da P20.

    Uso:
        supreme = SupremeOrchestrator(dry_run=True)
        mission = supreme.run("cria campanha de Natal para Cliente X")
    """

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.intake = SupremeIntake()
        self.context_builder = SupremeContextBuilder()
        self.planner = SupremePlanner()
        self.executor = SupremeExecutor(dry_run=dry_run)
        self.approval_gate = SupremeApprovalGate()
        self.reporter = SupremeReporter()

    def run(self, request: str) -> SupremeMission:
        """Executa o ciclo completo da missão."""
        # 1. Intake
        mission = self.intake.parse(request)

        # 2. Context
        context = self.context_builder.build(mission.intent)
        mission.context = context.to_dict()

        # 3. Plan
        plan = self.planner.plan(mission)
        mission.plan = plan.to_dict()

        # 4. Dry Run
        dry_run_result = self.executor.dry_run(plan)
        mission.plan["dry_run"] = dry_run_result

        # 5. Approval Gate
        decision = self.approval_gate.submit(plan, dry_run_result)
        mission.approval_decisions.append(decision.to_dict())

        if decision.verdict == VERDICT_DENIED:
            mission.status = SupremeStatus.CANCELLED
            return mission

        if decision.verdict == VERDICT_REQUIRES_APPROVAL:
            mission.status = SupremeStatus.AWAITING_APPROVAL
            return mission  # aguarda operador

        # 6. Execute
        result = self.executor.execute(plan)
        mission.execution = result.to_dict()

        # 7. Delivery (se aplicável)
        if result.has_deliverables:
            delivery = self.executor.build_delivery(result)
            mission.delivery = delivery.to_dict()

        # 8. Report
        report = self.reporter.generate(mission)
        mission.report = report.to_dict()
        mission.status = SupremeStatus.COMPLETED

        return mission


class SupremeIntake:
    """Classifica requisição → intent + sector."""

    # Registry de padrões de intenção
    INTENT_PATTERNS: dict[str, list[str]] = {
        "create_campaign": ["cria campanha", "nova campanha", "campanha de"],
        "publish_content": ["publica", "posta", "agenda post", "sobe conteúdo"],
        "deliver_to_client": ["entrega pro cliente", "envia pro cliente", "manda pro cliente"],
        "analyze_performance": ["analisa", "métricas", "relatório de", "como foi"],
        "commercial_outreach": ["prospecção", "capta lead", "contato com"],
    }

    def parse(self, request: str) -> SupremeMission:
        intent = self._classify_intent(request)
        sector = self._classify_sector(intent)
        return SupremeMission.new(
            request_text=request,
            intent=intent,
            sector=sector,
        )


class SupremeContextBuilder:
    """Monta contexto multi-fonte para a missão."""

    def build(self, intent: str) -> SupremeContext:
        # Memory: hooks virais, padrões
        memory = ContextPack(...)  # via P4

        # Analytics: métricas recentes
        metrics = MetricSummary(...)  # via P13

        # Marketing: briefings ativos, audiências
        briefs = []  # via P5

        return SupremeContext(memory=memory, metrics=metrics, briefs=briefs)


class SupremePlanner:
    """Decompõe intenção → SupremePlan (DAG de passos)."""

    # Mapeamento intent → sequência de operações
    INTENT_TO_PIPELINE: dict[str, list[tuple[str, str]]] = {
        "create_campaign": [
            ("P5", "build_campaign_brief"),
            ("P19", "orchestrate_campaign"),
            ("P19", "allocate_budget"),
            ("P19", "build_publish_queue_plan"),
            ("P8", "validate_publish_readiness"),
        ],
        "deliver_to_client": [
            ("P8", "prepare_handoff"),
            ("P17", "build_delivery_package"),
        ],
        "publish_content": [
            ("P8", "validate_publish_readiness"),
            ("P8", "execute_publish"),
        ],
    }

    def plan(self, mission: SupremeMission) -> SupremePlan:
        pipeline = self.INTENT_TO_PIPELINE.get(mission.intent, [])
        steps = self._build_steps(pipeline)
        edges = self._build_edges(steps)
        modules = list({s.module_ref for s in steps})

        return SupremePlan.new(
            mission_id=mission.mission_id,
            steps=steps,
            edges=edges,
            selected_modules=modules,
            estimated_duration=self._estimate(steps),
        )
```

### 16.3 errors.py

```python
class SupremeError(Exception): ...                      # base
class PlanError(SupremeError): ...                      # erro no planejamento
class ExecutionError(SupremeError): ...                 # erro na execução
class ApprovalDeniedError(SupremeError): ...            # approval negado
class UnknownIntentError(SupremeError): ...             # intenção não reconhecida
class StepAdapterError(SupremeError): ...               # adapter não encontrado
class DryRunBlockedError(SupremeError): ...             # dry_run bloqueou ação real
```

---

## 17. CLI COMMANDS SUGERIDOS

```python
# src/omnis_supreme/cli.py (arquivo 8, opcional — pós-skeleton)

@click.group()
def supreme():
    """OMNIS Supreme — execução de missões."""

@supreme.command()
@click.argument("request")
@click.option("--dry-run/--no-dry-run", default=True)
def run(request: str, dry_run: bool):
    """Executa uma missão suprema."""
    orchestrator = SupremeOrchestrator(dry_run=dry_run)
    mission = orchestrator.run(request)
    click.echo(json.dumps(mission.to_dict(), indent=2))

@supreme.command()
@click.argument("mission_id")
def status(mission_id: str):
    """Verifica status de uma missão."""

@supreme.command()
@click.argument("mission_id")
def approve(mission_id: str):
    """Aprova uma missão aguardando approval."""

@supreme.command()
@click.argument("mission_id")
def report(mission_id: str):
    """Gera relatório de uma missão completa."""
```

---

## 18. TEST STRATEGY

### Meta: ≥ 100 testes

| Arquivo | Testes | Foco |
|---|---|---|
| `test_models.py` | 30+ | SupremeMission.new(), to_dict()/from_dict(), SupremeStatus transições válidas/inválidas, SupremePlan construção, SupremeStep dependências |
| `test_service.py` | 25+ | SupremeIntake.classify() para cada intent, SupremePlanner com pipelines, SupremeExecutor.execute_step() com mock adapters |
| `test_adapters.py` | 20+ | Cada adapter do registry executado com inputs mockados, verificar que módulos reais são chamados corretamente |
| `test_approval_gate.py` | 15+ | Gate 1 (aprova/nega/pendente), Gate 2 (aprova/nega), risco classificado corretamente, scope guard bloqueia módulos não listados |
| `test_e2e_supreme.py` | 10+ | Missão completa mockada: "cria campanha" → intake → plan → dry_run → execute → report. Verificar SupremeStatus transições |

### Comandos de validação

```powershell
python -m pytest tests/omnis_supreme/ -q          # targeted ≥ 100
python -m pytest tests/ -q                          # full suite ≥ 4038
```

---

## 19. DRY-RUN STRATEGY

Seguindo o padrão dos 20 módulos:

```python
class SupremeOrchestrator:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run

    def run(self, request: str) -> SupremeMission:
        mission = SupremeMission.new(
            request_text=request,
            dry_run=self.dry_run,           # propaga para missão
            approval_required=True,          # sempre
        )
        # ...每一步都检查 dry_run
```

**Comportamento dry_run:**
- Intake e Planejamento: sempre executam (não têm efeitos colaterais)
- Execução: adapters recebem `dry_run=True`, módulos simulam outputs
- Delivery: `DeliveryPlanner(dry_run=True)` gera package sem persistir
- Approval: sempre requer aprovação (independe de dry_run)

**O que NUNCA acontece em dry_run:**
- Escrita em disco (ZIP, CSV, JSON files)
- Chamadas de rede (OAuth, APIs externas)
- Mutação de estado em bancos de dados
- Publicação real (P8 bloqueia com `dry_run=True`)

---

## 20. FAILURE / RETRY / RECOVERY

### Estratégia por camada

| Camada | Falha | Recovery |
|---|---|---|
| Intake | Intenção não reconhecida | `UnknownIntentError` → mission.status=FAILED, sugere revisão do request |
| Context | Fonte indisponível (ex: P4) | Context parcial com warning, prossegue degradado |
| Planning | Pipeline não definido para intent | `PlanError` → mission.status=FAILED, sugere capability gap |
| Dry Run | Step simulado falha | Blocker adicionado, plano volta pra planning |
| Execution | Step falha | `ExecutionError` → step.status=FAILED, missão pausa. Retry do step (até 3x). Se irrecuperável → mission.status=FAILED |
| Approval | Negado | `ApprovalDeniedError` → mission.status=CANCELLED, log do motivo |
| Delivery | P17 recusa handoff | `HandoffRejectedError` → volta pra execution, ajusta handoff |

### Retry automático (inline, sem fila)

```python
MAX_RETRIES = 3

def _execute_step_with_retry(self, step: SupremeStep, context: dict) -> dict:
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return self.execute_step(step, context)
        except Exception as e:
            last_error = e
            step.metadata["retry_attempt"] = attempt
            if attempt < MAX_RETRIES:
                step.metadata["retry_at"] = _now_iso()
    raise ExecutionError(
        f"Step {step.step_id} falhou após {MAX_RETRIES} tentativas: {last_error}"
    )
```

---

## 21. RISCOS ARQUITETURAIS

| # | Risco | Impacto | Prob | Mitigação |
|---|---|---|---|---|
| R1 | P20 virar God Module | Alto — acopla tudo | Média | Limite rígido: < 500 linhas de lógica própria. Toda lógica de domínio delegada aos módulos |
| R2 | Adapter registry crescer descontrolado | Médio — manutenção | Baixa | Cada adapter é 1 lambda ≤ 3 linhas. Registry centralizado e auditável |
| R3 | P20 importar módulo proibido | Alto — quebra boundary | Baixa | Teste de imports no CI (grep por proibidos). Revisão de PR obrigatória |
| R4 | SupremeMission virar "objeto Deus" com 30 campos | Médio — complexidade | Média | Campos são referências (dict), não dados duplicados. Mission é ponteiro, não repositório |
| R5 | Execução paralela de steps quebrar ordem | Alto — inconsistência | Baixa | P20 executa steps sequencialmente no skeleton. Paralelismo é pós-MVP |
| R6 | Circular dependency P20 ↔ P19 | Crítico — import loop | Nula | P20 importa P19 (unidirecional). P19 NUNCA importa P20 |
| R7 | Dry-run vazar ação real | Crítico — publi sem approval | Baixa | dry_run propaga para todos os módulos. P8 e P17 têm dry_run como guard |
| R8 | CLI commands crescerem e virarem app próprio | Médio — desvio de escopo | Média | CLI é opcional. Prioridade é serviço Python (usado via Claude Code) |

---

## 22. ANTI-PATTERNS PROIBIDOS

```
┌──────────────────────────────────────────────────────────────────┐
│                    ANTI-PATTERNS PROIBIDOS                       │
│                                                                  │
│  ✗ GOD MODULE                                                   │
│    src/omnis_supreme/service.py com 2000 linhas                 │
│    → Máximo 500 linhas de lógica própria                        │
│                                                                  │
│  ✗ BYPASS APPROVAL                                              │
│    if mission.intent == "test": approval_required = False       │
│    → approval_required=True é IMOBILIÁRIO                       │
│                                                                  │
│  ✗ DIRECT MODULE COUPLING                                       │
│    from src.campaign_manager.service import CampaignOrchestrator │
│    → Usar ADAPTER_REGISTRY, nunca importar services diretamente  │
│                                                                  │
│  ✗ REINVENTAR MODELOS                                           │
│    class SupremeCampaign(Campaign): ...                          │
│    → P20 NUNCA cria subclasses de modelos alheios               │
│                                                                  │
│  ✗ HARDCODED PIPELINES                                          │
│    if request == "campanha de natal": ...                        │
│    → Pipelines são data (INTENT_TO_PIPELINE), não if/else       │
│                                                                  │
│  ✗ CROSS-MODULE WRITES                                          │
│    src/delivery_portal/models.py foi editado pela P20           │
│    → P20 só LÊ exports, nunca EDITA outros módulos              │
│                                                                  │
│  ✗ RUNTIME DATA EM COMMITS                                      │
│    exports/, logs/, data/ nos commits da P20                    │
│    → .gitignore cobre. Verificar antes de commit                │
└──────────────────────────────────────────────────────────────────┘
```

---

## 23. CRITÉRIOS DE ACEITE

- [ ] Namespace `src/omnis_supreme/` com 7 arquivos
- [ ] Testes ≥ 100 (targeted), todos passando
- [ ] Full suite ≥ 4038 passando, 0 novas falhas
- [ ] SupremeStatus: 9 estados com transições validadas
- [ ] SupremeMission com `.new()` + `.to_dict()` + `.from_dict()` + `_now_iso()`
- [ ] `dry_run=True` e `approval_required=True` como defaults
- [ ] ADAPTER_REGISTRY cobre pelo menos 6 operações (P5, P8, P17, P19)
- [ ] SupremeOrchestrator.run() executa ciclo completo (intake → report)
- [ ] SupremeExecutor com tracing (P16) por step
- [ ] SupremeApprovalGate com 2 gates (plano + entrega)
- [ ] Nenhum import proibido
- [ ] Nenhum módulo existente modificado
- [ ] Nenhum legado tocado
- [ ] IDs com prefixos corretos (`spr_`, `plan_`, `step_`, `rpt_`)
- [ ] Retry automático (até 3x) em steps que falham
- [ ] Topological sort inline (para ordenar steps do DAG)
- [ ] CLI opcional (não bloqueia merge se ausente)

---

## 24. ROADMAP INCREMENTAL DE IMPLEMENTAÇÃO

### Milestone 1: Core Models (arquivos: 2 source + 1 test)
- `models.py` — SupremeMission, SupremePlan, SupremeStep, SupremeStatus, MissionReport
- `errors.py` — hierarquia de erros
- `test_models.py` — 30+ testes

### Milestone 2: Service Layer (arquivos: 2 source + 1 test)
- `service.py` — SupremeOrchestrator, SupremeIntake, SupremeContextBuilder, SupremePlanner
- `adapters.py` — ADAPTER_REGISTRY (6+ operações)
- `test_service.py` — 25+ testes

### Milestone 3: Execution + Tracing (arquivos: 2 source + 2 test)
- Atualizar `service.py` — SupremeExecutor com dry_run e retry
- `tracer.py` — ObservabilityTracer (wrapper P16)
- `test_adapters.py` — 20+ testes
- `test_e2e_supreme.py` — 10+ testes

### Milestone 4: Approval + Report (arquivos: 1 source + 1 test)
- `approval_gate.py` — SupremeApprovalGate (2 gates, P18)
- `reporter.py` — SupremeReporter
- `test_approval_gate.py` — 15+ testes

### Milestone 5: Integration
- `__init__.py` — exports públicos
- Skeleton doc (`P20_SUPREME_ACTIVATION_SKELETON.md`)
- Full suite validation (≥ 4038 testes)
- Merge

---

## 25. RECOMENDAÇÃO DE WORKTREES/ABAS PARA P20

### VEREDITO: **1 frente única**

P20 é um módulo coeso (orquestração) com baixo paralelismo interno. Diferente da Onda 6 (2 módulos independentes), a P20 tem dependências internas:

```
models → adapters → service → executor → tracer → approval → report
```

Cada camada depende da anterior. **2 frentes causariam conflitos de merge constantes.**

### Configuração

```powershell
# Worktree única
. .\scripts\omnis_parallel.ps1
Test-OmnisClean
New-OmnisSafetyTag
Start-ClaudeWorktree -FrenteName "p20-omnis-supreme"
```

| Item | Valor |
|---|---|
| Worktree | `C:\Users\lucas\omnis-p20-omnis-supreme` |
| Branch | `parallel/p20-omnis-supreme` |
| Abas | **1 aba principal** (implementação sequencial) |
| Arquivos | 12 (7 source + 5 test) |
| Testes alvo | ≥ 100 |
| Ordem interna | M1 → M2 → M3 → M4 → M5 |

---

## VEREDITO FINAL

```
█████████████████████████████████████████████████████████████
█                                                         █
█   P20 OMNIS SUPREME ACTIVATION                          █
█                                                         █
█   Tipo: Orquestração fina (não módulo de domínio)       █
█   Arquivos: 12 (7 source + 5 test)                     █
█   Testes alvo: ≥ 100                                    █
█   Worktrees: 1 (única)                                  █
█   Ordem: Sequencial (M1→M2→M3→M4→M5)                   █
█                                                         █
█   Principais integrações:                               █
█   - P5 (briefs) → P19 (campaign) → P8 (publish)        █
█   - P17 (delivery) ← P8 (handoff)                      █
█   - P18 (governance) — approval gates                  █
█   - P16 (observability) — tracing                      █
█   - P4 (memory) — contexto + aprendizados              █
█                                                         █
█   RISCO PRINCIPAL: God Module creep                    █
█   MITIGAÇÃO: Limite < 500 linhas lógica própria        █
█                                                         █
█████████████████████████████████████████████████████████████
```

---

## PRÓXIMOS PASSOS

1. Revisão deste documento pelo operador
2. Aprovação da arquitetura
3. Criação de worktree única: `omnis-p20-omnis-supreme`
4. Implementação sequencial M1→M5
5. Merge --no-ff na master
6. Full suite ≥ 4038 testes
7. Tag `onda-final-complete-<date>`

---

*OMNIS Control Tower — P20 Supreme Activation Architecture.*
*Aguardando revisão e aprovação do operador.*
