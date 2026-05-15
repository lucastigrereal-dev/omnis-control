# P25 — MULTI-MODEL ORCHESTRATION ARCHITECTURE

> **Data:** 2026-05-14
> **Status:** ARCHITECTURE DRAFT — Aguardando revisão
> **Base:** master pós-P24 (4604 testes, 0 regressões)
> **Pré-requisitos:** P20 Supreme + P21 Memory Intel + P24 Live Cockpit

---

## 1. DEFINIÇÃO

P25 Multi-Model Orchestration é a camada de **seleção e roteamento de modelos de IA** do OMNIS. Em vez de usar um único modelo (Claude) para todas as tarefas, o P25 mantém um **registro de modelos disponíveis** e um **roteador baseado em contratos** que seleciona o melhor modelo para cada tarefa com base em: complexidade, custo, latência, e risco da operação.

---

## 2. PROBLEMA QUE RESOLVE

**Atual:** Todo o OMNIS usa Claude via Claude Code como único modelo. Tarefas simples (classificar intenção, validar schema) consomem o mesmo modelo que tarefas complexas (planejar missão, gerar código). Não há fallback se um modelo falhar. Não há otimização de custo.

**Com P25:** O OMNIS pode usar o modelo certo para cada tarefa — barato para simples, potente para complexo, com fallback automático entre providers.

---

## 3. O QUE FAZ

1. **Model Registry** — cadastro de modelos disponíveis com capabilities, custo, latência
2. **Task Classifier** — classifica a tarefa por complexidade, risco, e domínio
3. **Model Router** — seleciona o melhor modelo para a tarefa com base em contratos
4. **Provider Adapters** — thin wrappers para cada provider (Anthropic, OpenAI, Groq, etc.)
5. **Fallback Chain** — se modelo A falhar, tenta B, depois C
6. **Cost Tracker** — rastreia custo por tarefa/modelo/dia
7. **Latency Monitor** — métricas de latency por modelo (integrado ao P16)

---

## 4. O QUE NÃO FAZ

| PROIBIDO | Motivo |
|---|---|
| Ser um "LLM Router" genérico sem contratos | Cada modelo tem contrato explícito de entrada/saída |
| Fazer fine-tuning de modelos | Fora do escopo. P25 roteia, não treina |
| Substituir o P20 Supreme | P20 orquestra missões. P25 seleciona modelos para steps |
| Gerenciar API keys | Keys ficam em env vars. P25 só referencia providers |
| Fazer load balancing complexo | v1 é seleção por contrato + fallback sequencial |
| Auto-escalar instâncias de modelo | Fora do escopo. Infra é externa |
| Ser um proxy HTTP | P25 é biblioteca Python, não servidor |

---

## 5. RELAÇÃO COM P20 SUPREME

P25 é **chamado pelo P20 SupremeExecutor** no momento de executar cada step:

```python
# P20 SupremeExecutor._execute_step (com P25):
def _execute_step(self, step: SupremeStep, context: dict) -> dict:
    router = ModelRouter()  # P25
    model_config = router.select_model(
        task_type=step.intent,
        complexity=self._classify_complexity(step),
        risk_level=step.risk_level,
    )
    adapter = router.get_adapter(model_config.provider)
    return adapter.execute(step, context, model_config)
```

P20 **não precisa conhecer detalhes de modelos**. Só pergunta ao P25: "qual modelo para esta tarefa?"

---

## 6. RELAÇÃO COM P21 MEMORY

P21 fornece **contexto histórico de performance de modelos**:

- "Modelo X teve 95% sucesso em tarefas de classificação"
- "Modelo Y é 3x mais barato que Z para tarefas de summarization"
- "Provider A teve 3 falhas consecutivas — evitar temporariamente"

O P25 consulta P21 antes de rotear para evitar modelos com histórico ruim.

---

## 7. RELAÇÃO COM P22 FORGE

P22 gera código. O P25 permite que o P22 use modelos diferentes para:

- **Planejamento de arquitetura** → modelo mais potente (ex: Opus)
- **Geração de scaffold** → modelo rápido (ex: Haiku)
- **Policy scan** → modelo barato (ex: Groq)

O P22 não precisa saber qual modelo está usando — o P25 abstrai isso.

---

## 8. RELAÇÃO COM P23 AUTONOMOUS EXECUTION

P23 executa steps autonomamente. Com P25, cada step pode usar um modelo diferente:

