# P27 — REAL WORLD ACTIONS ARCHITECTURE

> **Data:** 2026-05-14
> **Status:** ARCHITECTURE DRAFT — Aguardando revisão
> **Base:** master pós-P24 (4604 testes, 0 regressões)
> **Pré-requisitos:** P23 Autonomous + P24 Cockpit + P18 Governance + P25 Multi-Model

---

## 1. DEFINIÇÃO

P27 Real World Actions é a camada de **ações externas controladas** do OMNIS. Até agora, o OMNIS opera em modo read-only ou simulação: planeja, analisa, gera código, mas não executa ações no mundo real. O P27 adiciona a capacidade de **enviar, publicar, disparar, notificar, e integrar** com serviços externos — sempre com approval gates, sandbox de execução, e rastreamento de auditoria.

---

## 2. PROBLEMA QUE RESOLVE

**Atual:** OMNIS pode planejar um post (P8), gerar legenda, e até agendar (ARGOS) — mas são módulos separados com padrões inconsistentes. Para ações como "enviar email para lead", "postar no Instagram", "disparar webhook no n8n", "publicar no GitHub", não há camada unificada. Cada ação real requer intervenção manual do operador.

**Com P27:** OMNIS ganha um **Action Executor** unificado com:
- Catálogo de ações disponíveis
- Sandbox que bloqueia ações não-autorizadas
- Approval chain obrigatória para ações de risco
- Rastreamento completo (audit log)
- Dry-run que mostra o que SERIA feito sem executar

---

## 3. O QUE FAZ

1. **Action Registry** — catálogo de ações disponíveis (send_email, post_instagram, call_webhook, git_push, etc.)
2. **Action Executor** — executa ações com sandbox e timeout
3. **Approval Chain** — toda ação SEND/DEPLOY/FINANCIAL/DELETE requer approval (P18)
4. **Action Sandbox** — bloqueia ações não-registradas, limita rate, valida inputs
5. **Audit Trail** — toda ação real gera AuditEvent (P18) + entrada no cockpit (P24)
6. **Retry Policy** — ações que falham por timeout/network podem ser retried
7. **Dry-Run Preview** — "se eu executasse, isso aconteceria: ..."
8. **Provider Adapters** — thin wrappers para cada serviço externo (Gmail, Instagram API, GitHub, n8n, etc.)

---

## 4. O QUE NÃO FAZ

| PROIBIDO | Motivo |
|---|---|
| Executar ação sem approval gate | Toda ação de risco para em checkpoint |
| Bypassar o P18 Governance | P27 USA P18, não substitui |
| Ser um workflow engine completo (n8n) | n8n já existe. P27 é executor de ações pontuais |
| Fazer scraping não-autorizado | Toda ação externa é declarada no registry |
| Gerenciar OAuth tokens diretamente | Tokens ficam em credenciais do sistema. P27 só referencia |
| Auto-aprovar ações em produção | dry_run=False + risco critical = sempre requer approval humano |
| Executar ações em paralelo sem limite | Max 3 ações simultâneas. Rate limiting por action type |

---

## 5. RELAÇÃO COM P20 SUPREME

P27 expõe ações como **steps executáveis** dentro de missões:

```python
# P20 SupremePlan com steps P27:
plan = SupremePlan.new(
    steps=[
        SupremeStep(intent="analyze_lead"),            # P20 normal
        SupremeStep(intent="send_email",               # P27 action
                    context={"to": "lead@email.com", "template": "follow_up"}),
        SupremeStep(intent="log_contact",              # P27 action
                    context={"crm": "hubspot", "lead_id": "..."}),
    ]
)
```

O P20 não sabe COMO enviar email — só sabe que o step `send_email` existe no Action Registry.

---

## 6. RELAÇÃO COM P21 MEMORY

P21 armazena **histórico de ações reais**:

- "Email para lead X enviado em 2026-05-10, resposta em 2 dias"
- "Post no Instagram Y teve Z engajamento" (correlacionando ação → resultado)
- "Webhook Z falhou 3x em maio — provider instável"

Isso permite que o P28 (Self-Improvement) analise eficácia de ações.

---

## 7. RELAÇÃO COM P22 FORGE

P22 pode **gerar novos Action Adapters** sob demanda:

