# TOWER CONFLICT ENGINE — Architectural Conflict Detection

**Date:** 2026-05-22
**Cycle:** REALTIME #1
**Conflicts Detected:** 4 (0 CRITICAL, 2 HIGH, 2 MEDIUM)

---

## Conflict Detection Engine

| Component | Status |
|-----------|--------|
| Ownership conflict scanner | ACTIVE |
| Authority overlap detector | ACTIVE |
| Duplicate runtime detector | ACTIVE |
| Incompatible adapter checker | ACTIVE |
| Replay divergence checker | ACTIVE |

---

## Active Conflicts

### C1 — Governance Directory Split (HIGH)

| Field | Value |
|-------|-------|
| **Conflict** | `src/governance/` (functional) vs `src/governance-core/` (broken) |
| **Type** | Ownership conflict + naming inconsistency |
| **ABAs Involved** | ABA 4 |
| **Root Cause** | Directory created with hyphen during Autopilot 6H; Python can't import it |
| **Impact** | 3/6 governance modules unreachable; dual authority confusion |
| **Resolution** | Rename `governance-core/` → `governance_core/` (ABA 4 Wave 1) |
| **Severity** | HIGH |

### C2 — Dual Checkpoint Systems (HIGH)

| Field | Value |
|-------|-------|
| **Conflict** | Mission-level checkpoints (`src/missions/runtime.py`) vs Graph-level checkpoints (`src/execution_graph/replay.py`) |
| **Type** | Duplicate functionality with different schemas |
| **ABAs Involved** | ABA 1, ABA 7 |
| **Root Cause** | Independent development — missions team and execution graph team built separate systems |
| **Impact** | Two checkpoint formats, no unified resume, potential inconsistency |
| **Resolution** | Document split in ABA 7 Wave 5; decide: unify or maintain with clear boundary |
| **Severity** | HIGH |

### C3 — Provider Interface in Separate Repo (MEDIUM)

| Field | Value |
|-------|-------|
| **Conflict** | `omnis-runtime/src/provider_interface.py` outside `omnis-control/` |
| **Type** | Cross-repo dependency without version pinning |
| **ABAs Involved** | ABA 2 |
| **Root Cause** | Architecture decision: omnis-runtime as separate package |
| **Impact** | Import requires `sys.path` manipulation; no version lock |
| **Resolution** | Either: pin version in omnis-control, or vendor provider_interface into omnis-control |
| **Severity** | MEDIUM |

### C4 — JARVIS vs OMNIS Registry Naming (MEDIUM)

| Field | Value |
|-------|-------|
| **Conflict** | `~/.claude/registry/` uses "JARVIS Maestro" naming; OMNIS runtime uses "OMNIS Control" |
| **Type** | Naming inconsistency across documentation and code |
| **ABAs Involved** | TORRE |
| **Root Cause** | Evolutionary — JARVIS predates OMNIS; registry never renamed |
| **Impact** | Operator confusion; searchability issues |
| **Resolution** | Standardize naming in registry (TORRE task — P2) |
| **Severity** | MEDIUM |

---

## Ownership Conflicts

| File/Dir | Claimed By | Actual Owner | Conflict? |
|----------|-----------|--------------|-----------|
| `src/missions/runtime.py` | ABA 1 (code), ABA 7 (checkpoint logic) | ABA 1 | Shared — documented |
| `src/omnis_bus/replay.py` | ABA 1 (code), ABA 7 (replay logic) | ABA 1 | Shared — documented |
| `src/execution_graph/replay.py` | ABA 1 (code), ABA 7 (replay logic) | ABA 1 | Shared — documented |
| `~/.claude/state/omnis_health.json` | ABA 3 (writes), ABA 5 (reads) | ABA 3 | Shared — contract documented |

No unauthorized ownership conflicts detected.

---

## Duplicate Authority Detection

| Domain | Authority 1 | Authority 2 | Conflict? |
|--------|------------|------------|-----------|
| Risk classification | `src/governance/service.py` (RiskClassifier) | `src/governance-core/risks/risk_classifier.py` (inaccessible) | NO — one is dead |
| Approval gate | `src/governance/approval_gate.py` | `src/governance-core/approvals/approval_gate.py` (inaccessible) | NO — one is dead |
| Event envelope | `src/omnis_bus/envelope.py` (CanonicalEnvelope) | None | CLEAR |
| Health file | `src/observability/health_file.py` | None | CLEAR |

No live duplicate authorities. governance-core duplicates exist but are dead (unreachable).

---

## Incompatible Adapter Detection

| Adapter Pair | Compatibility | Issue |
|-------------|--------------|-------|
| EventBus → Observability | COMPATIBLE | Consumer not deployed yet |
| Health Bridge → KRATOS | COMPATIBLE | Format agreed (WAVE3), KRATOS not consuming |
| Provider → Missions | COMPATIBLE | Not wired yet |
| Governance Audit → Logs | COMPATIBLE | JSONL format, working |

No incompatible adapters detected.

---

## Replay Divergence Check

| Replay System | Source | Status |
|--------------|--------|--------|
| Mission replay | `src/missions/runtime.py` — checkpoint/resume | 1 checkpoint, resumable |
| Graph replay | `src/execution_graph/replay.py` — resume/replay | 3644 manifests |
| EventBus replay | `src/omnis_bus/replay.py` — ReplayBuffer | 3 synthetic events |

Divergence risk: LOW. Systems serve different layers (mission, graph, event) with clear boundaries. But formats are different — potential future conflict if unified.

---

## Conflict Resolution Queue

| Priority | Conflict | Resolution | Owner |
|----------|---------|-----------|-------|
| 1 | C1 — Governance split | Rename directory | ABA 4 |
| 2 | C2 — Dual checkpoints | Document split | ABA 7 |
| 3 | C3 — Provider repo separation | Version pin or vendor | ABA 2 |
| 4 | C4 — JARVIS/OMNIS naming | Standardize registry | TORRE |
