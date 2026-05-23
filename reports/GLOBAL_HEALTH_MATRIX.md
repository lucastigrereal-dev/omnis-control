# GLOBAL HEALTH MATRIX — OMNIS Organism Health

**Date:** 2026-05-22
**Mission:** GLOBAL EVALUATION — Wave 2
**Overall Score:** 0.61 — DEGRADED

---

## Health Score Methodology

Each domain scored 0.0-1.0 weighted by: component count, test coverage, live data presence, and operational criticality. The TORRE model applies stricter weighting than Phase 4 — KRATOS (operator's window) and Governance (safety layer) carry heavier penalties when degraded.

---

## Domain Health Scores

| # | Domain | Score | Status | Weight | Trend |
|---|--------|-------|--------|--------|-------|
| 1 | Runtime Core | 0.83 | 🟡 | 0.20 | → |
| 2 | Event Bus | 0.65 | 🟡 | 0.10 | → |
| 3 | Provider Fabric | 0.55 | 🟡 | 0.10 | ↓ |
| 4 | Governance | 0.45 | 🔴 | 0.15 | → |
| 5 | Observability | 0.65 | 🟡 | 0.10 | → |
| 6 | Recovery | 0.65 | 🟡 | 0.10 | → |
| 7 | Replay | 0.75 | 🟡 | 0.05 | → |
| 8 | KRATOS | 0.20 | 🔴 | 0.10 | → |
| 9 | Memory/Akasha | 0.65 | 🟡 | 0.05 | → |
| 10 | Mission Execution | 0.60 | 🟡 | 0.05 | → |
| | **WEIGHTED TOTAL** | **0.61** | 🟡 | 1.00 | ↓ |

---

## Component-Level Drill-Down

### Runtime Core — 0.83 🟡
```
Execution Graph:    ██████████████████░ 0.95
Mission State:      █████████████████░░ 0.85
EventBus:           ████████████████░░░ 0.80
CLI Commands:       ████████████████░░░ 0.80
Envelope v2:        ███████████████████ 0.95
ReplayBuffer:       ███████████████░░░░ 0.75
```

### Event Bus — 0.65 🟡
```
Redis :6381:        ██████████████████░ 0.95
10 Channels:        ██████████████████░ 0.95
Consumers:          ░░░░░░░░░░░░░░░░░░░ 0.00
Envelope:           ███████████████████ 0.95
```

### Provider Fabric — 0.55 🟡
```
Interface:          ████████████████░░░ 0.80
Tier Routing:       ████████████████░░░ 0.80
Fallback:           ██████████░░░░░░░░░ 0.50
Cost Tracking:      ████░░░░░░░░░░░░░░░ 0.20
Model Config:       ██████████░░░░░░░░░ 0.50
```

### Governance — 0.45 🔴
```
Audit Log:          ████████████████░░░ 0.80
Risk Classifier:    ███████████████░░░░ 0.75
Approval Gate:      ███████████████░░░░ 0.75
Human Slot:         ░░░░░░░░░░░░░░░░░░░ 0.00
Decision Log:       ░░░░░░░░░░░░░░░░░░░ 0.00
Action Classifier:  ░░░░░░░░░░░░░░░░░░░ 0.00
```

### Observability — 0.65 🟡
```
Metrics Spine:      ██████████████████░ 0.90
Tracer:             ████████████████░░░ 0.80
Health Bridge:      ███████████████████ 0.95
Error Taxonomy:     ███████████████░░░░ 0.75
Logging:            ████████████░░░░░░░ 0.60
```

### Recovery — 0.65 🟡
```
Checkpoint/Resume:  ██████████████████░ 0.90
Replay:             █████████████████░░ 0.85
Self-Healing:       ██████████████████░ 0.90
Watchdog:           ░░░░░░░░░░░░░░░░░░░ 0.00
Circuit Breaker:    ██████░░░░░░░░░░░░░ 0.30
```

### Replay — 0.75 🟡
```
Graph Replay:       ██████████████████░ 0.90
Mission Replay:     █████████████████░░ 0.85
EventBus Replay:    █████████████░░░░░░ 0.65
Recovery Replay:    ██████████████░░░░░ 0.70
```

### KRATOS — 0.20 🔴
```
Dashboard:          ░░░░░░░░░░░░░░░░░░░ 0.00
Health Feed:        ██████████░░░░░░░░░ 0.50
Mission Visibility: ░░░░░░░░░░░░░░░░░░░ 0.00
Event Stream:       ░░░░░░░░░░░░░░░░░░░ 0.00
Bridge Contract:    ██████████████████░ 0.90
```

### Memory/Akasha — 0.65 🟡
```
Akasha DB:          ████████████████░░░ 0.80
Biblioteca:         █████████████████░░ 0.85
Obsidian:           ██████████░░░░░░░░░ 0.50
memory_lookup:      ████████████░░░░░░░ 0.60
```

### Mission Execution — 0.60 🟡
```
Contract Model:     ███████████████████ 0.95
Event Persistence:  ███████████████████ 0.95
Checkpoint:         ██████████████████░ 0.90
Full Lifecycle:     ░░░░░░░░░░░░░░░░░░░ 0.00
Package Extension:  ██████░░░░░░░░░░░░░ 0.30
```

---

## Infrastructure Health

| Service | Health | Weight | Score |
|---------|--------|--------|-------|
| Docker (redis) | 1.00 | 0.25 | 0.250 |
| Docker (others) | 0.50 | 0.15 | 0.075 |
| Ollama | 0.90 | 0.20 | 0.180 |
| Disk | 0.90 | 0.15 | 0.135 |
| Python | 1.00 | 0.15 | 0.150 |
| Git | 1.00 | 0.10 | 0.100 |
| **Infrastructure** | | | **0.89** |

---

## Health Trend Analysis

| Milestone | Overall | Runtime | Gov | Obs | KRATOS | Recovery |
|-----------|---------|---------|-----|-----|--------|----------|
| Phase 3 baseline | 0.43 | 0.60 | 0.40 | 0.40 | 0.20 | 0.50 |
| Phase 4 activation | 0.78 | 0.85 | 0.70 | 0.65 | 0.50 | 0.90 |
| TORRE REALTIME #1 | 0.67 | 0.85 | 0.70 | 0.70 | 0.25 | 0.75 |
| **GLOBAL EVAL (now)** | **0.61** | **0.83** | **0.45** | **0.65** | **0.20** | **0.65** |

**Why the drop?** The GLOBAL evaluation model is the strictest yet:
- KRATOS weight increased from 0.05 to 0.10 (dashboard is the operator's window)
- Governance weight increased from 0.10 to 0.15 (safety layer)
- Provider Fabric dropped from 0.80→0.55 (ANTHROPIC_KEY still missing, no cost data)
- Recovery dropped from 0.90→0.65 (watchdog and circuit breaker scored at 0)

---

## Critical Health Risks

| Risk | Domain | Score Impact |
|------|--------|-------------|
| KRATOS 100% mock | Dashboard | -0.08 |
| Governance 3/6 dead | Safety | -0.08 |
| No consumers | EventBus | -0.04 |
| No watchdog | Recovery | -0.02 |
| Provider not wired | Missions | -0.02 |
| Dashboard collectors zero | Observability | -0.01 |

**Total recoverable health:** 0.86 (fixing these 6 items would bring score from 0.61 to 0.86)
