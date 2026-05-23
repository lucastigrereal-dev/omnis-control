# TOWER AUTHORITY MATRIX

**Date:** 2026-05-22
**Authority:** TORRE CENTRAL
**Purpose:** Define who owns what, who can modify what, and who resolves conflicts

---

## Authority by Domain

| Domain | Primary Owner | Source of Truth | Can Modify | Cannot Touch | Conflict Arbiter |
|--------|--------------|-----------------|------------|--------------|-----------------|
| **Runtime Core** | ABA 1 | `src/execution_graph/`, `src/missions/`, `src/omnis_bus/` | ABA 1 only | All other ABAs | TORRE |
| **Provider Fabric** | ABA 2 | `omnis-runtime/src/provider_interface.py` | ABA 2 only | All other ABAs | TORRE |
| **Observability** | ABA 3 | `src/observability/`, `data/metrics_spine/` | ABA 3 only | All other ABAs | TORRE |
| **Governance** | ABA 4 | `src/governance/`, `src/governance-core/` | ABA 4 only | All other ABAs | TORRE |
| **KRATOS Cockpit** | ABA 5 | `kratos-mission-control/` | ABA 5 (with human auth) | All other ABAs | HUMAN |
| **Memory/Akasha** | ABA 6 | Akasha DB, Obsidian vault | ABA 6 only | All other ABAs | TORRE |
| **Recovery** | ABA 7 | `src/missions/runtime.py`, replay modules | ABA 7 only | All other ABAs | TORRE |
| **Registry** | TORRE | `~/.claude/registry/` | TORRE only | All ABAs | TORRE |
| **Config** | TORRE | `config/paths.yaml` | TORRE only | All ABAs | TORRE |
| **Secrets** | HUMAN | `.env`, `credentials.json` | HUMAN only | ALL (including TORRE) | HUMAN |

---

## Decision Authority Levels

| Level | Who Decides | Examples |
|-------|-------------|----------|
| **L0 — READ** | Any ABA autonomously | Reading files, scanning code, running tests |
| **L1 — WRITE local** | ABA autonomously | Creating reports, writing health files, checkpoint data |
| **L2 — WRITE external** | ABA + TORRE approval | Modifying shared modules, updating registry |
| **L3 — MUTATE state** | TORRE + Human slot | Renaming directories, moving files, changing architecture |
| **L4 — DEPLOY** | HUMAN only | Push, deploy, merge to master |
| **L5 — DESTRUCTIVE** | HUMAN only | Delete worktrees, remove branches, rm -rf |

---

## File Ownership Map

### Owned by ABA 1 (Runtime Core)
```
src/execution_graph/**        → ABA 1
src/missions/**               → ABA 1
src/omnis_bus/**              → ABA 1
src/cli_commands/**           → ABA 1
tests/execution_graph/**      → ABA 1
tests/missions/**             → ABA 1
tests/omnis_bus/**            → ABA 1
```

### Owned by ABA 2 (Provider Fabric)
```
omnis-runtime/src/provider_interface.py  → ABA 2
```

### Owned by ABA 3 (Observability)
```
src/observability/**           → ABA 3
data/metrics_spine/**          → ABA 3
tests/observability/**         → ABA 3
```

### Owned by ABA 4 (Governance)
```
src/governance/**              → ABA 4
src/governance-core/**         → ABA 4
~/.claude/logs/**              → ABA 4 (shared with TORRE)
```

### Owned by ABA 5 (KRATOS)
```
kratos-mission-control/**      → ABA 5 (HUMAN AUTH REQUIRED)
~/.claude/state/kratos_health.json → ABA 3 writes, ABA 5 reads
```

### Owned by ABA 6 (Memory/Akasha)
```
Akasha DB (:5432)              → ABA 6
Obsidian vault                 → ABA 6 (read-only)
src/missions/memory_lookup.py  → ABA 1 owns code, ABA 6 owns integration
```

### Owned by ABA 7 (Recovery)
```
src/missions/runtime.py        → ABA 1 owns code, ABA 7 owns checkpoint logic
src/omnis_bus/replay.py        → ABA 1 owns code, ABA 7 owns replay logic
src/execution_graph/replay.py  → ABA 1 owns code, ABA 7 owns replay logic
```

### Owned by TORRE
```
reports/TOWER_*.md             → TORRE
config/paths.yaml              → TORRE
~/.claude/registry/**          → TORRE
docs/project-os/**             → TORRE
```

---

## Conflict Resolution Protocol

1. ABA detects conflict → reports to TORRE via `reports/ABA<N>_*_STATUS.md`
2. TORRE evaluates: is this a real conflict or perceived?
3. If real: TORRE decides which ABA owns the resolution
4. If cross-cutting: TORRE creates a joint task with clear ownership split
5. KRATOS conflicts: always escalate to HUMAN

---

## Current Authority Gaps

| Gap | Severity | Detail |
|-----|----------|--------|
| No ABA lead assigned | HIGH | ABAs are logical, not yet assigned to sessions/agents |
| Provider interface in separate repo | MEDIUM | `omnis-runtime/src/` outside omnis-control |
| governance vs governance-core split | HIGH | Two directories, one functional, one broken |
| KRATOS in separate repo | MEDIUM | Cross-repo coordination needed for ABA 5 |
