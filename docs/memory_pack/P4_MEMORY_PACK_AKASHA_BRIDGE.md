# P4 Memory Pack / Akasha Bridge Skeleton

**Wave:** P4 — Memory Pack  
**Status:** Skeleton created (dry-run/read-only)  
**Date:** 2026-05-12  
**Isolation:** `src/memory_pack/`, `tests/memory_pack/`, `docs/memory_pack/`

## Purpose

Memory Pack / Akasha Bridge provides a deterministic, read-only skeleton for:

1. **Modeling** memory sources (Akasha, Obsidian, Mem0, Gringotts, Biblioteca, Session, Static)
2. **Querying** memory conceptually (no real connection)
3. **Building** context packs from memory hits
4. **Planning** writeback (never executing)
5. **Simulating** queries for testing and validation

## Architecture

```
src/memory_pack/
├── __init__.py    # Public API re-exports
├── models.py      # 6 dataclasses + constants + enums
├── service.py     # MemoryPackPlanner + 5 convenience functions
└── errors.py      # 13 error classes
```

## Models

| Model | Purpose | Key Properties |
|---|---|---|
| `MemorySource` | Registered memory source metadata | source_type, priority, is_primary |
| `MemoryQuery` | Structured memory query | text, sources, sectors, filters |
| `MemoryHit` | Query result pointer | relevance, rank_score, snippet |
| `ContextPack` | Assembled context from hits | assembled_text, source_summary |
| `MissionMemoryRecord` | Persistent mission learning | sector, key_insights, decisions |
| `MemoryWritePlan` | Planned (never executed) writeback | action, records, target_chunks |

## Constants

- **7 Sources:** akasha, obsidian, mem0, gringotts, biblioteca, session, static
- **7 Sectors:** midia, comercial, vendas, conhecimento, produto, financeiro, operacoes
- **5 Relevances:** exact(100), high(75), medium(50), low(25), none(0)
- **3 Formats:** json, markdown, dict
- **4 Write Actions:** insert, update, upsert, delete (blocked)

## Service Functions

| Function | Description | Side Effects |
|---|---|---|
| `validate_memory_query(query)` | Validates query structure | None |
| `rank_memory_hits(hits, min_rel, max)` | Ranks by relevance + source priority | None |
| `build_context_pack(query, hits)` | Assembles context pack | None |
| `plan_memory_writeback(records, ...)` | Creates write plan | None (never executes) |
| `export_context_pack(pack, fmt)` | Exports to json/markdown/dict | None |

## Safety Rules (enforced)

1. **Dry-run by default** — all operations are planning/modeling only
2. **No real Akasha/Postgres connection** — no psycopg2, asyncpg, sqlalchemy
3. **No network** — no requests, httpx, urllib, socket
4. **No LLM** — no openai, anthropic, langchain
5. **No pandas** — stdlib only (dataclasses, json, uuid, datetime, enum)
6. **Writeback plan never executes** — `MemoryWritePlan.is_dry_run` always `True`
7. **Delete action blocked** — `MemoryWritePlan.new()` rejects ACTION_DELETE

## Dependencies

- Python stdlib only: `dataclasses`, `json`, `uuid`, `datetime`, `enum`, `typing`
- No external packages required

## Testing

```bash
python -m pytest tests/memory_pack/ -q
```

Tests cover:
- Model creation, validation, serialization roundtrips
- Service: query validation, hit ranking, context pack building
- Service: writeback planning, context pack export (all formats)
- Simulation: query simulation, writeback simulation
- Safety: no forbidden imports, no env reading, dry-run guarantees

## What Was NOT Done

- No real Akasha connection
- No database writes
- No network calls
- No CLI integration
- No modifications outside `src/memory_pack/`, `tests/memory_pack/`, `docs/memory_pack/`
