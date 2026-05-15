# OMNIS W12B3 — Architecture Review

**Date:** 2026-05-15
**Scope:** Post-Wave 11 architecture

## Module map

```
omnis-control/
├── src/
│   ├── control_tower/          # Phase orchestration
│   ├── execution_contracts/    # Contract models
│   ├── work_orders/            # Work order system
│   ├── skills_bridge/          # Skill registry bridge
│   ├── execution_queue/        # Job queue
│   ├── decision_log/           # Decision audit log
│   ├── runtime_orchestrator/   # Wave 7B: runtime orchestration
│   ├── war_room_bridge/        # Wave 7B: war room bridge
│   ├── skill_router_bridge/    # Wave 7B: skill router
│   ├── runtime_cli/            # Wave 7B: local CLI smoke
│   ├── health/                 # Health module
│   ├── skill_execution/        # W8: skill execution engine ← NEW
│   ├── akasha_runtime/         # W9: akasha memory bridge ← NEW
│   ├── remote_control/         # W10: telegram/whatsapp ← NEW
│   └── plugin_runtime/         # W11: MCP/plugin system ← NEW
├── tests/                      # Mirrors src/ structure
├── docs/                       # Architecture + wave reports
├── config/                     # YAML paths
└── data/                       # File-backed stores
```

## Design patterns

| Pattern | Where | Why |
|---|---|---|
| Dataclass models | All modules | Zero-dependency, to_dict/from_dict |
| Composite service | *Service, *Runtime classes | Single entry point, composable internals |
| Mock adapters | Adapter classes | Real connections opt-in only |
| Event bus | *EventBus, *EventLog | In-memory audit trail |
| Registry | *Registry classes | Indexed lookups with dedup |
| Permission gate | *PermissionGate classes | Risk→Action mapping with forbidden lists |

## Consistency checks

| Aspect | W8 | W9 | W10 | W11 |
|---|---|---|---|---|
| to_dict/from_dict | Yes | Yes | Yes | Yes |
| dry_run default | Yes | Yes | Yes | Yes |
| _new_id prefix | seb/ebr/ser | ak* | rc/rcr/ac/re | pcap/pmf/ps/mcpd |
| In-memory first | Yes | Yes | Yes | Yes |
| File-backed optional | No | Yes | No | No |
| Event system | SkillEventBus | Via service | RemoteEventLog | Via runtime |

## Verdict: CLEAN

Consistent patterns across all 4 new modules. No architectural drift.
All modules follow the same dataclass + composite + gate pattern established in Wave 7B.
