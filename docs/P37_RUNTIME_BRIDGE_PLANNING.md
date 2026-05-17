# P37 RuntimeBridge — Planejamento

**Date:** 2026-05-16
**Auditor:** agent-architect (OMNIS CCOS)
**Epic:** P37 — RuntimeBridge
**Suite baseline:** 6955 passed, 2 skipped
**Status:** PLANEJADO — zero implementacao

---

## 1. Resumo Executivo

**execution_graph e execution_queue NAO se importam diretamente.** Zero acoplamento estatico entre os dois modulos. A ponte esta AUSENTE — nao e que existe acoplamento a ser reduzido; o problema e que a transformacao `StepRun → QueueItem` nao existe em lugar nenhum.

O unico ponto onde execution_queue e usado e `src/omnis_control/pipeline.py`, que constroi QueueItems manualmente a partir de work orders, ignorando completamente o pipeline de graph.

**Tarefa real do P37:** Criar `src/runtime_bridge/` como modulo novo que transforma `StepRun` (saida do execution_graph) em `QueueItem`(s) (entrada do execution_queue), estabelecendo um contrato explicito entre os dois dominios.

---

## 2. Mapa de Acoplamento Atual

### 2.1 execution_graph (17 arquivos, 0 imports de execution_queue)

| Arquivo | Importa de |
|---|---|
| `__init__.py` | models, builder, validator, errors (tudo interno) |
| `builder.py` | models, errors internos |
| `runner.py` | models, errors, retry, circuit_breaker, rollback (tudo interno) |
| `mission_bridge.py` | mission_orchestrator, squad_composer, task_decomposer, builder, runner, store |
| `approval_bridge.py` | models, approval_center, runner |
| `events.py` | models (internal) |
| `metrics.py` | events (internal) |
| `replay.py` | models, runner, store (tudo interno) |
| `store.py` | pathlib apenas |
| `circuit_breaker.py` | interno |
| `retry.py` | interno |
| `rollback.py` | models interno |
| `validator.py` | models interno |

### 2.2 execution_queue (5 arquivos, 0 imports de execution_graph)

| Arquivo | Importa de |
|---|---|
| `__init__.py` | models, queue, runner, state, errors (tudo interno) |
| `queue.py` | models, state, errors (tudo interno) |
| `runner.py` | models, queue, errors (tudo interno) |
| `state.py` | models, errors (tudo interno) |
| `models.py` | dataclasses, enum, uuid, datetime |

### 2.3 Onde execution_queue e usado fora do seu modulo

| Arquivo | Como usa |
|---|---|
| `src/omnis_control/pipeline.py:16-17` | Importa `ExecutionQueue` e `QueueItem`. Constroi QueueItem manualmente no metodo `execute()`. |

**So 1 arquivo em todo src/ importa de execution_queue. E ele nao importa de execution_graph.**

### 2.4 Onde execution_graph e usado fora do seu modulo

| Arquivo | Como usa |
|---|---|
| `src/work_order/graph_integration.py` | Importa models, runner, approval_bridge. Faz graph→work_order, nao graph→queue. |
| `src/work_order/builder.py` | Importa models. |
| `src/cli_commands/execution_graph_cmd.py` | CLI — importa builder, runner, store, replay. |
| `src/cli_commands/mission_orchestrator_cmd.py` | CLI — importa mission_bridge.run_full_pipeline. |
| `src/cli_commands/work_order_cmd.py` | CLI — importa mission_bridge, runner. |
| `src/mission_orchestrator/planner.py` | Referencia. |
| `src/routers/system_router.py` | Referencia. |
| `src/campaign_manager/service.py` | Referencia. |

---

## 3. Arquivos que P37 Tocara

### 3.1 Criar (4 novos)

| Arquivo | Proposito | Estimativa |
|---|---|---|
| `src/runtime_bridge/__init__.py` | Exports publicos: `RuntimeBridge`, `bridge_step_run`, `BridgeResult` | ~15 linhas |
| `src/runtime_bridge/bridge.py` | Logica core: `RuntimeBridge` class com metodo `bridge(step_run) → BridgeResult` | ~80 linhas |
| `src/runtime_bridge/models.py` | `BridgeResult` dataclass + status mapping StepStatus→QueueItemStatus | ~50 linhas |
| `src/runtime_bridge/errors.py` | `BridgeError`, `BridgeMappingError` | ~20 linhas |

### 3.2 NAO modificar (somente leitura)

| Arquivo | Motivo |
|---|---|
| `src/execution_graph/models.py` | Le StepRun, StepRunLog, StepStatus, ExecutionGraph |
| `src/execution_graph/runner.py` | Le StepRun (retorno de run_graph_dry) |
| `src/execution_queue/models.py` | Le QueueItem, QueueItemStatus, QueueResult |
| `src/execution_queue/queue.py` | Le ExecutionQueue (enqueue, validate, run) |