- **Step de análise** → modelo potente
- **Step de validação** → modelo rápido
- **Step de transformação** → modelo deterministico (sem LLM)

O circuito breaker do P23 monitora falhas por modelo também.

---

## 9. RELAÇÃO COM P24 LIVE COCKPIT

P24 mostra no cockpit:

- **Modelos ativos** — quais estão sendo usados agora
- **Custo do dia** — acumulado por modelo
- **Latência p95** — por provider
- **Fallbacks acionados** — alertas quando modelo primário falhou

---

## 10. CONTRATOS PRINCIPAIS

### 10.1 ModelConfig

```python
@dataclass
class ModelConfig:
    model_id: str              # "mm_<8hex>"
    name: str                  # "claude-opus-4-7"
    provider: str              # "anthropic" | "openai" | "groq" | ...
    capabilities: list[str]    # ["text", "code", "analysis", "planning"]
    cost_per_1k_tokens: float  # USD
    avg_latency_ms: int        # latência média em ms
    max_tokens: int            # limite de contexto
    priority: int              # 1 = primário, 2 = fallback, 3 = último recurso
    enabled: bool              # pode ser desligado sem remover
```

### 10.2 RoutingRequest / RoutingDecision

```python
@dataclass
class RoutingRequest:
    task_type: str             # "classify_intent" | "generate_code" | "summarize" | ...
    complexity: str            # "low" | "medium" | "high" | "critical"
    risk_level: str            # low | medium | high | critical (do P18)
    max_cost_usd: float        # teto de custo para esta tarefa
    max_latency_ms: int        # teto de latência
    preferred_provider: str    # opcional — forçar provider

@dataclass
class RoutingDecision:
    decision_id: str           # "mrd_<8hex>"
    model: ModelConfig         # modelo selecionado
    fallback_chain: list[str]  # modelos de fallback em ordem
    reason: str                # por que este modelo foi escolhido
    estimated_cost_usd: float  # custo estimado
```

### 10.3 ProviderAdapter (protocol)

```python
class ProviderAdapter(Protocol):
    """Contrato mínimo para um provider de modelo."""

    provider: str              # "anthropic", "openai", etc.
    supported_models: list[str]

    def execute(self, prompt: str, model: ModelConfig, **kwargs) -> dict:
        """Executa o prompt no modelo e retorna resposta padronizada."""
        ...

    def health_check(self) -> bool:
        """True se o provider está acessível."""
        ...
```

---

## 11. STATE / FLOW

```
┌────────────────────────────────────────────────────────────────┐
│                    P25 MODEL ROUTING FLOW                       │
│                                                                 │
│  [P20 SupremeExecutor]                                         │
│     │                                                           │
│     ├─→ ModelRouter.select_model(task_type, complexity, risk)  │
│     │      │                                                    │
│     │      ├─→ TaskClassifier.classify(step) → complexity      │
│     │      ├─→ ModelRegistry.find(capabilities, complexity)    │
│     │      ├─→ CostTracker.estimate(task, models)              │
│     │      ├─→ MemoryIntel.get_model_performance(provider)     │
│     │      └─→ RoutingDecision                                  │
│     │                                                           │
│     ├─→ ModelRouter.get_adapter(decision.model.provider)       │
│     │      └─→ ProviderAdapter (thin wrapper)                   │
│     │                                                           │
│     ├─→ adapter.execute(prompt, model)                         │
│     │      ├─→ SUCCESS → ExecutionResult                        │
│     │      └─→ FAILURE → fallback_chain.next()                 │
│     │                                                           │
│     └─→ CostTracker.record(decision, tokens_used, success)     │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## 12. ARQUIVOS SUGERIDOS

```
src/multi_model/
├── __init__.py               # Exports: ModelRegistry, ModelRouter, ProviderAdapter, etc.
├── models.py                 # ModelConfig, RoutingRequest, RoutingDecision, TaskClass
├── errors.py                 # ModelError, ProviderUnavailableError, RoutingError, CostLimitError
├── registry.py               # ModelRegistry — cadastro, busca, enable/disable
├── router.py                 # ModelRouter — select_model(), get_adapter()
├── classifier.py             # TaskClassifier — classifica tarefa por complexidade/domínio
├── adapters/
│   ├── __init__.py           # ADAPTER_REGISTRY
│   ├── anthropic_adapter.py  # AnthropicProviderAdapter
│   ├── openai_adapter.py     # OpenAIProviderAdapter
│   ├── groq_adapter.py       # GroqProviderAdapter
│   └── mock_adapter.py       # MockAdapter para testes/dry-run
├── cost_tracker.py           # CostTracker — rastreia custo por tarefa/modelo
├── fallback.py               # FallbackChain — tentar A → B → C
└── cli.py                    # CLI: model list, model test, cost report