- "Preciso de um adapter para enviar mensagem no WhatsApp Business"
- P22 gera `whatsapp_adapter.py` seguindo o contrato `ActionAdapter`
- Após review → registrado no Action Registry

P27 fornece o contrato. P22 gera a implementação.

---

## 8. RELAÇÃO COM P23 AUTONOMOUS EXECUTION

P27 é o **principal consumidor dos checkpoints do P23**:

| Action Type | Risco | Checkpoint? |
|---|---|---|
| `read` | low | Não — executa direto |
| `write` (rascunho) | medium | Sim — approval antes de salvar |
| `send` (email, mensagem) | high | Sim — approval obrigatório |
| `deploy` | critical | Sim — dupla confirmação |
| `financial` | critical | Sim — dupla confirmação |
| `delete` | critical | Sim — dupla confirmação |

O circuito breaker do P23 também monitora falhas consecutivas de ação.

---

## 9. RELAÇÃO COM P24 LIVE COCKPIT

P24 mostra:

- **Ações pendentes de approval** — fila de checkpoints P27
- **Ações executadas hoje** — com status (success/failed/pending)
- **Rate limit status** — quantas ações cada provider ainda aceita
- **Alertas** — ação bloqueada por governance, adapter offline, rate limit atingido

---

## 10. CONTRATOS PRINCIPAIS

### 10.1 ActionDefinition

```python
@dataclass
class ActionDefinition:
    action_id: str             # "rwa_<8hex>"
    name: str                  # "send_email", "post_instagram", "call_webhook"
    provider: str              # "gmail", "instagram", "github", "n8n", "webhook"
    action_type: str           # read | write | send | deploy | financial | delete
    risk_level: str            # low | medium | high | critical
    requires_approval: bool     # derivado de risk_level >= high
    input_schema: dict          # JSON Schema dos parâmetros esperados
    output_schema: dict         # JSON Schema do retorno
    rate_limit: RateLimit       # max por hora/dia
    timeout_seconds: int        # timeout da ação
    retry_policy: RetryPolicy   # max retries, backoff
    enabled: bool
```

### 10.2 ActionRequest / ActionResult

```python
@dataclass
class ActionRequest:
    request_id: str            # "rwq_<8hex>"
    action_id: str             # qual ação executar
    params: dict               # parâmetros validados contra input_schema
    dry_run: bool              # default True
    mission_id: str            # missão que originou a ação
    step_id: str               # step que originou a ação
    approved_by: str           # quem aprovou (ou "system" para dry_run)

@dataclass
class ActionResult:
    result_id: str             # "rwr_<8hex>"
    request_id: str
    status: str                # "success" | "failed" | "dry_run" | "blocked" | "timeout"
    output: dict               # resposta padronizada
    error: str
    audit_event_id: str        # referencia AuditEvent do P18
    latency_ms: int
    retry_count: int
    executed_at: str
```

### 10.3 ActionAdapter (protocol)

```python
class ActionAdapter(Protocol):
    """Contrato mínimo para adapter de ação externa."""

    provider: str              # "gmail", "instagram", "github", etc.
    supported_actions: list[str]

    def execute(self, action: ActionDefinition, params: dict) -> dict:
        """Executa ação real. Levanta ActionError em falha."""
        ...

    def health_check(self) -> bool:
        """True se o serviço externo está acessível."""
        ...

    def validate_params(self, action: ActionDefinition, params: dict) -> list[str]:
        """Retorna lista de erros de validação (vazia = ok)."""
        ...
```

---

## 11. STATE / FLOW