### 3.3 Modificar (opcional, BAIXA prioridade)

| Arquivo | Mudanca |
|---|---|
| `src/omnis_control/pipeline.py` | Refatorar Step 9 para usar RuntimeBridge em vez de construir QueueItem manualmente |

**A modificacao do pipeline e opcional e pode ser feita em onda separada (ex: P37b).**

---

## 4. Interface Proposta do RuntimeBridge

### 4.1 Contrato publico

```python
# src/runtime_bridge/__init__.py

@dataclass
class BridgeResult:
    """Resultado da ponte graph→queue."""
    graph_run_id: str
    queue_items: list[QueueItem]        # itens criados na fila
    mapping: dict[str, str]              # step_id -> item_id
    items_blocked: int = 0
    items_ready: int = 0
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict: ...
    @classmethod
    def from_dict(cls, d: dict) -> BridgeResult: ...


class RuntimeBridge:
    """Ponte entre ExecutionGraph e ExecutionQueue."""

    def __init__(self, queue: ExecutionQueue, dry_run: bool = True): ...

    def bridge(
        self,
        step_run: StepRun,
        *,
        risk_level: str = "low",
        requires_approval: bool = False,
    ) -> BridgeResult: ...
    # Converte cada StepRunLog com status DONE em QueueItem READY.
    # Steps SKIPPED/FAILED geram itens BLOCKED com reason.

    def bridge_and_validate(self, step_run: StepRun, **kw) -> BridgeResult: ...
    # bridge() + queue.validate() em cada item.

    def bridge_and_run(self, step_run: StepRun, **kw) -> BridgeResult: ...
    # bridge() + queue.validate() + queue.run() em cada item READY.
```

### 4.2 StepStatus → QueueItemStatus mapping

| StepRunLog.status | QueueItemStatus | Descricao |
|---|---|---|
| `running` | — (pulado) | Step em execucao nao gera QueueItem |
| `done` | `ready` | Output simulado disponivel, pronto para executar |
| `failed` | `blocked` | Erro na simulacao, bloqueado com reason |
| `skipped` | `blocked` | Dependencia falhou, bloqueado com reason |

### 4.3 Por que esse design?

1. **dry_run=True como default** — coerente com as regras universais do OMNIS.
2. **Injecao de dependencia** — bridge recebe ExecutionQueue no construtor, nao instancia internamente. Facilita mock em testes.
3. **BridgeResult como unica saida** — um unico objeto com mapeamento bidirecional (step_id ↔ item_id), facil de logar e auditar.
4. **Metodos compostos opcionais** — `bridge_and_validate` / `bridge_and_run` sao conveniencia; o metodo base `bridge()` so transforma, sem efeito colateral.
5. **Nao modifica models existentes** — zero risco de breaking change nos modulos graph/queue.

---

## 5. Riscos de Contrato

| Risco | Probabilidade | Impacto | Mitigacao |
|---|---|---|---|
| `StepRunLog` nao ter campos suficientes para popular `QueueItem` | BAIXA | MEDIO | StepRunLog tem step_id, role_id, status, message — suficiente |
| `QueueItemStatus` nao aceitar transicoes de estado esperadas | BAIXA | BAIXO | Validar `VALID_TRANSITIONS` antes de chamar queue.state.transition |
| `StepRun.logs` conter multiplos logs por step (RUNNING + DONE) | ALTA | MEDIO | Filtrar apenas o ultimo log de cada step_id (status final) |
| `ExecutionGraph` model mudar e quebrar o bridge | MEDIA | BAIXO | Bridge le apenas a interface publica (StepRun, StepRunLog); mudancas internas no graph nao afetam |
| Pipeline de producao (`omnis_control/pipeline.py`) ter comportamento divergente do bridge | MEDIA | ALTO | NAO mexer no pipeline na primeira versao do P37; bridge e standalone |
| `StepRun.blocked()` retornar estrutura diferente de `run_graph_dry()` | BAIXA | MEDIO | Verificar StepRun.blocked() como edge case |

---

## 6. Plano de Execucao em Etapas (5 blocos)

