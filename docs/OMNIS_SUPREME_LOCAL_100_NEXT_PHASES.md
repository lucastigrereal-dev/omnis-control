# OMNIS Supreme Local 100% — Next Phases

**Date:** 2026-05-18
**From:** v1.0.0-omnis-supreme-local (FROZEN)

---

## Strategic Context

Supreme Local 100% is frozen. OMNIS now operates fully offline with self-search, self-replay, self-versioning, self-review, self-queue, and self-parallelization.

The next frontier: **connective intelligence** — bridging the local Supreme with the external Publisher OS (JARVIS, ARGOS, Instagram pipeline).

---

## Phase A: Bridge Activation (estimated 2-3 sessions)

Connect Local Supreme to Publisher OS without compromising offline integrity.

### A1 — ARGOS Bridge Hardening
- `src/argos_bridge/` already exists — validate read path
- Add write path with operator approval gate
- Test round-trip: local backlog → ARGOS enqueue → status check

### A2 — Akasha Read Bridge
- `src/akasha_runtime/` exists — activate read-only queries
- 20K docs, 606K chunks available via pgvector
- Integrate with local_search for hybrid retrieval

### A3 — Memory Sync Protocol
- Bidirectional sync: local JSON ↔ Akasha pgvector
- Conflict resolution: local wins on content, remote wins on metrics
- Dry-run first, batch commit

### A4 — Skill Bridge Activation
- `src/skills_bridge/` — route local skill calls to Publisher OS agents
- Gate: only read-only skills auto-forward; write skills require approval

---

## Phase B: Production Pipeline (estimated 3-4 sessions)

Connect content production flow end-to-end.

### B1 — Content Factory → ARGOS Pipeline
- Quality Gate (S08) scores content → passes threshold → auto-enqueue
- Backlog (S09) manages production queue
- Parallel Runner (S10) fans out multi-profile publishing

### B2 — CRM Integration
- Lead qualifier from CLAUDE.md → CRM backend (container on :4000)
- Template Registry (S01) serves personalized outreach templates
- App Factory (S07) generates client-facing mini-apps

### B3 — Analytics Loop
- publisher-os analytics → local metrics store
- Quality Gate feedback loop: published performance → score weighting
- A/B comparison (S05) validated against real Instagram metrics

---

## Phase C: Multi-Agent Autonomy (estimated 4-5 sessions)

Deploy the 30-agent Supreme roadmap from memory.

### C1 — MissionEngine (W-A1)
- Autonomous mission decomposition from natural language
- Backlog auto-population from mission plans
- Skill matching from registry

### C2 — Squad Orchestration
- Parallel Runner dispatches to specialized squads
- File locks prevent collision on shared assets
- Consolidation reports after multi-squad operations

### C3 — Self-Improvement Loop
- Quality Gate scores own outputs
- Failed dimensions → auto-enqueue revision tasks in Backlog
- Versioning tracks improvement over time

---

## Phase D: KRATOS Cockpit Integration (estimated 2-3 sessions)

Surface Local Supreme state in the KRATOS frontend.

### D1 — Live Status Bridge
- `src/live_cockpit/` — real-time Supreme health metrics
- Backlog counts, recent batches, quality scores

### D2 — Operator Console
- Web UI to view/search/approve queue items
- Trigger replays, rollbacks, A/B comparisons
- Read-only by default; actions require confirmation

---

## Phase E: Hardening & Scale (ongoing)

### E1 — Disk Sanity
- Current: 15.2% free (140.9 GB of 924.3 GB)
- Target: 20%+ free before Phase B production load
- Cleanup targets: stale worktrees, old test caches, npm/pip caches

### E2 — Container Health
- `jarvis_frontend` — unhealthy, needs restart or rebuild
- `crm-tigre-backend` — intermittent health flips

### E3 — OAuth Meta
- Pending: META_APP_ID / META_APP_SECRET
- Required before real Instagram publishing
- Feature-flag gate until resolved

---

## Risk Register

| Risk | Severity | Mitigation |
|------|----------|------------|
| Disk < 15% during production | HIGH | Cleanup before Phase B |
| jarvis_frontend unhealthy | MEDIUM | Restart, no data loss risk |
| Meta OAuth blocked | HIGH | Manual publishing fallback |
| Bridge write-path bug | MEDIUM | dry_run gate on all writes |
| Memory drift (Akasha vs local) | LOW | Conflict resolution protocol |

---

## Decision Gates

Before starting Phase A:
1. [ ] Disk cleanup completed (target: 20%+ free)
2. [ ] jarvis_frontend container healthy
3. [ ] Decision: CCOS vs G14 App Factory priority resolution
4. [ ] Operator approval for bridge write-path activation

Before starting Phase B:
1. [ ] ARGOS read bridge validated with 10 real queries
2. [ ] Quality Gate calibration against 50 published posts
3. [ ] Operator approval for auto-enqueue

---

## Immediate Next 3 Steps

1. **Disk cleanup** — free 20GB+ from stale caches and worktrees
2. **Restart jarvis_frontend** — resolve unhealthy container state
3. **ARGOS read validation** — run 10 read-only queries through existing bridge
