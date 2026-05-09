# P4.3 — Capability Gap Detector

**Status:** COMPLETE  
**Tests:** 21/21 PASS  
**Commit:** pending  

## What was built

Local detector that identifies when an incoming request is not covered by any existing OMNIS capability. No network, no LLM, no external calls — pure keyword matching over `config/capabilities.yaml` and `config/sectors_registry.yaml`.

## Files

| File | Role |
|---|---|
| `src/capability_gap/__init__.py` | package |
| `src/capability_gap/errors.py` | `CapabilityGapError` |
| `src/capability_gap/models.py` | `CapabilityGap`, `GapDetectionResult`, status constants |
| `src/capability_gap/detector.py` | `detect()` — main entry point |
| `src/capability_gap/store.py` | `GapStore` — JSONL append-only persistence |
| `src/cli_commands/capability_gap_cmd.py` | CLI: detect / list / show |
| `config/capabilities.yaml` | 12 capabilities with keywords |
| `config/sectors_registry.yaml` | 7 sectors with keywords |

## Detection logic

```
detect(request)
  → match_capabilities()    → "covered" (matched_capabilities=[...])
  → match_sector()          → "unknown_sector" if no sector
  → sector found, no cap    → "gap_detected" (gaps=[CapabilityGap])
```

## CLI

```bash
omnis capability-gap detect "cria carrossel instagram"   # covered
omnis capability-gap detect "análise blockchain"          # unknown_sector
omnis capability-gap list
omnis capability-gap show gap_abc123
```

## Test coverage

| Module | Tests | Notes |
|---|---|---|
| models | 3 | new(), to_dict/from_dict round-trip, GapDetectionResult.to_dict |
| detector | 7 | covered, gap_detected, unknown_sector, no network, no env reads |
| store | 5 | save+list, empty, get found/not-found, newest-first ordering |
| cli | 6 | help, detect covered/unknown JSON, saves gap, list empty, show not-found |

## Fixes applied

- `store.get()` called `list_all(limit=0)` → `[:0]` empty slice. Fixed to `limit=10000`.
- CLI `cmd_detect/list/show` used `GapStore()` with default arg bound at import time — monkeypatch couldn't reach it. Fixed: all three commands now pass `store_mod.DEFAULT_GAPS_LOG` explicitly.
