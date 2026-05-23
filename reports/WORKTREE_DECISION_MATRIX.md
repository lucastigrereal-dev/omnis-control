# WORKTREE DECISION MATRIX — OMNIS CONTROL

Generated: 2026-05-23
Mode: audit only / no cleanup / no revert / no delete
Branch: `feature/omnis-5waves-runtime-supreme`

## Current Safe Checkpoint

| Item | Value |
|---|---|
| Last code checkpoint | `28896e0 fix(wave-0): restore green suite after interrupted claude run` |
| Last memory checkpoint | `245560b docs(claude): capture wave-0 recovery checkpoint` |
| Last verified suite | `8846 passed, 4 skipped` |
| Gate | STOP at Wave 0. Do not advance Wave 1 without Lucas GO. |

## Decision Summary

| Bucket | Recommendation | Risk | Action |
|---|---|---:|---|
| Canonical refinement | Commit now in dedicated docs commit | P1 | Codex selected latest Downloads source |
| Runtime snapshots | Do not commit as source | P2 | Leave uncommitted or archive later |
| Generated templates | Do not commit now | P2 | Regenerate intentionally in dedicated commit if needed |
| Tower/global reports | Preserve, but decide location | P1 | Commit only if Torre declares canonical |
| Logs/replays/checkpoints | Do not commit by default | P2 | Add ignore/archive policy later |
| Test compatibility drift | Already covered by code commits; do not commit old test edits blindly | P1 | Re-evaluate only if needed |

## Bucket A — Confirmed Source Of Truth

### `docs/project-os/OMNIS_REFINAMENTO_50_DECISOES.md`

Classification: CANONICAL_CONFIRMED
Evidence: `C:\Users\lucas\Downloads\OMNIS_REFINAMENTO_50.md` explicitly states it is an annex to `OMNIS_BLUEPRINT_CANONICO.md`, has the same authority as the blueprint, and that conflicts are resolved by the newer document. D-Q50 defines the hierarchy: live code > Blueprint + Refinement > historical reports > external research.
Reason to keep: It resolves the 60-failure preflight, defines T-006/T-019 decisions, and closes the execution contract Claude Code should follow after interruption.
Risk: Medium. It is an architecture/execution contract, not proof of runtime behavior. Code and tests still outrank it.
Recommendation: Commit `docs/project-os/OMNIS_REFINAMENTO_50_DECISOES.md` now, using the latest Downloads version as the source.

## Bucket B — Runtime Snapshot Docs

### `docs/ESTADO_ATUAL_RESUMIDO.md`

Classification: RUNTIME_SNAPSHOT
Evidence: Diff changes generated timestamp, session id, Docker container counts and scan duration.
Recommendation: Do not include in source-truth commit. If needed, commit only in a dedicated runtime snapshot commit.

### `docs/disk_audit_report.json`

Classification: RUNTIME_SNAPSHOT
Evidence: Diff updates generated timestamp and disk free/used numbers.
Recommendation: Do not commit as source by default. Treat as generated report.

### `config/paths.yaml`

Classification: TIMESTAMP_ONLY
Evidence: Diff only updates `_metadata.last_validated`.
Recommendation: Do not commit alone. If paths were not semantically changed, leave out.

## Bucket C — Generated Templates

### `templates/**/*.json`

Classification: GENERATED_TIMESTAMP_REFRESH
Evidence: Representative diff for `templates/automation/automation_skill_jarvis-router.json` changes only `created_at` and `updated_at`. Registry diff shows `updated_at` and per-template timestamps refreshed.
Recommendation: Do not commit now. If template regeneration is desired, run the generator intentionally and commit all templates in one explicit `chore(templates)` commit.

Affected tracked files:

- `templates/template_registry.json`
- `templates/automation/*.json`
- `templates/marketing/*.json`
- `templates/ops/*.json`

## Bucket D — Tower / Global Reports

### `reports/GLOBAL_*.md`

