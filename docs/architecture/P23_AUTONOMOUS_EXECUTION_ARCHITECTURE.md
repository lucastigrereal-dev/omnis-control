# P23 — AUTONOMOUS EXECUTION ARCHITECTURE

> **Data:** 2026-05-13
> **Status:** DRAFT — Aguardando revisão
> **Base:** master `ada6373` (P20 fechado, P21+P22 arquitetados)
> **Pré-requisitos:** P21 Memory Intelligence + P22 Capability Forge Real

---

## 1. DEFINIÇÃO

P23 Autonomous Execution é a camada que transforma o P20 de **execução semi-manual** (cada step requer intervenção do operador) em **execução autônoma com gates**. O operador aprova o plano no início e recebe o relatório no final. O meio é autônomo.

Diferente de um "modo automático completo" (perigoso), a P23 implementa **autonomia supervisionada**: executa steps em sequência, respeita approval gates em checkpoints críticos, faz retry automático, e escala para o operador apenas em falhas irrecuperáveis.

---

## 2. PROBLEMA QUE RESOLVE

**Atual:** O P20 gera um plano (SupremePlan) e executa steps, mas cada step que requer decisão para o operador. Para missões com 10+ steps, o operador precisa ficar presente durante toda a execução.

**Com P23:** "Aprova o plano, volta quando terminar." O sistema executa autonomamente, para apenas em gates críticos (envio, publicação, cobrança), e notifica o operador ao concluir.

---

## 3. O QUE FAZ

1. **Auto-execute steps** — steps não-críticos executam sem intervenção
2. **Checkpoint gates** — para em actions SEND, DEPLOY, FINANCIAL, DELETE
3. **Retry automático** — steps que falham são retentados (até 3x) com backoff
4. **Circuit breaker** — se 3+ steps consecutivos falham, pausa e escala
5. **Progress tracking** — status em tempo real de cada step (via P16)
6. **Resume from checkpoint** — se interrompido, retoma do último step concluído
7. **Notification** — push ao operador em checkpoints e conclusão
8. **Dry-run completo** — simula toda a execução autônoma sem efeitos reais
9. **Timeout por step** — cada step tem timeout configurável (default 5min)
10. **Learning writeback** — aprendizados de execução autônoma → P21

---

## 4. O QUE NÃO FAZ

| PROIBIDO | Motivo |
|---|---|
| Executar sem approval inicial | O plano sempre requer aprovação antes de executar |
| Pular gates críticos | SEND, DEPLOY, FINANCIAL, DELETE sempre param para aprovação |
| Tomar decisões de negócio | Ex: "qual hotel contactar?", "qual preço cobrar?" — operador decide |
| Modificar o plano durante execução | Plano é imutável após aprovação. Mudanças = replan |
| Executar steps em paralelo (MVP) | v1 é sequencial. Paralelismo é pós-MVP |
| Substituir P20 | P23 é modo de execução do P20, não substituto |
| Auto-aprovar capabilities novas | Gaps detectados durante execução autônoma são reportados, não resolvidos |
| Executar indefinidamente | Timeout global da missão (default 30min) |

---

## 5. RELAÇÃO COM P20

P23 é um **modo do SupremeExecutor**. O P20 ganha um novo método:

```python
class SupremeExecutor:
    # Existente (P20):
    def execute(self, plan: SupremePlan) -> ExecutionResult: ...
    def execute_step(self, step: SupremeStep, context: dict) -> dict: ...

    # NOVO (P23):
    def execute_autonomous(self, plan: SupremePlan, 
                           checkpoints: list[str] = None) -> AutonomousResult:
        """Executa plano autonomamente, parando apenas em checkpoints."""
```

O `SupremeOrchestrator.run()` ganha um parâmetro:

```python
def run(self, request: str, mode: str = "interactive") -> SupremeMission:
    """mode: 'interactive' (P20) | 'autonomous' (P23)"""
```

---

## 6. RELAÇÃO COM MÓDULOS EXISTENTES

| Módulo | Como P23 usa |
|---|---|
| P20 `omnis_supreme` | **Estende.** SupremeExecutor.execute_autonomous() |
| P18 `governance` | Define quais actions requerem checkpoint gate |
| P16 `observability_local` | Progress tracking, metric points por step |
| P21 `memory_intel` | Writeback de aprendizados de execução autônoma |
| P4 `memory_pack` | Contexto para decisões de retry/recovery |

