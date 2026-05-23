# TOWER REALTIME AUTHORITY — Live Authority Matrix

**Date:** 2026-05-22
**Cycle:** REALTIME #1
**Authority Status:** STABLE — No conflicts, 4 shared domains documented

---

## Authority Verification Engine

| Component | Status |
|-----------|--------|
| Domain ownership verification | COMPLETE |
| Authority conflict detection | CLEAR |
| Cross-ABA boundary check | CLEAR |
| Source of truth validation | COMPLETE |
| Authority gap detection | 3 gaps found |

---

## Domain Authority Map (LIVE)

### Runtime Core → ABA 1
```
CANONICAL: src/execution_graph/, src/missions/, src/omnis_bus/, src/cli_commands/
AUTHORITY: ABA 1 (sole owner)
DELEGATES: Checkpoint logic to ABA 7 (documented shared ownership)
VALIDATION: 357/358 tests pass
STATUS: ACTIVE
```

### Provider Fabric → ABA 2
```
CANONICAL: omnis-runtime/src/provider_interface.py
AUTHORITY: ABA 2 (sole owner)
DEPENDENCY: External repo (omnis-runtime) — version not pinned
VALIDATION: Import + routing verified
STATUS: ACTIVE
```

### Observability → ABA 3
```
CANONICAL: src/observability/, data/metrics_spine/
AUTHORITY: ABA 3 (sole owner)
SHARES: ~/.claude/state/omnis_health.json (writes, ABA 5 reads)
VALIDATION: 127/127 tests pass
STATUS: ACTIVE
```

### Governance → ABA 4
```
CANONICAL: src/governance/ (functional), src/governance-core/ → src/governance_core/ (pending rename)
AUTHORITY: ABA 4 (sole owner)
BLOCKER: governance-core hyphen — 3 modules unreachable
VALIDATION: 3/6 modules importable
STATUS: DEGRADED
```

### KRATOS Cockpit → ABA 5
```
CANONICAL: kratos-mission-control/
AUTHORITY: ABA 5 (with HUMAN authorization required)
GUARDRAIL: "NUNCA tocar KRATOS" — override requires explicit human command
VALIDATION: Dashboard shows 100% mock
STATUS: BLOCKED
```

### Memory/Akasha → ABA 6
```
CANONICAL: Akasha DB (:5432), Obsidian vault
AUTHORITY: ABA 6 (sole owner)
SHARES: src/missions/memory_lookup.py (ABA 1 owns code, ABA 6 owns integration)
VALIDATION: DB connection not recently verified
STATUS: ACTIVE
```

### Recovery/Self-Healing → ABA 7
```
CANONICAL: src/missions/runtime.py (shared), src/omnis_bus/replay.py (shared)
AUTHORITY: ABA 7 (checkpoint/replay/watchdog logic)
SHARES: Runtime code owned by ABA 1, recovery logic owned by ABA 7
VALIDATION: 271/271 tests pass
STATUS: ACTIVE
```

### Registry & Config → TORRE
```
CANONICAL: ~/.claude/registry/, config/paths.yaml, reports/TOWER_*.md
AUTHORITY: TORRE (sole owner)
VALIDATION: TOWER files consistent
STATUS: ACTIVE
```

### Secrets → HUMAN
```
CANONICAL: .env, credentials.json, API keys
AUTHORITY: HUMAN (Lucas) — NO system component can read
VALIDATION: Enforced by no-touch rules
STATUS: PROTECTED
```

---

## Authority Gaps

| Gap | Severity | Detail |
|-----|----------|--------|
| No ABA lead assigned per session | MEDIUM | ABAs are logical constructs; no agent/session owns each |
| Provider interface in external repo | MEDIUM | Version not pinned; ABA 2 has no control over upstream |
| Shared ownership not formalized | LOW | ABA 1/7 share 3 files — documented but no contract |

---

## Authority Violation Watch

| Check | Status |
|-------|--------|
| Has any ABA touched KRATOS? | NO — guardrail intact |
| Has any ABA read .env? | NO — no-touch enforced |
| Has any ABA modified another ABA's canonical files? | NO — no ABA execution yet |
| Has any ABA performed destructive action? | NO |
| Has TORRE exceeded coordination scope? | NO — reports only |

---

## Who Controls What (Quick Reference)

```
"Who controls the execution graph?"       → ABA 1
"Who controls which LLM is called?"       → ABA 2
"Who controls health monitoring?"         → ABA 3
"Who controls approval gates?"            → ABA 4
"Who controls the dashboard?"             → ABA 5 (blocked)
"Who controls knowledge retrieval?"       → ABA 6
"Who controls checkpoint/recovery?"       → ABA 7
"Who controls the registry?"              → TORRE
"Who controls secrets?"                   → HUMAN (Lucas)
"Who resolves conflicts between ABAs?"    → TORRE
"Who authorizes KRATOS changes?"          → HUMAN (Lucas)
```
