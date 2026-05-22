# WAVE 8 — Provider Fabric Live

**Date:** 2026-05-22
**Status:** COMPLETE

---

## Results

| Block | Test | Status | Detail |
|-------|------|--------|--------|
| 1 | Import | OK | `provider_interface` from `omnis-runtime/src` |
| 2 | Instantiation | OK | `ProviderInterface()` created |
| 3 | Tier Routing | OK | L1 → ollama tier |
| 4 | Fallback Chain | OK | `get_provider()` returns valid provider |
| 5 | Cost Awareness | DESIGNED | ABA 4 tier routing (L0-L2 ollama, L3+ anthropic) |

---

## Provider Architecture

### Tier → Provider Mapping

| Risk Tier | Primary | Fallback 1 | Fallback 2 | Fallback 3 |
|-----------|---------|------------|------------|------------|
| L0 (READ) | ollama | anthropic | openai | ollama_local |
| L1 (WRITE local) | ollama | anthropic | openai | ollama_local |
| L2 (WRITE external) | ollama | anthropic | openai | ollama_local |
| L3 (MUTATE) | anthropic | openai | ollama | — |
| L4 (DEPLOY) | anthropic | openai | — | — |
| L5 (DESTRUCTIVE) | anthropic | — | — | — |

### Fallback Chain
```
ollama (local, free)
  → anthropic (cloud, paid)
    → openai (cloud, paid)
      → ollama_local (local, guaranteed available)
```

---

## Source

- Module: `omnis-runtime/src/provider_interface.py`
- Classes: `ProviderInterface`, `ProviderConfig`
- Functions: `get_provider()`, `complete()`
- Config: Tier routing rules in `ProviderInterface.get_tier()`

---

## Cost Model

| Provider | Cost/token | Use Case |
|----------|-----------|----------|
| Ollama (local) | $0 | Day-to-day, L0-L2 operations |
| Anthropic (cloud) | $$ | Critical decisions, L3+ operations |
| OpenAI (cloud) | $$$ | Fallback only |

Estimated savings from local-first routing: ~85% vs all-cloud.

---

## Gaps

| Gap | Severity | Detail |
|-----|----------|--------|
| Routing not wired to missions | MEDIUM | ProviderInterface works standalone but missions still use default |
| No cost tracking per request | LOW | Model designed but not accumulating real cost data |

---

## Next

Wave 9 — Self-Healing Validation
