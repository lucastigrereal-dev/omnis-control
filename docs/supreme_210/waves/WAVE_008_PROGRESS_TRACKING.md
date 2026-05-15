# WAVE 008 — Progress Tracking System

## Objetivo
Implementar sistema de tracking de progresso para as 210 waves: JSONL backend, CLI viewer, atualizacao automatica por wave.

## Setor principal
Produto & Tecnologia (Setor 5)

## Skills ativadas
gsd:progress, sc:document, jarvis-memory-write, sc:implement

## Dependencias
W007 (roadmap generator)

## Arquivos permitidos
`src/omnis_control/progress_tracker.py`, `tests/test_progress_tracker.py`, `docs/supreme_210/`

## Arquivos proibidos
`.env`, `data/` (runtime data dir)

## Risco
**LOW** — Apenas tracking local

## Testes obrigatorios
```sh
python -m pytest tests/test_progress_tracker.py --import-mode=importlib -p no:warnings -v
```

## Rollback
Remover tracker e tests

---

## Blocos

### B1 — Progress data model
Dataclasses: WaveProgress, BlockProgress, SessionSummary.

### B2 — JSONL backend
Append-only JSONL writer/reader em `docs/supreme_210/progress/`.

### B3 — Markdown updater
Atualizar `OMNIS_SUPREME_210_WAVES_PROGRESS.md` com dados do JSONL.

### B4 — Wave state machine
Transicoes: PLANNED → IN_PROGRESS → COMPLETE / BLOCKED / ABORTED.

### B5 — Block state machine
Transicoes: TODO → IN_PROGRESS → PASS / PASS_WITH_NOTES / BLOCKED / FAIL / SKIPPED.

### B6 — Summary calculator
Calcular: total waves done, blocos done, % completo, waves blocked, tempo medio.

### B7 — CLI viewer
`python -m omnis_control.progress --group 01 --format table`

### B8 — Auto-update hook
Atualizar progress tracking apos cada wave concluida.

### B9 — Tests
Tests para todas as transicoes de estado, JSONL read/write, summary calc.

### B10 — Wave validation and report
Consolidar, gerar `reports/WAVE_008_REPORT.md`.

---

**Status:** PLANNED
