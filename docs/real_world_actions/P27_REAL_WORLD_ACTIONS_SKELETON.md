# P27 — REAL WORLD ACTIONS SKELETON

> **Data:** 2026-05-14
> **Status:** SKELETON COMPLETE

---

## FILES

```
src/real_world_actions/
├── __init__.py              # Public exports (29 symbols)
├── models.py                # ActionDefinition, ActionRequest, ActionResult, RateLimit, RetryPolicy
├── errors.py                # RealWorldActionError + 7 subclasses
├── registry.py              # ActionRegistry — catalogue of actions
├── sandbox.py               # ActionSandbox — validation, blocking, preview
├── rate_limiter.py          # RateLimiter — per-provider/action enforcement
├── approval_chain.py        # ApprovalChain — P18 governance bridge
├── executor.py              # ActionExecutor — full pipeline orchestrator
├── cli.py                   # CLI: list, preview, execute, approve, deny, history, providers
└── adapters/
    ├── __init__.py          # ADAPTER_REGISTRY + ActionAdapter protocol
    ├── mock_adapter.py      # MockAdapter for testing
    ├── email_adapter.py     # EmailAdapter (Gmail SMTP)
    ├── instagram_adapter.py # InstagramAdapter (Graph API)
    ├── webhook_adapter.py   # WebhookAdapter (HTTP POST)
    ├── github_adapter.py    # GitHubAdapter (gh CLI)
    ├── n8n_adapter.py       # N8nAdapter (webhook trigger)
    └── slack_adapter.py     # SlackAdapter

tests/real_world_actions/
├── test_models.py           # 36 testes
├── test_registry.py         # 18 testes
├── test_sandbox.py          # 14 testes
├── test_rate_limiter.py     # 13 testes
├── test_approval_chain.py   # 14 testes
├── test_executor.py         # 15 testes
├── test_adapters.py         # 36 testes
└── test_e2e_actions.py      # 18 testes

docs/real_world_actions/
└── P27_REAL_WORLD_ACTIONS_SKELETON.md
```

---

## CONTRACTS

### ActionDefinition
- `action_id` prefix: `rwa_`
- Risk derived from action_type via `ACTION_TYPE_RISK_MAP`
- `requires_approval` — True for high/critical
- Factory: `ActionDefinition.new(name, provider, action_type)`

### ActionRequest / ActionResult
- `request_id` prefix: `rwq_`, `result_id` prefix: `rwr_`
- Status flow: dry_run → pending_approval → success | failed | denied | timeout
- Factory: `ActionRequest.new(action_id)`, `ActionResult.new(request_id)`

### ActionExecutor
- `dry_run=True` default
- Pipeline: resolve → validate → sandbox → approval → execute → audit
- `execute(request)` — single action
- `execute_batch(requests)` — multiple actions

### CLI
- `omnis-action list [--provider] [--risk] [--type]`
- `omnis-action preview <action> [--params]`
- `omnis-action execute <action> [--params] [--no-dry-run]`
- `omnis-action approve <request_id>`
- `omnis-action deny <request_id> [--reason]`
- `omnis-action history [--limit]`
- `omnis-action providers`

---

## DEPENDENCIES
- Bridge to P18 Governance (approval_chain.py)
- Zero toques em módulos existentes
- All adapters are dry-run safe by default