```
┌──────────────────────────────────────────────────────────────────┐
│                    P27 ACTION EXECUTION FLOW                      │
│                                                                   │
│  [P20/P23] Step: "send_email"                                    │
│     │                                                             │
│  ┌──▼──────────────────────────────────────────────────────────┐ │
│  │ 1. ACTION RESOLUTION                                          │ │
│  │    ActionRegistry.find("send_email") → ActionDefinition      │ │
│  │    Se não encontrada → UnknownActionError                     │ │
│  └──────────────────────────────────────────────────────────────┘ │
│     │                                                             │
│  ┌──▼──────────────────────────────────────────────────────────┐ │
│  │ 2. VALIDATION                                                 │ │
│  │    ActionSandbox.validate(action, params) → erros?           │ │
│  │    RateLimiter.check(provider) → permitido?                  │ │
│  │    Se não passar → ActionBlockedError                         │ │
│  └──────────────────────────────────────────────────────────────┘ │
│     │                                                             │
│  ┌──▼──────────────────────────────────────────────────────────┐ │
│  │ 3. GOVERNANCE ◀── P18                                         │ │
│  │    if action.risk_level >= "high":                            │ │
│  │        ApprovalGate.request(action, params)                   │ │
│  │        if denied → ActionDeniedError + AuditEvent             │ │
│  │    if dry_run:                                                │ │
│  │        return preview (pula steps 4-5)                        │ │
│  └──────────────────────────────────────────────────────────────┘ │
│     │                                                             │
│  ┌──▼──────────────────────────────────────────────────────────┐ │
│  │ 4. SANDBOX EXECUTION                                          │ │
│  │    adapter = ActionRegistry.get_adapter(action.provider)      │ │
│  │    result = adapter.execute(action, params)                   │ │
│  │    timeout: action.timeout_seconds                            │ │
│  │    failure → retry conforme action.retry_policy               │ │
│  └──────────────────────────────────────────────────────────────┘ │
│     │                                                             │
│  ┌──▼──────────────────────────────────────────────────────────┐ │
│  │ 5. AUDIT + FEEDBACK                                           │ │
│  │    AuditLog.record_event(AuditEvent.new(...))                 │ │
│  │    P24 cockpit: incrementa contador de ações                  │ │
│  │    P21 memory: armazena ação para análise futura              │ │
│  └──────────────────────────────────────────────────────────────┘ │
│     │                                                             │
│     ▼                                                             │
│  [ActionResult] status="success" → próximo step                  │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 12. ARQUIVOS SUGERIDOS

```
src/real_world_actions/
├── __init__.py               # Exports: ActionRegistry, ActionExecutor, ActionSandbox, etc.
├── models.py                 # ActionDefinition, ActionRequest, ActionResult, RateLimit, RetryPolicy
├── errors.py                 # ActionError, ActionBlockedError, AdapterUnavailableError, RateLimitError
├── registry.py               # ActionRegistry — cadastro, busca, enable/disable
├── executor.py               # ActionExecutor — executa ação com sandbox + retry + timeout
├── sandbox.py                # ActionSandbox — validação, rate limit, bloqueio de ações
├── approval_chain.py         # ApprovalChain — integração com P18 Governance
├── adapters/
│   ├── __init__.py           # ADAPTER_REGISTRY
│   ├── email_adapter.py      # EmailAdapter (Gmail SMTP)
│   ├── instagram_adapter.py  # InstagramAdapter (Graph API)
│   ├── webhook_adapter.py    # WebhookAdapter (HTTP POST)
│   ├── github_adapter.py     # GitHubAdapter (gh CLI / API)
│   ├── n8n_adapter.py        # N8nAdapter (webhook trigger)
│   └── mock_adapter.py       # MockAdapter para testes/dry-run
├── rate_limiter.py           # RateLimiter — controle de taxa por provider/ação
└── cli.py                    # CLI: action list, action execute, action approve, action history

tests/real_world_actions/
├── test_models.py            # 15+ testes
├── test_registry.py          # 12+ testes
├── test_executor.py          # 15+ testes
├── test_sandbox.py           # 12+ testes
├── test_approval_chain.py    # 12+ testes
├── test_adapters.py          # 12+ testes
├── test_rate_limiter.py      # 10+ testes
└── test_e2e_actions.py       # 12+ testes

docs/real_world_actions/
└── P27_REAL_WORLD_ACTIONS_ARCHITECTURE.md
```

**Total: 13 source + 8 test + 1 doc = 22 arquivos**

---

## 13. CLASSES SUGERIDAS

```python
class ActionRegistry:
    """Registro de ações disponíveis."""
    def register(action: ActionDefinition) -> None: ...
    def find(name: str) -> ActionDefinition: ...
    def list_by_provider(provider: str) -> list[ActionDefinition]: ...
    def list_by_risk(risk_level: str) -> list[ActionDefinition]: ...
    def enable(action_id: str) -> None: ...
    def disable(action_id: str) -> None: ...

class ActionSandbox:
    """Sandbox que bloqueia ações não-registradas, valida inputs, limita rate."""
    def validate(action: ActionDefinition, params: dict) -> list[str]: ...
    def check_rate(action: ActionDefinition) -> bool: ...
    def is_allowed(action: ActionDefinition) -> bool: ...
    def preview(action: ActionDefinition, params: dict) -> dict: ...

