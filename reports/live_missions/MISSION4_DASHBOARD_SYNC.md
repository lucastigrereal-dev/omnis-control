# MISSION 4 — Dashboard Sync

**Mission ID:** MIS-PHASE3-004
**Date:** 2026-05-22
**Status:** COMPLETE
**Risk Level:** L1 (LOCAL — read-only scan, auto-approved)

---

## Executive Summary

Mapped 5 dashboard surfaces, 6 audit surfaces, 5 metrics layers. Found: KRATOS is 100% mock data, health bridge file doesn't exist on disk, observability layer fully designed but dormant (no Redis), 10 data inconsistencies between authoritative documents (3 CRITICAL). Only live metrics: P0.9 spine (12,368 JSONL entries).

---

## 1. Dashboard Surface Map

### Surface Inventory

| # | Dashboard | Type | Data Source | Live Data? | Coverage |
|---|-----------|------|-------------|------------|----------|
| 1 | KRATOS `/sistema` | Web (React) | Hardcoded mock stores | **NO** | 8 KRATOS + 8 OMNIS services |
| 2 | KRATOS `/` | Web (React) | Mixed (context real, services mock) | Partial | Summary cards |
| 3 | Publisher OS `/system` | Web (Next.js) | Backend API, 5s polling | **YES** | Publisher OS Docker only |
| 4 | Live Cockpit CLI | Terminal (Rich) | Module imports + shutil | Mixed (disk real, rest zero) | 13 modules |
| 5 | Health HTTP Server | REST API | 7 checkers (disk, docker, etc.) | Would be real if running | 7 components |

### Additional Surfaces

| # | Surface | Type | Status |
|---|---------|------|--------|
| 6 | `omnis_health.json` bridge | File | **FILE DOES NOT EXIST** — `~/.claude/state/` dir not found |
| 7 | `diagnose_omnis.json` | File snapshot | **20 days stale** (May 2) |
| 8 | Consolidation reports | Markdown | **1 day stale** (May 21) |

---

## 2. Critical Sync Gaps

### GAP 1 — KRATOS is 100% Mock Data (CRITICAL)

Both `backend/services/store.ts` and `backend/omnis/store.ts` seed hardcoded data. Services marked "degraded" (OMNIS, n8n) are hardcoded strings, not actual status. The `omnis_health.json` bridge file was designed specifically for KRATOS to consume — but KRATOS never reads it.

**Contract breach:** CLAUDE.md states "KRATOS reads OMNIS status via `omnis_health.json` bridge file." Reality: KRATOS reads from in-memory mock stores.

### GAP 2 — Health Bridge File Never Written (CRITICAL)

`health_file.py` targets `~/.claude/state/omnis_health.json`. The `~/.claude/state/` directory does not exist. The bridge exists in code but has never produced output. 6 unit tests pass but no runtime invocation.

### GAP 3 — Observability Layer Dormant (CRITICAL)

The entire `src/observability/` layer depends on Redis EventBus. Redis not running → no event bus → no health scorer, no audit log, no replay engine, no tracer, no telemetry collector. The layer is architecturally complete but operationally dead.

### GAP 4 — Live Cockpit Returns Zeros

8 of 9 collector methods return hardcoded zeros:
- `collect_missions()` → `{}`
- `collect_campaigns()` → `{"active_campaigns": 0}`
- `collect_observability()` → `{"tests_passing": 0, "tests_failing": 0}`

Only `collect_system_health()` (disk usage) and `collect_module_health()` (import checks) provide real data.

### GAP 5 — No Single Dashboard Covers Full Ecosystem

Publisher OS Cockpit → only Docker containers. KRATOS → only mock data. Live Cockpit → only module imports. Health bridge → doesn't exist. No surface shows the unified state of OMNIS + KRATOS + Publisher OS + Akasha.

---

## 3. Metrics & Audit Surface Map

### Metrics Layers

| # | Layer | Storage | Live? | Data Volume |
|---|-------|---------|-------|-------------|
| 1 | P0.9 Metrics Spine | `data/metrics_spine/metrics.jsonl` | **YES** | 12,368 entries (May 7-20) |
| 2 | EG Run Metrics | In-memory | No | Computed from EventLog |
| 3 | Prod Hardening Metrics | In-memory | No | Wave D/E/F testing only |
| 4 | Publisher Metrics | None (dataclass only) | No | Placeholder |
| 5 | Observability SLO Metrics | In-memory (async singleton) | No | 8 SLO targets defined, zero data |

**Finding:** Token/cost tracking non-functional — all 12,368 metrics entries show `tokens_in:0, tokens_out:0, cost_usd:0.0`.

### Audit Layers