tests/multi_model/
├── test_models.py            # 15+ testes
├── test_registry.py          # 12+ testes
├── test_router.py            # 15+ testes
├── test_classifier.py        # 10+ testes
├── test_adapters.py          # 12+ testes
├── test_fallback.py          # 10+ testes
├── test_cost_tracker.py      # 10+ testes
└── test_e2e_multimodel.py    # 10+ testes

docs/multi_model/
└── P25_MULTI_MODEL_ORCHESTRATION_ARCHITECTURE.md
```

**Total: 12 source + 8 test + 1 doc = 21 arquivos**

---

## 13. CLASSES SUGERIDAS

```python
class TaskClassifier:
    """Classifica tarefas por complexidade e domínio."""
    def classify(step: SupremeStep) -> TaskClass: ...
    def classify_intent(intent: str) -> TaskClass: ...

class ModelRegistry:
    """Registro de modelos disponíveis."""
    def register(model: ModelConfig) -> None: ...
    def find(capabilities: list[str], max_cost: float) -> list[ModelConfig]: ...
    def get(model_id: str) -> ModelConfig: ...
    def enable(model_id: str) -> None: ...
    def disable(model_id: str) -> None: ...
    def list_enabled() -> list[ModelConfig]: ...

class ModelRouter:
    """Roteador principal — seleciona modelo e adapter."""
    def __init__(self, registry: ModelRegistry, classifier: TaskClassifier, ...): ...
    def select_model(request: RoutingRequest) -> RoutingDecision: ...
    def get_adapter(provider: str) -> ProviderAdapter: ...
    def execute(request: RoutingRequest, prompt: str) -> dict: ...

class FallbackChain:
    """Cadeia de fallback: se A falhar, tenta B, depois C."""
    def __init__(self, models: list[ModelConfig]): ...
    def execute(prompt: str, adapters: dict) -> dict: ...
    @property
    def attempts(self) -> int: ...

class CostTracker:
    """Rastreia custo acumulado por tarefa/modelo/dia."""
    def estimate(prompt: str, model: ModelConfig) -> float: ...
    def record(model_id: str, tokens: int, cost: float) -> None: ...
    def daily_total() -> float: ...
    def by_model() -> dict[str, float]: ...
```

---

## 14. CLI COMMANDS SUGERIDOS

```
model list                     # Lista modelos registrados com status
model test <model_id>          # Testa conectividade com modelo
model route <task_type>        # Simula roteamento para tarefa (dry-run)
model cost today               # Custo acumulado do dia
model cost report [--days 7]   # Relatório de custo por modelo/dia
```

---

## 15. TEST STRATEGY

| Arquivo | Testes | Foco |
|---|---|---|
| `test_models.py` | 15+ | ModelConfig.new(), RoutingRequest validation, RoutingDecision.to_dict/from_dict |
| `test_registry.py` | 12+ | Register, find por capability, enable/disable, fallback order |
| `test_router.py` | 15+ | Seleção por complexidade, por custo, por risco. Fallback quando primário offline |
| `test_classifier.py` | 10+ | Classificação de intents OMNIS → complexity/risk |
| `test_adapters.py` | 12+ | Mock adapter retorna resposta padronizada. Health check |
| `test_fallback.py` | 10+ | Fallback A→B→C funciona. Circuito abre após 3 falhas |
| `test_cost_tracker.py` | 10+ | Estimativa de custo, acumulado diário, breakdown por modelo |
| `test_e2e_multimodel.py` | 10+ | Router + Adapter + Fallback integrados. Dry-run não gasta créditos |

**Meta: ≥ 95 testes**

---

## 16. DRY-RUN STRATEGY

```python
class ModelRouter:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run

    def execute(self, request: RoutingRequest, prompt: str) -> dict:
        if self.dry_run:
            return {
                "status": "dry_run",
                "decision": self.select_model(request).to_dict(),
                "estimated_cost": self.cost_tracker.estimate(prompt, decision.model),
                "prompt_length": len(prompt),
            }
        # Execução real