class ActionExecutor:
    """Executor principal — sandbox → approval → execute → audit."""
    def __init__(self, dry_run: bool = True): ...
    def execute(self, request: ActionRequest) -> ActionResult: ...
    def execute_batch(self, requests: list[ActionRequest]) -> list[ActionResult]: ...
    def get_adapter(self, provider: str) -> ActionAdapter: ...

class ApprovalChain:
    """Bridge com P18 Governance — toda ação de risco para aqui."""
    def __init__(self, governance: ApprovalPolicyEngine): ...
    def request_approval(self, action: ActionDefinition, params: dict) -> GovernanceDecision: ...
    def is_auto_approved(self, action: ActionDefinition) -> bool: ...
    def get_pending(self) -> list[ActionRequest]: ...

class RateLimiter:
    """Controle de taxa por provider/ação."""
    def check(self, provider: str, action: str) -> bool: ...
    def record(self, provider: str, action: str) -> None: ...
    def remaining(self, provider: str, action: str) -> int: ...
    def reset(self, provider: str) -> None: ...
```

---

## 14. CLI COMMANDS SUGERIDOS

```
action list [--provider gmail|instagram|...]   # Lista ações disponíveis
action preview <action_name> [--params '...']   # Dry-run: mostra o que seria feito
action execute <action_name> [--params '...'] [--approve]  # Executa ação real
action approve <request_id>                     # Aprova ação pendente
action deny <request_id> [--reason "..."]       # Nega ação pendente
action history [--limit 20] [--status failed]   # Histórico de ações
action providers                                 # Lista providers e saúde
```

---

## 15. TEST STRATEGY

| Arquivo | Testes | Foco |
|---|---|---|
| `test_models.py` | 15+ | ActionDefinition.new(), ActionRequest validation, ActionResult status |
| `test_registry.py` | 12+ | Register, find, enable/disable, listagem por risco/provider |
| `test_executor.py` | 15+ | Dry-run retorna preview. Execução real com mock adapter. Timeout. Retry. |
| `test_sandbox.py` | 12+ | Validação de params contra schema. Bloqueio de ação não-registrada. Rate limit. |
| `test_approval_chain.py` | 12+ | Ação low auto-aprovada. Ação critical requer approval. Integração P18. |
| `test_adapters.py` | 12+ | Mock adapter. Cada adapter real implementa contrato. Health check. |
| `test_rate_limiter.py` | 10+ | Check/record/reset. Limite por provider e por ação. |
| `test_e2e_actions.py` | 12+ | Registry → Sandbox → Approval → Execute → Audit. Cycle completo. |

**Meta: ≥ 100 testes**

---

## 16. DRY-RUN STRATEGY

```python
class ActionExecutor:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run

    def execute(self, request: ActionRequest) -> ActionResult:
        action = self.registry.find(request.action_id)
        errors = self.sandbox.validate(action, request.params)

        if self.dry_run:
            return ActionResult(
                status="dry_run",
                output={
                    "action": action.name,
                    "provider": action.provider,
                    "params": request.params,
                    "validation_errors": errors,
                    "would_execute": len(errors) == 0,
                    "requires_approval": action.requires_approval,
                },
                ...
            )
        # Execução real continua...
