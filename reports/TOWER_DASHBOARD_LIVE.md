# TOWER DASHBOARD LIVE — KRATOS/Codex Painel Feed

**Date:** 2026-05-22
**Cycle:** REALTIME #1
**Target:** Dashboard visualization layer

---

## Live Payload (JSON)

```json
{
  "timestamp": "2026-05-22T00:00:00Z",
  "cycle": "REALTIME #1",
  "torre_status": "ACTIVE",
  "overall_health_score": 0.67,
  "overall_status": "DEGRADED",
  "runtime_truth_pct": 57,

  "summary": {
    "abas_total": 7,
    "abas_ready": 4,
    "abas_blocked": 2,
    "abas_warnings": 1,
    "abas_executing": 0,
    "abas_completed": 0,
    "waves_completed": 0,
    "waves_total": 30,
    "active_drifts": 18,
    "p0_drifts": 5,
    "active_blockers": 5,
    "human_decisions_pending": 4,
    "conflicts_detected": 4
  },

  "risk_feed": [
    {"level": "P0", "component": "KRATOS", "issue": "100% mock data", "action": "Human authorization"},
    {"level": "P0", "component": "Governance", "issue": "3/6 modules unreachable", "action": "Rename directory"},
    {"level": "P0", "component": "Runtime", "issue": "EventBus has no consumers", "action": "Deploy consumer"},
    {"level": "P0", "component": "Docs", "issue": "CURRENT_STATE.md 9 commits behind", "action": "Regenerate"},
    {"level": "P0", "component": "Tests", "issue": "4 test-to-source mismatches", "action": "Fix imports"}
  ],

  "drift_feed": [
    {"priority": "P0", "count": 5, "trend": "stable"},
    {"priority": "P1", "count": 5, "trend": "stable"},
    {"priority": "P2", "count": 8, "trend": "stable"}
  ],

  "blocker_feed": [
    {"status": "BLOCKED", "count": 5, "human_required": 4, "torre_resolvable": 1},
    {"status": "WARNINGS", "count": 5},
    {"status": "READY", "count": 7}
  ],

  "readiness_feed": {
    "aba1_runtime": "READY",
    "aba2_provider": "READY_WITH_WARNINGS",
    "aba3_observability": "READY",
    "aba4_governance": "BLOCKED",
    "aba5_kratos": "BLOCKED",
    "aba6_memory": "READY",
    "aba7_recovery": "READY"
  },

  "health_feed": {
    "runtime_core": 0.85,
    "provider_fabric": 0.60,
    "observability": 0.70,
    "governance": 0.50,
    "kratos_live": 0.25,
    "memory_akasha": 0.70,
    "recovery": 0.75,
    "infrastructure": 0.83
  },

  "next_actions": [
    {"aba": "ABA 4", "action": "Fix governance-core hyphen", "priority": "P0", "blocker": false},
    {"aba": "ABA 1", "action": "Deploy Redis consumer", "priority": "P0", "blocker": false},
    {"aba": "ABA 3", "action": "Activate EventBus consumers", "priority": "P1", "blocker": false},
    {"aba": "ABA 5", "action": "Await human: pode mexer no KRATOS?", "priority": "P0", "blocker": true}
  ],

  "conflict_feed": [
    {"id": "C1", "severity": "HIGH", "what": "Governance directory split"},
    {"id": "C2", "severity": "HIGH", "what": "Dual checkpoint systems"},
    {"id": "C3", "severity": "MEDIUM", "what": "Provider in separate repo"},
    {"id": "C4", "severity": "MEDIUM", "what": "JARVIS vs OMNIS naming"}
  ],

  "dead_systems_feed": [
    "kratos_bridge (11 files)",
    "akasha_event_sink (4 files)",
    "akasha_runtime (3 files)",
    "content_factory (11 files)",
    "+ 11 other DEAD packages"
  ],

  "mock_residual_feed": [
    {"component": "KRATOS dashboard", "pct_mock": 100},
    {"component": "Dashboard collectors", "pct_mock": 89},
    {"component": "Human slot notification", "pct_mock": 100},
    {"component": "Cost tracking", "pct_mock": 100}
  ]
}
```

---

## Dashboard Widget Layout (Recommended)

```
┌──────────────────────────────────────────────────────────────┐
│  OMNIS COMMAND CENTER — TORRE REALTIME                       │
├─────────────┬─────────────┬─────────────┬────────────────────┤
│ HEALTH: 0.67│ TRUTH: 57%  │ DRIFTS: 18  │ BLOCKERS: 5        │
│ DEGRADED    │ PARTIAL     │ P0: 5       │ HUMAN: 4           │
├─────────────┴─────────────┴─────────────┴────────────────────┤
│ ABA STATUS BAR                                               │
│ ABA1 🟢  ABA2 🟡  ABA3 🟢  ABA4 🔴  ABA5 🔴  ABA6 🟢  ABA7 🟢│
├──────────────────────────────────────────────────────────────┤
│ P0 RISK FEED                    │ BLOCKER FEED               │
│ • KRATOS 100% mock              │ 🔴 B1: KRATOS guardrail    │
│ • governance-core broken        │ 🔴 B5: hyphen rename       │
│ • EventBus no consumers         │ 🟡 B2: ANTHROPIC_KEY       │
│ • CURRENT_STATE.md stale        │ 🟡 B3: Worktree auth       │
│ • 4 test mismatches             │ 🟡 B4: Branch auth         │
├──────────────────────────────────────────────────────────────┤
│ CONFLICTS (4)                   │ NEXT ACTIONS               │
│ ⚠️ C1: Gov dir split (HIGH)     │ 1. ABA 4: Fix hyphen       │
│ ⚠️ C2: Dual checkpoints (HIGH)  │ 2. ABA 1: Deploy consumer  │
│ ⚠️ C3: Provider repo (MED)      │ 3. ABA 3: Activate bus     │
│ ⚠️ C4: Naming conflict (MED)    │ 4. ABA 5: Await human      │
├──────────────────────────────────────────────────────────────┤
│ DEAD SYSTEMS: 15 packages (12.8%) | MOCK: 4 components       │
│ RUNTIME HEALTH: 🟢 Redis 🟢 Ollama 🟢 Disk 🔴 1 Docker      │
└──────────────────────────────────────────────────────────────┘
```

---

## Update Triggers

| Trigger | What Updates |
|---------|-------------|
| ABA completes a wave | ABA status bar, health score, next actions |
| Drift detected/fixed | Drift feed, P0 risk feed |
| Blocker resolved/added | Blocker feed |
| Human decision received | Blocker feed, ABA status |
| Health probe runs | Health score, runtime health |
| Conflict resolved | Conflict feed |

---

## Refresh Cadence

| Feed | Refresh Rate |
|------|-------------|
| ABA status | On ABA report drop |
| Health score | Every health probe (on-demand) |
| Drift feed | Every reconciliation cycle |
| Blocker feed | Real-time (on change) |
| Risk feed | Every TORRE cycle |
| Next actions | Every TORRE cycle |