| # | Layer | Target Storage | Status |
|---|-------|---------------|--------|
| 1 | Governance Decision Audit | `~/.claude/logs/governance_audit.jsonl` | **File doesn't exist** |
| 2 | Observability Audit Log | `data/audit/YYYYMMDD.jsonl` | **Directory doesn't exist** |
| 3 | Observability Audit Trail | In-memory only | No persistence |
| 4 | Command Audit Log | Optional JSONL | Not activated |
| 5 | MCP Permission Auditor | In-memory | Tests exist, not runtime |
| 6 | Architecture Auditor | Claude Code agent skill | Design only |

**Finding:** Zero audit surfaces are actively writing data. All 6 are designed, coded, and tested — but none are wired to runtime.

---

## 4. Data Source Consistency Audit

### 10 Inconsistencies Found

| # | Severity | Domain | Claim | Reality |
|---|----------|--------|-------|---------|
| 1 | **CRITICAL** | Git | CURRENT_STATE.md: HEAD = `a7c21bb` | Actual HEAD = `bd2de46` (9 commits ahead) |
| 2 | **CRITICAL** | Worktrees | ACTIVE_WORKTREES.md: 8 worktrees | `git worktree list`: 11 worktrees |
| 3 | **CRITICAL** | Guardrails | Autopilot report claims kratos commit | GUARDRAILS.md: "NUNCA tocar KRATOS" |
| 4 | MODERATE | Worktrees | Stale review: 10 worktrees | 11 actual (omnis-p20 missing) |
| 5 | MODERATE | Git | Stale review: omnis-control HEAD = `6cd48d2` | Actual = `bd2de46` |
| 6 | MODERATE | Git | Stale review: omnis-runtime = `233cdf4` | Actual = `e7ff37a` |
| 7 | MODERATE | Repos | Autopilot report: "3 repos" | omnis-runtime is worktree of omnis-control |
| 8 | LOW | Tests | CURRENT_STATE.md: 7838 tests | Actual: 8631 collected |
| 9 | LOW | Docker | CLAUDE.md: 2 unhealthy containers | ESTADO_ATUAL: 1 unhealthy |
| 10 | LOW | Disk | ESTADO_ATUAL: 15.1% free | sectors.yaml: 8.2% free |

### Confirmed Consistent
- Branch name matches across all sources
- All 4 omnis-control autopilot commits exist in git log
- GUARDRAILS.md internally consistent
- paths.yaml services match documented expectations
- config/sectors.yaml (OMNIS) vs registry/sectors.yaml (JARVIS) — intentionally different layers with explicit mapping table

---

## 5. Sync Status Matrix

| Data Point | KRATOS | Publisher OS | Live Cockpit | Health Bridge | Metrics Spine | Reality |
|------------|--------|-------------|--------------|---------------|---------------|---------|
| Docker containers | Mock (8) | Real (8) | 0 | Would be real | Not tracked | ~17 containers |
| Disk usage | Not shown | Real | Real | Not in bridge | Not tracked | ~15% free |
| Module health | Not shown | Not shown | Import check (13) | Not in bridge | Not tracked | 117 packages |
| Test results | Not shown | Not shown | 0 | Not tracked | Not tracked | 340/341 (targeted) |
| Missions active | Mock (3) | Not shown | 0 | Not tracked | 12,368 events | Unknown |
| Pipeline queue | Not shown | Real (Redis) | 0 | Not tracked | Not tracked | Unknown |
| LLM models | Not shown | Real (7) | Not shown | ollama only | Not tracked | ollama + 7 OpenRouter |
| Audit trail | Not shown | Not shown | Not shown | Not tracked | Not tracked | **Empty** |

---

## 6. Recommendations

| # | Action | Priority | Effort |
|---|--------|----------|--------|
| 1 | Wire KRATOS to read `omnis_health.json` bridge | P0 | Medium |
| 2 | Create `~/.claude/state/` and activate health_file bridge | P0 | Low |
| 3 | Start Redis and activate EventBus | P0 | Low |
| 4 | Update CURRENT_STATE.md to reflect actual HEAD | P1 | Low |
| 5 | Update ACTIVE_WORKTREES.md with missing 3 worktrees | P1 | Low |
| 6 | Wire Live Cockpit collectors to real data sources | P1 | Medium |
| 7 | Activate governance audit log (create dir, write first entry) | P1 | Low |
| 8 | Wire token/cost tracking into metrics spine | P2 | Medium |
| 9 | Resolve guardrail violation: document or revert kratos commit | P2 | Decision needed |
| 10 | Decommission duplicate metrics collectors (pick 1 canonical) | P2 | Low |

---

## Validation

### Provider Routing
- 3 agent dispatches, all L1, auto-approved

### Mission Persistence
- trace_id propagated through all dispatches

### Governance Hooks
- Zero Human Slot triggers (all read-only)
- Decision log entries: 3 (pending directory creation to persist)

---

## Next Action
Proceed to Mission 5 — Recovery Test