```

Dry-run = preview completo. Mostra o que SERIA feito, quais parâmetros, se passaria validação, se requer aprovação.

---

## 17. APPROVAL STRATEGY

Usa P18 `ApprovalPolicyEngine` e `GovernanceDecision`:

| Risco | Auto-approve? | Requer |
|---|---|---|
| `low` (read) | Sim | Nada |
| `medium` (write rascunho) | Sim, com log | AuditEvent gerado |
| `high` (send) | Não | 1 aprovação do operador |
| `critical` (deploy, financial, delete) | Não | Dupla confirmação (2 approvals) |

Ações `critical` também pedem `reason` obrigatório no approval.

---

## 18. FAILURE / RECOVERY

| Falha | Comportamento |
|---|---|
| Provider offline (health check falha) | `AdapterUnavailableError`. Ação bloqueada até provider voltar |
| Timeout na execução | Retry até `max_retries`. Se esgotar → `ActionResult(status="timeout")` |
| Rate limit atingido | `RateLimitError`. Ação bloqueada até janela resetar |
| Parâmetros inválidos | `ActionBlockedError` com lista de erros de validação |
| Ação negada pelo approval | `ActionDeniedError` + AuditEvent. Missão registra negação |
| Adapter retorna erro inesperado | Capturado como `ActionResult(status="failed")`. Não quebra missão |
| Ação parcialmente executada (ex: email enviado mas log falhou) | `ActionResult(status="partial")`. Alerta no P24 |

---

## 19. RISCOS ARQUITETURAIS

| # | Risco | Impacto | Prob | Mitigação |
|---|---|---|---|---|
| R1 | Ação real executada sem approval | Crítico | Muito Baixa | Sandbox bloqueia. Approval chain é síncrono e obrigatório |
| R2 | Vazamento de credenciais em logs | Crítico | Baixa | Adapters nunca logam secrets. Params são sanitizados antes de log |
| R3 | Ação irreversível executada por engano | Alto | Baixa | Delete/financial requer dupla confirmação + reason obrigatório |
| R4 | Rate limit de API externa estourado | Médio | Média | RateLimiter preventivo. Dry-run não consome cota |
| R5 | Adapter Instagram quebrar com mudança de API | Médio | Média | Adapter isolado. Saúde monitorada via P16. Fallback para mock |

---

## 20. ANTI-PATTERNS PROIBIDOS

```
✗ EXECUTAR SEM APPROVAL — toda ação >= high risco para em checkpoint
✗ BYPASSAR GOVERNANCE — P27 USA P18. Nunca implementa própria governance
✗ ADAPTERS COM LÓGICA DE NEGÓCIO — adapter é thin wrapper HTTP/SMTP
✗ HARDCODED CREDENCIAIS — credenciais via env vars. Adapter referencia, não armazena
✗ EXECUTAR EM PARALELO SEM LIMITE — max 3 ações simultâneas
✗ IGNORAR RATE LIMIT — RateLimiter é obrigatório antes de toda execução real
✗ AÇÃO SEM AUDIT EVENT — toda ação real gera AuditEvent (P18)
✗ DRY-RUN QUE EXECUTA — dry_run=True NUNCA chama API externa
```

---

## 21. CRITÉRIOS DE ACEITE

- [ ] Namespace `src/real_world_actions/` com 13 arquivos
- [ ] Testes ≥ 100 (targeted), todos passando
- [ ] ActionRegistry funcional com register/find/enable/disable
- [ ] ActionSandbox bloqueia ações não-registradas e valida params
- [ ] ApprovalChain integrada com P18 — ação high+ para em checkpoint
- [ ] Pelo menos 3 adapters reais + MockAdapter
- [ ] RateLimiter funcional por provider
- [ ] Audit trail: toda ação real gera AuditEvent
- [ ] dry_run=True default — nunca executa ação real sem approval
- [ ] Zero regressões na full suite

---

## 22. ORDEM INCREMENTAL DE IMPLEMENTAÇÃO

### M1: Models + Errors + Registry
- `models.py`, `errors.py`, `registry.py`
- `test_models.py`, `test_registry.py`

### M2: Sandbox + Rate Limiter
- `sandbox.py`, `rate_limiter.py`
- `test_sandbox.py`, `test_rate_limiter.py`

### M3: Approval Chain (P18 Bridge)
- `approval_chain.py`
- `test_approval_chain.py`

### M4: Executor + Mock Adapter
- `executor.py`, `adapters/__init__.py`, `adapters/mock_adapter.py`
- `test_executor.py`

### M5: Adapters Reais + CLI
- `adapters/email_adapter.py`, `adapters/instagram_adapter.py`, `adapters/webhook_adapter.py`, `adapters/github_adapter.py`, `adapters/n8n_adapter.py`
- `cli.py`, `test_adapters.py`

### M6: E2E + Docs
- `test_e2e_actions.py`
- `__init__.py`, skeleton doc, full suite

---

## 23. RECOMENDAÇÃO DE PARALELIZAÇÃO

**1 frente principal + adapters em paralelo.** M1→M2→M3→M4 são sequenciais. M5 (5 adapters reais) pode ser parcialmente paralelizado se cada adapter for feito por um agente diferente, pois compartilham apenas o contrato (definido em M4). M6 é final.

---

*OMNIS Control Tower — P27 Real World Actions Architecture.*