```

Dry-run sempre usa MockAdapter — nunca chama API real, nunca gasta créditos.

---

## 17. APPROVAL STRATEGY

P25 **não requer approval gate próprio** porque:

1. Não executa ações destrutivas — só chama APIs de LLM
2. O approval já acontece no P20 (mission approval) e P23 (checkpoint approval)
3. O CostTracker tem **teto diário configurável** — se exceder, para de executar e gera alerta

**Exceção:** Trocar de provider (ex: Anthropic → OpenAI) requer confirmation se o custo estimado for >2x o provider padrão.

---

## 18. FAILURE / RECOVERY

| Falha | Comportamento |
|---|---|
| Provider offline (timeout) | Fallback para próximo modelo na chain |
| Provider retorna erro 5xx | Tenta 2 retries com backoff 1s → fallback |
| Modelo retorna resposta inválida | Fallback para modelo mais capaz |
| Cost limit diário atingido | Bloqueia execuções não-críticas. Críticas pedem approval |
| Todos os models offline | Erro `AllModelsUnavailableError`. Missão pausa |
| Adapter quebrado (bug) | `AdapterError` → fallback para MockAdapter (retorna schema mínimo) |

---

## 19. RISCOS ARQUITETURAIS

| # | Risco | Impacto | Prob | Mitigação |
|---|---|---|---|---|
| R1 | Vazar API keys em logs | Crítico | Baixa | Keys só em env vars. Adapters não logam headers |
| R2 | Custo disparar sem controle | Alto | Média | CostTracker com teto diário. Alerta no P24 |
| R3 | Router virar God Class com 500 regras | Médio | Média | Contratos explícitos. Classifier separado. Registry desacoplado |
| R4 | Dependência de provider específico | Médio | Baixa | Adapters padronizados. Mock adapter sempre disponível |
| R5 | Latência adicionada pelo routing | Baixo | Baixa | Routing é determinístico (<10ms). Só a chamada ao modelo tem latência |

---

## 20. ANTI-PATTERNS PROIBIDOS

```
✗ ROTEADOR GIGANTE COM 500 REGRAS IF/ELSE — classifier + registry separados
✗ HARDCODED MODEL NAMES — tudo no registry, configurável
✗ ADAPTERS COM LÓGICA DE NEGÓCIO — adapters são thin wrappers
✗ GASTAR CRÉDITOS EM DRY-RUN — dry_run=True = MockAdapter sempre
✗ IGNORAR FALLBACK — todo execute() tem fallback chain
✗ CUSTO INFINITO — CostTracker com teto diário
✗ PROVIDER COMO DEPENDÊNCIA FORTE — mock adapter é default
```

---

## 21. CRITÉRIOS DE ACEITE

- [ ] Namespace `src/multi_model/` com 12 arquivos
- [ ] Testes ≥ 95 (targeted), todos passando
- [ ] ModelRegistry funcional com register/find/enable/disable
- [ ] ModelRouter.select_model() retorna RoutingDecision para qualquer task_type
- [ ] FallbackChain executa A→B→C sem perder contexto
- [ ] CostTracker com teto diário configurável
- [ ] Pelo menos 2 adapters reais + MockAdapter
- [ ] dry_run=True default, nunca chama API real
- [ ] Zero toques em módulos existentes (exceto P20 adapters — nova entry)
- [ ] Full suite sem regressões

---

## 22. ORDEM INCREMENTAL DE IMPLEMENTAÇÃO

### M1: Models + Errors + Classifier
- `models.py`, `errors.py`, `classifier.py`
- `test_models.py`, `test_classifier.py`

### M2: Registry + Mock Adapter
- `registry.py`, `adapters/__init__.py`, `adapters/mock_adapter.py`
- `test_registry.py`

### M3: Router + Fallback
- `router.py`, `fallback.py`
- `test_router.py`, `test_fallback.py`

### M4: Adapters Reais
- `adapters/anthropic_adapter.py`, `adapters/openai_adapter.py`, `adapters/groq_adapter.py`
- `test_adapters.py`

### M5: Cost Tracker + CLI + E2E + Docs
- `cost_tracker.py`, `cli.py`
- `test_cost_tracker.py`, `test_e2e_multimodel.py`
- `__init__.py`, skeleton doc

---

## 23. RECOMENDAÇÃO DE PARALELIZAÇÃO

**1 frente única.** P25 é sequencial internamente. M1→M2→M3→M4→M5. Os adapters (M4) podem ser parcialmente paralelizados se feitos por providers diferentes, mas o contrato único (M2 MockAdapter) precisa estar pronto antes.

---

*OMNIS Control Tower — P25 Multi-Model Orchestration Architecture.*
