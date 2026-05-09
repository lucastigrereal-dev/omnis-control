# P8.1 Step Runner Dry-Run — Report

**Data:** 2026-05-09 | **Status:** DONE

---

## Arquivos criados/alterados

```
src/execution_graph/runner.py          — run_graph_dry(), failure injection
src/execution_graph/store.py           — JSONL append-only event store
src/execution_graph/models.py          — +StepRun, StepRunLog, _make_run_id
src/cli_commands/execution_graph_cmd.py — +graph run|run-show|run-list
tests/execution_graph/test_step_runner.py — 21 testes
```

---

## Modelos novos

### StepRunLog
Evento individual de execução: step_id, role_id, status, message, timestamp

### StepRun
Execução completa de um grafo:
- graph_run_id, graph_id, request
- status: running | done | failed
- step_states: dict[step_id → status]
- logs: list[StepRunLog]
- started_at, finished_at

---

## Runner

`run_graph_dry(graph, fail_at=None) → StepRun`

- Itera steps em topological order
- Cada step: PENDING → RUNNING → DONE (ou FAILED se fail_at)
- Falha em step N → todos downstream marcados SKIPPED
- Log duplo por step (running + done/failed)
- Zero side effects, determinístico

---

## Store

```
exports/graph_runs/<grun_id>/
  manifest.json    — StepRun completo
  events.jsonl     — append-only event log (pendente uso futuro)
```

Funções:
- `append_event(run_dir, event)` — JSONL append
- `read_events(run_dir)` — lista todos eventos
- `get_step_state(run_dir)` — reconstrói estado atual
- `write_manifest(run_dir, manifest)` — salva JSON completo
- `read_manifest(run_dir)` — carrega JSON

---

## CLI

```bash
python jarvis.py graph run "<request>"              # dry-run completo
python jarvis.py graph run "<request>" --json        # output JSON
python jarvis.py graph run-show <run_id>             # detalhes
python jarvis.py graph run-show <run_id> --json      # detalhes JSON
python jarvis.py graph run-list                      # lista runs
python jarvis.py graph run-list --json               # lista JSON
```

---

## Testes

```
tests/execution_graph/test_step_runner.py: 21/21 PASS
  - 3 unit (log, run, id generation)
  - 5 runner success (marketing, all executed, ordered, running→done, all done)
  - 3 failure injection (fail status, skip downstream, no fail=all done)
  - 1 empty graph raises
  - 6 store (append/read, empty, state, manifest write/read, nonexistent)
  - 1 integration (runner persists to store)
  - 4 CLI smoke (run, run --json, run-show, run-list)

P8.0 + P8.1 acumulado: 37/37 PASS
```
