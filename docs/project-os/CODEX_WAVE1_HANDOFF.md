# CODEX WAVE 1 HANDOFF

Generated: 2026-05-23
Branch: `feature/omnis-5waves-runtime-supreme`
Mode: handoff only / no Wave 2 GO

## Paste This Into Claude Code

```text
Leia primeiro:
C:\Users\lucas\omnis-control\CLAUDE.md
C:\Users\lucas\omnis-control\docs\project-os\CODEX_WAVE1_HANDOFF.md
C:\Users\lucas\omnis-control\docs\project-os\OMNIS_REFINAMENTO_50_DECISOES.md
C:\Users\lucas\Downloads\OMNIS_BLUEPRINT_CANONICO.md
C:\Users\lucas\Downloads\OMNIS_ORQUESTRADOR.md

Contexto:
Codex já recuperou Wave 0 e adiantou os bloqueadores principais da Wave 1.
Não reimplemente esses commits. Confirme estado, rode a suite completa uma vez e só avance se verde.

Comando obrigatório antes de evoluir:
python -m pytest tests/ --import-mode=importlib -p no:warnings -q

Se a suite passar:
continue a partir do Blueprint + Refinamento 50, priorizando a próxima tarefa canônica ainda não concluída.

Se a suite falhar:
pare evolução, corrija somente o cluster que falhou, rode teste focado, commit seletivo, e reporte.

Não tocar:
KRATOS, .env, secrets, push, deploy, reset, clean, git add ., templates gerados, snapshots pendentes.
```

## Current Position

Wave 0 is recovered and green. Wave 1 has been partially executed by Codex to remove blockers before Claude Code resumes evolution.

Claude Code can trust these recent commits:

- `14b931e fix(router): enforce cost tracker during model execution`
- `3d0d9be fix(agentic): route apps sector to app factory squad`
- `80e50c8 test(architecture): add runtime governance meta-tests`
- `48007a1 test(skill-router): align skill call intent expectations`
- `4328c83 docs(tower): preserve global snapshot reports`
- `7c0f04e docs(project-os): add canonical refinement decisions`
- `245560b docs(claude): capture wave-0 recovery checkpoint`
- `28896e0 fix(wave-0): restore green suite after interrupted claude run`

## What Codex Fixed

### T-009 Runtime Governance

Added architecture meta-tests in `tests/architecture/test_runtime_governance.py`.

Coverage:

- direct `openai` / `anthropic` SDK imports are only allowed in provider adapters
- `CostTracker` raises `CostLimitError` when daily budget would be exceeded
- source code does not directly read `.env`
- source code does not dump full `os.environ`
- `print()` is limited to CLI/report boundaries

Focused verification:

```powershell
pytest tests/architecture/test_runtime_governance.py tests/multi_model_orchestration/test_cost_tracker.py -q
```

Last result: `18 passed`.

### T-101 AppFactory Squad Routing

Fixed sector drift between `apps` and `app_factory`.

Change:

- `SquadSelector.select("apps")` now routes to `SQD-APP`
- existing `app_factory` behavior is preserved

Focused verification:

```powershell
pytest tests/agentic/test_squad_selector.py tests/squad_composer/test_composer.py tests/execution_graph/test_execution_graph.py::test_build_graph_app_request -q
```

Last result: `39 passed`.

### T-102 / T-103 Router + CostTracker

Fixed real execution path so `ModelRouter` uses `CostTracker`.

Change:

- router checks budget before provider execution
- router records token cost after provider result
- tests cover pre-call blocking and post-call accounting

Focused verification:

```powershell
pytest tests/multi_model_orchestration/test_router.py tests/multi_model_orchestration/test_cost_tracker.py tests/architecture/test_runtime_governance.py -q
```

Last result: `30 passed`.

### T-104 Approval Gate

No code change needed. Existing implementation already validates high-risk approval lifecycle.

Focused verification:

```powershell
pytest tests/governance/test_approval_gate.py tests/execution_graph/test_e2e_pipeline.py::test_e2e_high_risk_full_lifecycle tests/execution_graph/test_e2e_pipeline.py::test_e2e_orchestrator_full_approval_flow tests/execution_graph/test_e2e_pipeline.py::test_e2e_orchestrator_approve_then_run -q
```