| Módulo | P23 NÃO importa |
|---|---|
| P1-P15, P17, P19 | Domínios de negócio |

---

## 7. CONTRATOS PRINCIPAIS

### 7.1 AutonomousConfig

```python
@dataclass
class AutonomousConfig:
    config_id: str               # "aut_<8hex>"
    max_retries_per_step: int = 3
    retry_backoff_seconds: int = 5
    step_timeout_seconds: int = 300     # 5 min
    mission_timeout_seconds: int = 1800  # 30 min
    circuit_breaker_threshold: int = 3   # pausa após 3 falhas consecutivas
    checkpoint_actions: list[str] = None  # default: ["send", "deploy", "financial", "delete"]
    notify_on_checkpoint: bool = True
    notify_on_completion: bool = True
    dry_run: bool = True
```

### 7.2 AutonomousResult

```python
@dataclass
class AutonomousResult:
    run_id: str                  # "aut_<8hex>"
    plan_id: str
    status: str                  # "completed" | "paused_at_checkpoint" | "failed" | "timeout" | "circuit_breaker"
    steps_executed: int
    steps_succeeded: int
    steps_failed: int
    steps_skipped: int
    checkpoints_hit: list[str]   # step_ids onde parou
    current_step_id: str | None  # último step executado (para resume)
    elapsed_seconds: float
    trace_events: list[dict]     # TraceEvent[] do P16
    warnings: list[str]
    errors: list[str]
    resume_possible: bool
    completed_at: str
```

### 7.3 Checkpoint Actions

```python
# Do P18 governance — mapeamento action → requer checkpoint?
CHECKPOINT_ACTIONS = {
    "read": False,        # seguro, auto-executa
    "write": False,       # dry_run=True bloqueia escrita real
    "send": True,         # CHECKPOINT — enviar para cliente requer aprovação
    "deploy": True,       # CHECKPOINT — deploy requer aprovação
    "delete": True,       # CHECKPOINT — deletar requer aprovação
    "financial": True,    # CHECKPOINT — financeiro requer aprovação
    "configure": False,   # config é segura em dry_run
}
```

---

## 8. STATE / FLOW

```python
class AutonomousState(str, Enum):
    IDLE = "idle"                        # pronto para iniciar
    RUNNING = "running"                  # executando steps
    PAUSED_CHECKPOINT = "paused_checkpoint"  # parado em gate crítico
    PAUSED_ERROR = "paused_error"        # parado por falha (circuit breaker)
    PAUSED_TIMEOUT = "paused_timeout"    # parado por timeout
    RESUMING = "resuming"                # retomando de checkpoint
    COMPLETED = "completed"              # todos steps concluídos
    FAILED = "failed"                    # falha irrecuperável
    CANCELLED = "cancelled"              # cancelado pelo operador
```

### Fluxo principal

```
IDLE → RUNNING → step_1 → step_2 → [CHECKPOINT step_3] → PAUSED_CHECKPOINT
                    ↓                        ↓
              [step falha]            [operador aprova]
                    ↓                        ↓
              retry (≤3x)              RESUMING → step_3 → ... → COMPLETED
                    ↓
              [3 falhas consecutivas]
                    ↓
              PAUSED_ERROR → [operador decide: retry / skip / abort]
```

---

## 9. ARQUIVOS SUGERIDOS

```
src/autonomous_execution/           # P23 namespace
├── __init__.py
├── models.py                       # AutonomousConfig, AutonomousResult, AutonomousState
├── executor.py                     # AutonomousExecutor — lógica principal
├── checkpoint.py                   # CheckpointManager — gates e ações críticas
├── circuit_breaker.py              # CircuitBreaker — detecção de falhas consecutivas
├── recovery.py                     # RecoveryManager — retry, resume, rollback
├── errors.py                       # AutonomousError, CheckpointError, CircuitBreakerError, TimeoutError
└── cli.py                          # autonomous run, autonomous resume, autonomous status

tests/autonomous_execution/
├── __init__.py
├── test_models.py                  # 15+ testes
├── test_executor.py                # 25+ testes (execução autônoma completa)
├── test_checkpoint.py              # 10+ testes (gates, ações críticas)
├── test_circuit_breaker.py         # 10+ testes
├── test_recovery.py                # 10+ testes (retry, resume)
└── test_e2e_autonomous.py          # 10+ testes

docs/autonomous_execution/
└── P23_AUTONOMOUS_EXECUTION_SKELETON.md
```