Classification: REPORT_PACKAGE
Evidence: Untracked report package dated 2026-05-22, including `OMNIS_GLOBAL_EVALUATION_MASTER_REPORT.md` with readiness and fake/real runtime classification.
Recommendation: Preserve. Commit only if Torre says these are canonical package outputs. Otherwise move/keep in external audit package later with explicit GO.

### `reports/TOWER_*.md`

Classification: TOWER_REPORT_PACKAGE
Evidence: Untracked Tower state/reconciliation reports, e.g. `TOWER_MASTER_STATE.md` says Authority `TORRE CENTRAL` and lists Phase 4/ABA state.
Recommendation: Preserve. Do not delete. Do not mix with Wave 0 fix commits. Best commit shape, if approved: `docs(tower): add phase4 central command reports`.

Important conflict:

- Some reports mention older test counts or readiness states that predate the green checkpoint `8846 passed, 4 skipped`.
- If committed, add a header or companion note saying they are Tower snapshots, not current code truth.

## Bucket E — Logs, Audit Trail, Replays, Checkpoints

### `data/audit/20260522.jsonl`

Classification: RUNTIME_LOG
Evidence: JSONL entries from `audit_trail`, `war_room_bridge`, and sequence events.
Recommendation: Do not commit by default.

### `logs/events.log`

Classification: RUNTIME_LOG
Evidence: Redis listener operational logs with reconnect events and timestamps.
Recommendation: Do not commit. Consider `.gitignore` policy.

### `data/missions/checkpoints/**`

Classification: RUNTIME_CHECKPOINT
Evidence: Untracked checkpoint JSON under hashed mission checkpoint path.
Recommendation: Do not commit unless mission replay/checkpoint persistence is intentionally versioned.

### `missions/.replays/**`

Classification: GENERATED_REPLAY_PACKAGE
Evidence: 19 files, about 151 KB, including generated captions, reels, CSV, package zip, manifests and replay session.
Recommendation: Do not commit by default. If this is a demo asset, commit in a separate `demo(replay)` commit after Lucas approval.

## Bucket F — Large Aspirational / Strategy Doc

### `docs/OMNIS_SUPREME_EVOLUTION_REPORT.md`

Classification: STRATEGY_DOC_REWRITE
Evidence: Diff expands from 609 lines to 3521 lines and changes framing to "Enterprise · 50 Entregas · 4 Mega-Agências".
Risk: High chance of mixing vision with runtime truth. Some claims may be stale relative to the green Wave 0 checkpoint.
Recommendation: Do not commit with code. If needed, send to architecture review and commit separately only after reality reconciliation.

## Bucket G — Test File Drift

### `tests/skill_router_bridge/test_models.py`

Classification: TEST_EXPECTATION_DRIFT
Evidence: Diff changes tests from accepting arbitrary string intents to enum-backed `SkillIntent.CREATE` / `GENERATE`.
Context: Code fixes already restored compatibility through `SkillCall` and passed full suite without this file committed.
Recommendation: Do not commit now. The green checkpoint proves this edit is not required for current suite.

## Recommended Commit Plan

1. Commit the confirmed canonical refinement now:
   - `docs/project-os/OMNIS_REFINAMENTO_50_DECISOES.md`
   - `reports/WORKTREE_DECISION_MATRIX.md`
   - Suggested message: `docs(project-os): add canonical refinement decisions`.
2. If Torre approves report package:
   - Commit `reports/TOWER_*.md` and `reports/GLOBAL_*.md` separately.
   - Suggested message: `docs(tower): add phase4 reconciliation reports`.
3. Leave templates, logs, replays, runtime snapshots, and timestamp-only files out until there is an explicit artifact policy.

## Do Not Touch Without GO

- Do not run cleanup.
- Do not delete logs/replays.
- Do not revert user/Torre generated files.
- Do not stage all files.
- Do not run `git add .`.
- Do not advance Wave 1 until dirty worktree policy is decided.

## Next Safe Command

```powershell
git -C C:\Users\lucas\omnis-control status --short
```

If the next action is commit hygiene, use explicit paths only.
