# TOWER DASHBOARD HANDOFF

**Date:** 2026-05-22
**Authority:** TORRE CENTRAL
**Target:** Codex Painel / KRATOS Dashboard
**Purpose:** Structured payload for dashboard visualization of OMNIS operational state

---

## Dashboard Payload

```json
{
  "timestamp": "2026-05-22T00:00:00Z",
  "overall_status": "OPERATIONAL",
  "overall_score": 0.78,
  "last_phase": "Phase 4 — ULTRA AUTORUN",
  "last_phase_status": "COMPLETE",
  "branch": "feature/omnis-5waves-runtime-supreme",
  "recent_commits": 3,
  "human_decisions_pending": 5,
  "active_drifts": 18,
  "active_blockers": 5,

  "abas": {
    "aba1_runtime_core": {
      "status": "READY",
      "priority": "P0",
      "score": 0.85,
      "blockers": [],
      "warnings": ["No Redis consumers", "Test-to-source mismatches"],
      "next_action": "Deploy Redis consumer, complete mission lifecycle"
    },
    "aba2_provider_fabric": {
      "status": "READY_WITH_WARNINGS",
      "priority": "P1",
      "score": 0.80,
      "blockers": ["ANTHROPIC_API_KEY not set"],
      "warnings": ["Dead litellm imports", "Model name hardcoded"],
      "next_action": "Wire provider to missions (fallback blocked)"
    },
    "aba3_observability": {
      "status": "READY",
      "priority": "P1",
      "score": 0.65,
      "blockers": [],
      "warnings": ["EventBus layer dormant", "configure_logging None bug"],
      "next_action": "Activate EventBus consumers, wire dashboard collectors"
    },
    "aba4_governance": {
      "status": "BLOCKED",
      "priority": "P0",
      "score": 0.70,
      "blockers": ["governance-core hyphen import"],
      "warnings": ["3/6 modules unreachable"],
      "next_action": "Fix hyphen import, activate human_slot/decision_log/action_classifier"
    },
    "aba5_kratos_live": {
      "status": "BLOCKED",
      "priority": "P0",
      "score": 0.50,
      "blockers": ["KRATOS guardrail — human authorization required"],
      "warnings": ["Dashboard shows 100% mock data"],
      "next_action": "Await human: 'pode mexer no KRATOS'"
    },
    "aba6_memory_akasha": {
      "status": "READY",
      "priority": "P2",
      "score": 0.75,
      "blockers": [],
      "warnings": ["40-50% Obsidian duplication"],
      "next_action": "Document dedup strategy, verify Akasha connectivity"
    },
    "aba7_recovery": {
      "status": "READY",
      "priority": "P1",
      "score": 0.90,
      "blockers": ["Worktree deletion auth", "Branch deletion auth"],
      "warnings": ["No automated watchdog"],
      "next_action": "Implement watchdog daemon (cleanup blocked)"
    }
  },

  "drifts": {
    "p0": [
      "KRATOS 100% mock data",
      "governance-core hyphen breaks imports",
      "4 test-to-source mismatches",
      "CURRENT_STATE.md 9 commits behind",
      "Redis EventBus has no consumers"
    ],
    "p1": [
      "ACTIVE_WORKTREES.md missing 3 worktrees",
      "Dual registry naming (JARVIS vs OMNIS)",
      "15 DEAD packages",
      "No automated watchdog",
      "Provider not wired to missions"
    ],
    "p2": [
      "40-50% Obsidian duplication",
      "18 skills declared but unscaffolded",
      "7 stale worktrees",
      "4 dead branches",
      "configure_logging returns None",
      "5 dead litellm imports",
      "ollama model hardcoded in 7 places",
      "Two separate checkpoint systems"
    ]
  },

  "blockers": [
    {"id": "B1", "what": "KRATOS guardrail", "who": "Lucas", "action": "Say 'pode mexer no KRATOS'"},
    {"id": "B2", "what": "ANTHROPIC_API_KEY", "who": "Lucas", "action": "Set env var"},
    {"id": "B3", "what": "Worktree deletion", "who": "Lucas", "action": "Authorize cleanup"},
    {"id": "B4", "what": "Dead branch deletion", "who": "Lucas", "action": "Authorize deletion"},
    {"id": "B5", "what": "governance-core rename", "who": "TORRE", "action": "Rename directory (needs L3 confirm)"}
  ],

  "runtime_health": {
    "docker_aurora_redis": "healthy",
    "docker_others": "degraded",
    "ollama": "healthy (8 models)",
    "disk": "healthy (27.2% free)",
    "redis_eventbus": "validated (10 channels, 0 consumers)",
    "health_bridge": "active (7 components, 0.95)",
    "missions": "partial (1 checkpoint, resumable=True)",
    "governance": "partial (3/6 active)",
    "kratos": "mock"
  },

  "next_recommended_aba": "ABA 4 — Governance (fix hyphen, unblocks immediately)",
  "next_recommended_command": "/TORRE:ABA4 — Fix governance-core hyphen + activate 3 modules"
}
```

---

## Visual Dashboard Structure

### Row 1 — Overall Status Cards
```
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ SCORE: 0.78 │ │ PHASE: 4    │ │ DRIFTS: 18  │ │ BLOCKERS: 5 │
│ OPERATIONAL  │ │ COMPLETE    │ │ P0: 5       │ │ HUMAN: 4    │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
```

### Row 2 — ABA Status Bar
```
ABA1: 🟢 READY    ABA2: 🟡 WARNINGS    ABA3: 🟢 READY    ABA4: 🔴 BLOCKED
ABA5: 🔴 BLOCKED  ABA6: 🟢 READY        ABA7: 🟢 READY
```

### Row 3 — P0 Drifts (Red)
### Row 4 — Runtime Health (Green/Yellow/Red)
### Row 5 — Human Decisions Pending
### Row 6 — Next Recommended Action

---

## Update Frequency

| Data | Refresh |
|------|---------|
| ABA status | On ABA report drop |
| Drift matrix | On reconciliation cycle |
| Runtime health | On health bridge write (every mission probe) |
| Blockers | On human decision or ABA completion |
| Dashboard payload | Every TORRE session |