**Total: 8 source + 5 test + 1 doc = 14 arquivos**

---

## 10. CLASSES SUGERIDAS

```python
class AutonomousExecutor:
    """Executor autônomo de missões Supreme."""

    def __init__(self, config: AutonomousConfig = None):
        self.config = config or AutonomousConfig.new()
        self.checkpoint_mgr = CheckpointManager(self.config)
        self.circuit_breaker = CircuitBreaker(self.config)
        self.recovery = RecoveryManager(self.config)
        self.tracer = ObservabilityTracer()

    def execute(self, plan: SupremePlan) -> AutonomousResult:
        """Executa plano autonomamente."""

    def execute_step_autonomous(self, step: SupremeStep, 
                                context: dict) -> dict:
        """Executa um step com retry e timeout."""

    def should_checkpoint(self, step: SupremeStep) -> bool:
        """Verifica se step requer parada para aprovação."""

    def pause_at_checkpoint(self, step: SupremeStep, 
                            result: AutonomousResult) -> AutonomousResult:
        """Pausa execução em gate crítico."""

    def resume(self, result: AutonomousResult) -> AutonomousResult:
        """Retoma execução do último checkpoint."""


class CheckpointManager:
    """Gerencia gates de aprovação durante execução autônoma."""

    def is_checkpoint_action(self, step: SupremeStep) -> bool: ...
    def request_approval(self, step: SupremeStep, context: dict) -> GovernanceDecision: ...
    def get_pending_checkpoints(self, result: AutonomousResult) -> list[str]: ...


class CircuitBreaker:
    """Detecta padrões de falha e decide pausar."""

    def __init__(self, threshold: int = 3): ...
    def record_failure(self, step_id: str) -> None: ...
    def record_success(self, step_id: str) -> None: ...
    def is_open(self) -> bool: ...  # True se threshold atingido
    def reset(self) -> None: ...


class RecoveryManager:
    """Gerencia retry, resume e rollback."""

    def retry_step(self, step: SupremeStep, error: Exception, 
                   attempt: int) -> bool:  # True = retry, False = abort
        ...

    def can_resume(self, result: AutonomousResult) -> bool: ...

    def get_resume_point(self, result: AutonomousResult) -> int:  # step index
        ...
```

---

## 11. CLI COMMANDS SUGERIDOS

```python
@autonomous.command()
@click.argument("plan_id")
@click.option("--mode", type=click.Choice(["interactive", "autonomous"]), 
              default="autonomous")
def run(plan_id: str, mode: str):
    """Executa um plano de forma autônoma."""

@autonomous.command()
@click.argument("run_id")
def resume(run_id: str):
    """Retoma execução pausada em checkpoint."""

@autonomous.command()
@click.argument("run_id")
def status(run_id: str):
    """Status em tempo real da execução autônoma."""

@autonomous.command()
@click.argument("run_id")
def cancel(run_id: str):
    """Cancela execução autônoma em andamento."""
```

---

## 12. TEST STRATEGY

### Meta: ≥ 80 testes

| Arquivo | Testes | Foco |
|---|---|---|
| `test_models.py` | 15+ | AutonomousConfig, AutonomousResult, AutonomousState transições |
| `test_executor.py` | 25+ | execute() com plan de 5 steps, checkpoints parando corretamente, resume funcional, timeout de step, timeout de missão |
| `test_checkpoint.py` | 10+ | is_checkpoint_action() para cada action type, approval request gerado, pending checkpoints listados |
| `test_circuit_breaker.py` | 10+ | record_failure incrementa, abre após threshold, reset funciona, success reseta contador |
| `test_recovery.py` | 10+ | retry_step com 1ª/2ª/3ª tentativa, can_resume true/false, get_resume_point correto |
| `test_e2e_autonomous.py` | 10+ | Missão completa autônoma com mock de steps, checkpoint pause/resume, circuit breaker trip |

---

## 13. DRY-RUN STRATEGY

```python
class AutonomousExecutor:
    def __init__(self, config: AutonomousConfig):
        self.dry_run = config.dry_run  # default True

    def execute(self, plan: SupremePlan) -> AutonomousResult:
        if self.dry_run:
            # Simula todos os steps sem efeitos colaterais
            # Cada step retorna resultado simulado
            # Checkpoints são registrados mas não param execução
            pass
```

**dry_run=True:**
- Steps executam com resultado simulado (via adapters com dry_run)
- Checkpoints são registrados no log mas não pausam
- Tempo real de execução (sem timeouts acelerados)

