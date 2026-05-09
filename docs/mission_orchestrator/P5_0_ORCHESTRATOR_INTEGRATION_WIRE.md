# P5.0 — Orchestrator Integration Wire

**Tests:** 10 new (45 total in module)  
**Status:** COMPLETE  

## What changed

`OrchestratorRun` now carries P4 intelligence fields:

| Field | Type | Description |
|---|---|---|
| `sector_id` | `Optional[str]` | Best-matching sector from sector_registry |
| `matched_capabilities` | `list[str]` | Capability IDs from skill_matcher |
| `suggested_gap_ids` | `list[str]` | Gap IDs from capability_gap.detect() (when no caps) |
| `approval_required` | `bool` | True if any matched cap or gap has risk medium/high |
| `approval_id` | `Optional[str]` | Populated later by P5.1 enforcement hook |

## Planning flow

```
build_plan(request_text)
  → detect_intent()           # mission_builder content intent
  → match_capabilities()      # skill_matcher P4.2
  → match_sector()            # sector_registry P4.1
  → if no caps: detect_gap()  # capability_gap P4.3
  → set approval_required     # risk: medium or high
```

## Raise behavior change

Previously: `UnknownIntentError` if intent == "unknown" and `allow_unknown=False`.  
Now: only raises if intent == "unknown" **AND** no capability matches the request.

This means: `importar arquivo imagem` → `asset_inbox_import` matches (medium risk) →  
no raise even though mission_builder returns intent="unknown".
