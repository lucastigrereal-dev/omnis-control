# OMNIS Memory Embedding Strategy

**Date:** 2026-05-15
**Status:** DEFINED — Mock-first, real provider behind feature flag

## Principles

1. **Mock-first**: All tests use MockHashEmbeddingProvider — deterministic, zero external calls
2. **No API without authorization**: Real embedding providers require explicit config + enabled flag
3. **Deterministic for dedup**: Same content → same embedding → dedup works reliably
4. **Dimension configurable**: 384 default, configurable per strategy

## Available providers

| Provider | Class | Deterministic | External Call | Use Case |
|---|---|---|---|---|
| mock_hash | MockHashEmbeddingProvider | Yes | No | Default for tests + dry-run |
| mock_constant | MockConstantEmbeddingProvider | Yes | No | Unit tests (don't care about values) |
| mock_keyword | MockKeywordEmbeddingProvider | Yes | No | Keyword-aware tests |
| nomic_local | (future) | Yes | No (local) | Local embedding via Ollama |
| openai_real | (future) | No | Yes | Production — feature flag gated |

## Integration points

1. **AkashaMemoryDocument.embedding** — populated by provider before write
2. **WritePolicyEnforcer** — checks `require_embedding` flag
3. **DedupRegistry** — uses embedding hash as one dedup key option

## Security

- Mock providers never call external APIs
- Real providers require `requires_explicit_authorization=True`
- Never read .env for API keys — inject via config parameter only
- Embedding dimensions logged (not the vectors themselves)