**dry_run=False:**
- Steps executam com resultado real
- Checkpoints pausam e aguardam operador
- Timeouts são aplicados

---

## 14. FAILURE / RECOVERY

| Cenário | Comportamento | Recovery |
|---|---|---|
| Step falha 1x | Retry automático após backoff | Se passar no retry, continua |
| Step falha 3x | Step marcado FAILED | Circuit breaker incrementa |
| 3 falhas consecutivas | Circuit breaker abre → PAUSED_ERROR | Operador decide: skip step, retry all, ou abort |
| Timeout de step (5min) | Step marcado TIMEOUT | Passa para próximo step com warning |
| Timeout de missão (30min) | PAUSED_TIMEOUT | Operador decide: estender timeout ou finalizar |
| Checkpoint não aprovado | PAUSED_CHECKPOINT indefinidamente | Operador aprova/rejeita |
| Falha irrecuperável | FAILED | Relatório parcial gerado, aprendizados → P21 |

---

## 15. RISCOS ARQUITETURAIS

| # | Risco | Impacto | Prob | Mitigação |
|---|---|---|---|---|
| R1 | Execução autônoma executar ação real sem aprovação | Crítico | Baixa | CheckpointManager bloqueia SEND/DEPLOY/FINANCIAL/DELETE |
| R2 | Loop infinito de retry | Médio — recurso | Baixa | Max 3 retries + circuit breaker |
| R3 | Timeout muito curto matar missões legítimas | Baixo | Média | Configurável por missão. Defaults generosos (5min/step) |
| R4 | Operador perder visibilidade durante execução longa | Médio | Média | Progress tracking via P16. Notification em checkpoints |
| R5 | Resume de missão pausada corromper estado | Alto | Baixa | Steps são idempotentes. Resume do último checkpoint confirmado |

---

## 16. ANTI-PATTERNS PROIBIDOS

```
✗ AUTO-APROVAR GATES CRÍTICOS — bypass de checkpoint em SEND/DEPLOY/FINANCIAL/DELETE
✗ EXECUÇÃO PARALELA NO MVP — v1 é sequencial
✗ MODIFICAR PLANO DURANTE EXECUÇÃO — plano aprovado é imutável
✗ IGNORAR TIMEOUTS — steps sem timeout podem travar
✗ EXECUTAR SEM TRACING — todo step deve gerar TraceEvent
✗ RESUME SEM VERIFICAÇÃO DE ESTADO — validar que missão está realmente pausada
```

---

## 17. CRITÉRIOS DE ACEITE

- [ ] Namespace `src/autonomous_execution/` com 8 arquivos
- [ ] Testes ≥ 80 (targeted), todos passando
- [ ] AutonomousExecutor.execute() funcional com plan de 5+ steps
- [ ] CheckpointManager bloqueia SEND/DEPLOY/FINANCIAL/DELETE
- [ ] CircuitBreaker abre após 3 falhas consecutivas
- [ ] Retry automático (até 3x) funcional
- [ ] Resume de checkpoint funcional
- [ ] Timeout de step e missão configuráveis
- [ ] dry_run=True default
- [ ] Zero imports de módulos proibidos
- [ ] Zero toques em P20 (apenas estende)
- [ ] Full suite sem regressões

---

## 18. ORDEM INCREMENTAL

### M1: Models + Errors
- `models.py`, `errors.py`
- `test_models.py` — 15+ testes

### M2: Checkpoint + Circuit Breaker
- `checkpoint.py`, `circuit_breaker.py`
- `test_checkpoint.py` + `test_circuit_breaker.py` — 20+ testes

### M3: Recovery + Executor Core
- `recovery.py`, `executor.py` (execute, execute_step_autonomous)
- `test_recovery.py` + `test_executor.py` — 35+ testes

### M4: Resume + Timeout
- Atualizar `executor.py` — resume, timeout handling
- Completar `test_executor.py`

### M5: CLI + E2E + Docs
- `cli.py`, `test_e2e_autonomous.py` — 10+ testes
- `__init__.py`, skeleton doc
- Full suite validation

---

## 19. RECOMENDAÇÃO DE PARALELIZAÇÃO

**1 frente única.** P23 é linear e coesa. Circuit breaker e recovery dependem dos modelos. Executor depende de checkpoint + recovery. Sem paralelismo viável.

---

*OMNIS Control Tower — P23 Autonomous Execution Architecture.*