```
B1 — Model + Errors (15 min)
  Criar src/runtime_bridge/models.py (BridgeResult) + errors.py
  Round-trip to_dict/from_dict no BridgeResult

B2 — Core Bridge (30 min)
  Criar src/runtime_bridge/bridge.py com RuntimeBridge.bridge()
  Status mapping table
  Logica de filtro: ultimo log por step_id

B3 — Dry-run + Validate (20 min)
  Metodos bridge_and_validate, bridge_and_run
  dry_run=True em todo fluxo
  Gate: nao chamar queue.run() se dry_run=True e item.dry_run_required

B4 — Tests (30 min)
  Criar tests/runtime_bridge/test_bridge.py (~15 testes)
  Casos minimos:
    - bridge with all DONE steps → all READY
    - bridge with FAILED step → downstream BLOCKED
    - bridge with SKIPPED steps → BLOCKED
    - bridge empty StepRun → BridgeResult vazio
    - bridge_and_validate with dry_run → DRY_RUN status
    - bridge_and_run with approval required → WAITING_APPROVAL
    - round-trip BridgeResult.to_dict/from_dict
    - status mapping table completo
    - bridge with StepRun.blocked() (edge case)
    - dry_run=True: queue.run() nunca chamado

B5 — CLI + Docs + Commit (20 min)
  Export em __init__.py
  Atualizar docs/supreme_210/reports/
  Commit convencional
```

**Tempo total estimado:** ~2h

---

## 7. Testes Minimos Esperados

| # | Cenario | Esperado |
|---|---|---|
| 1 | StepRun com 3 steps DONE | 3 QueueItems READY, BridgeResult.items_ready=3 |
| 2 | StepRun com 1 FAILED + 2 downstream | 1 BLOCKED (o failed) + 2 SKIPPED (os downstream) |
| 3 | StepRun vazio (sem logs) | BridgeResult com items vazio, sem erros |
| 4 | bridge_and_validate com dry_run_required=True | Itens com status DRY_RUN, nao READY |
| 5 | bridge_and_run com approval required | Itens WAITING_APPROVAL, nao executados |
| 6 | BridgeResult.to_dict/from_dict round-trip | Campos identicos |
| 7 | Status mapping: todos os StepStatus tem mapping | Sem KeyError |
| 8 | Multiplos logs por step (RUNNING + DONE) | So o ultimo log (DONE) gera QueueItem |
| 9 | QueueRunner.process com item READY e dry_run=True | QueueResult com dry-run, sem execucao real |
| 10 | RuntimeBridge com dry_run=True | bridge_and_run NAO chama queue.run() |

**Total esperado:** ~15 testes novos, todos passando em < 1 segundo.

---

## 8. Criterio de Pronto

- [ ] 3+ arquivos criados em `src/runtime_bridge/`
- [ ] `RuntimeBridge.bridge()` funcional com status mapping completo
- [ ] dry_run=True como default universal
- [ ] `BridgeResult.to_dict()/from_dict()` round-trip
- [ ] 15+ testes targeted passando: `python -m pytest tests/runtime_bridge/`
- [ ] Suite completa verde (6955+)
- [ ] Import scan limpo: `grep -r "secret\|token=\|api_key=" src/runtime_bridge/` vazio
- [ ] `docs/supreme_210/reports/P37_RUNTIME_BRIDGE_REPORT.md` gerado
- [ ] Commit com mensagem `feat(omnis): P37 runtime bridge graph to queue`

---

## 9. Recomendacao

**P37 esta pronto para iniciar implementacao. Worktree pode ser criada.**

Zero dependencias bloqueantes. O escopo e autocontido — modulo novo que le de dois modulos existentes sem modifica-los.

### Proximo comando seguro apos aprovacao

```powershell
# Opcao A: Criar worktree dedicada
git worktree add ../omnis-runtime-bridge -b feat/p37-runtime-bridge
cd ../omnis-runtime-bridge

# Opcao B: Continuar na branch atual (feature/omnis-5waves-runtime-supreme)
# sem criar worktree separada
```

**Recomendo Opcao B** — P37 e modular e nao colide com outros epicos. Nao justifica worktree dedicada a menos que Lucas queira paralelizar P37 com P38/P39 depois.

### Proximo prompt

```
Atue como agent-executor do OMNIS CCOS.
Execute P37 RuntimeBridge conforme docs/P37_RUNTIME_BRIDGE_PLANNING.md.
Escopo travado. dry_run=True. Gerar handoff report.
```

---

## 10. Observacoes

- `docs/implementation/W131_APP_IDEA_INTAKE_PLAN.md` permanece nao rastreado, fora do escopo de P37.
- 4 worktrees stale (P20, P23, P24, P25-P29) continuam no disco — nao bloqueiam P37.
- `REGISTRY.md` ja foi atualizado na microfase de saneamento.
- A interface proposta e minimalista de proposito — evita overengineering. Se houver necessidade de mais metodos (ex: `bridge_partial` para steps especificos), expandir em P41.

---

*Plano gerado por agent-architect — 2026-05-16*