Last result: `29 passed`.

### T-105 Health

No code change needed.

Focused verification:

```powershell
pytest tests/omnis_health -q
```

Last result: `49 passed`.

## Do Not Touch Without New Decision

Leave these dirty files out of commits unless Lucas/Torre explicitly decides otherwise:

- `config/paths.yaml`
- `docs/ESTADO_ATUAL_RESUMIDO.md`
- `docs/disk_audit_report.json`
- `docs/OMNIS_SUPREME_EVOLUTION_REPORT.md`
- `templates/**/*.json`

Reason: they appear to be timestamp snapshots, generated templates, or large strategy docs requiring separate reconciliation.

## Next Best Step For Claude Code

Run one full suite once before moving into the next evolution wave:

```powershell
python -m pytest tests/ --import-mode=importlib -p no:warnings -q
```

If green, Claude Code can proceed to the next canonical evolution task from Blueprint + Refinement 50.

If not green, fix only the failing cluster and do not advance the wave.

## Exact Resume Checklist

1. Confirm working directory is `C:\Users\lucas\omnis-control`.
2. Run `git status --short`.
3. Confirm branch is `feature/omnis-5waves-runtime-supreme`.
4. Do not stage existing dirty snapshots/templates.
5. Run the full suite command above.
6. If green, record the result in the next handoff/report.
7. Select exactly one next canonical task from Blueprint + Refinement 50.
8. Lock scope before editing.
9. Run focused tests for that task.
10. Commit only touched files with explicit paths.

## Remaining Dirty Worktree Policy

Current dirty files are intentionally not resolved by this handoff.

Decision:

- `templates/**/*.json`: leave uncommitted unless doing a dedicated template regeneration release.
- `config/paths.yaml`: leave uncommitted if only timestamp/runtime validation changed.
- `docs/ESTADO_ATUAL_RESUMIDO.md`: leave uncommitted unless updating canonical state after a full green suite.
- `docs/disk_audit_report.json`: leave uncommitted; runtime snapshot.
- `docs/OMNIS_SUPREME_EVOLUTION_REPORT.md`: do not commit without reality reconciliation against Blueprint + Refinement 50.

## Next Candidate Tasks

Preferred order after full suite is green:

1. `T-019`: reconcile `OMNIS_SUPREME_EVOLUTION_REPORT.md` with Blueprint + Refinement 50, marking what is historical versus current.
2. `T-008`: define log retention/rotation policy for JSONL logs.
3. `T-017`: archive old Wave Registry epochs if the active registry becomes noisy.
4. Only then move toward Wave 2 integration work.

Do not start `T-201`, `T-202`, `T-203`, or KRATOS Bridge work until the full suite is green and Lucas explicitly accepts the next wave.

## Known Good Focused Tests

```powershell
pytest tests/architecture/test_runtime_governance.py tests/multi_model_orchestration/test_cost_tracker.py -q
pytest tests/agentic/test_squad_selector.py tests/squad_composer/test_composer.py tests/execution_graph/test_execution_graph.py::test_build_graph_app_request -q
pytest tests/multi_model_orchestration/test_router.py tests/multi_model_orchestration/test_cost_tracker.py tests/architecture/test_runtime_governance.py -q
pytest tests/governance/test_approval_gate.py tests/execution_graph/test_e2e_pipeline.py::test_e2e_high_risk_full_lifecycle tests/execution_graph/test_e2e_pipeline.py::test_e2e_orchestrator_full_approval_flow tests/execution_graph/test_e2e_pipeline.py::test_e2e_orchestrator_approve_then_run -q
pytest tests/omnis_health -q
```

## Stop Conditions

Stop and report instead of continuing if:

- full suite fails in more than one unrelated cluster
- a fix requires touching KRATOS
- a fix requires secrets, deploy, push, package install, Docker restart, migrations, or branch cleanup
- a generated template/snapshot needs to be committed
- Blueprint and runtime disagree on architecture authority

## Boundary

This handoff is not permission to touch KRATOS, push, deploy, read secrets, reset, clean, or commit generated templates.
