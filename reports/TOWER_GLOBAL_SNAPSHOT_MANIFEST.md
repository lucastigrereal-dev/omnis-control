# TOWER / GLOBAL SNAPSHOT MANIFEST

Generated: 2026-05-23
Mode: preservation only / no runtime authority / no Wave 1 GO
Branch: `feature/omnis-5waves-runtime-supreme`

## Decision

The `TOWER_*.md`, `GLOBAL_*.md`, and `OMNIS_GLOBAL_EVALUATION_MASTER_REPORT.md` files are preserved as a strategic snapshot package.

Classification: SNAPSHOT_REFERENCE

Authority order:

1. Live code, tests, schemas, contracts, and runtime configs.
2. `docs/project-os/OMNIS_REFINAMENTO_50_DECISOES.md` plus the canonical Blueprint.
3. This Tower/Global snapshot package.
4. Older reports and external research.

This package is not a GO to advance Wave 1. It is a preserved map of Torre/Global findings that must be reconciled against the green Wave 0 checkpoint before execution.

## Included Files

### Global Evaluation Package

- `reports/GLOBAL_DRIFT_AND_FRAGMENTATION.md`
- `reports/GLOBAL_EXECUTION_TRUTH.md`
- `reports/GLOBAL_GOVERNANCE_TRUTH.md`
- `reports/GLOBAL_HEALTH_MATRIX.md`
- `reports/GLOBAL_KRATOS_TRUTH.md`
- `reports/GLOBAL_MEMORY_TRUTH.md`
- `reports/GLOBAL_OPERATIONAL_READINESS.md`
- `reports/GLOBAL_REALITY_EVALUATION.md`
- `reports/GLOBAL_SELF_HEALING_TRUTH.md`
- `reports/OMNIS_GLOBAL_EVALUATION_MASTER_REPORT.md`

### Tower Command Package

- `reports/TOWER_ABA_BRIEFINGS.md`
- `reports/TOWER_ABA_EXECUTION_MATRIX.md`
- `reports/TOWER_AUTHORITY_MATRIX.md`
- `reports/TOWER_BLOCKERS.md`
- `reports/TOWER_CENTRAL_COMMAND_FINAL_REPORT.md`
- `reports/TOWER_CONFLICT_ENGINE.md`
- `reports/TOWER_DASHBOARD_HANDOFF.md`
- `reports/TOWER_DASHBOARD_LIVE.md`
- `reports/TOWER_DRIFT_MATRIX.md`
- `reports/TOWER_GLOBAL_BLOCKERS.md`
- `reports/TOWER_GLOBAL_DRIFTS.md`
- `reports/TOWER_GLOBAL_NEXT_ACTIONS.md`
- `reports/TOWER_GLOBAL_READINESS.md`
- `reports/TOWER_GLOBAL_STATE.md`
- `reports/TOWER_LIVE_MONITORING.md`
- `reports/TOWER_MASTER_STATE.md`
- `reports/TOWER_NEXT_ACTIONS.md`
- `reports/TOWER_NEXT_ACTIONS_ENGINE.md`
- `reports/TOWER_REALTIME_AUTHORITY.md`
- `reports/TOWER_REALTIME_BLOCKERS.md`
- `reports/TOWER_REALTIME_DRIFT.md`
- `reports/TOWER_REALTIME_MASTER_REPORT.md`
- `reports/TOWER_RECONCILIATION_PROTOCOL.md`
- `reports/TOWER_RECOVERY_INCIDENTS.md`
- `reports/TOWER_RUNTIME_TRUTH.md`
- `reports/TOWER_SYSTEM_HEALTH.md`

## Excluded From Commit

The following artifact classes stay out of source control by default:

- runtime logs under `logs/`
- audit streams under `data/audit/`
- mission checkpoints under `data/missions/checkpoints/`
- replay packages under `missions/.replays/`
- timestamp-only runtime snapshots unless explicitly approved
- generated template refreshes unless regenerated intentionally as a template release

## Practical Rule

Use this package to understand what Torre saw. Use the green suite and canonical refinement to decide what Claude Code may execute next.
