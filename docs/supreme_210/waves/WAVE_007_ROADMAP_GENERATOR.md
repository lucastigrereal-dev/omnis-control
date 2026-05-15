# WAVE 007 — Roadmap Generator

## Objetivo
Criar ferramenta/script que gera roadmap sequencial a partir dos arquivos de wave. CLI: `python -m omnis_control.roadmap generate`.

## Setor principal
Produto & Tecnologia (Setor 5)

## Skills ativadas
sc:implement, test-driven-development, sc:test

## Dependencias
W005, W006

## Arquivos permitidos
`src/omnis_control/roadmap.py`, `tests/test_roadmap.py`, `docs/supreme_210/`

## Arquivos proibidos
`.env`, `src/remote_control/`

## Risco
**LOW** — Codigo local, sem side effects

## Testes obrigatorios
```sh
python -m pytest tests/test_roadmap.py --import-mode=importlib -p no:warnings -v
```

## Rollback
Remover roadmap.py e tests

---

## Blocos

### B1 — Wave file parser
Parsear `docs/supreme_210/waves/WAVE_*.md` → dict com campos estruturados.

### B2 — Roadmap data model
Definir dataclasses: WaveInfo, BlockInfo, GroupInfo com to_dict/from_dict.

### B3 — Progress reader
Ler `OMNIS_SUPREME_210_WAVES_PROGRESS.md` e `progress/*.jsonl` → status atual.

### B4 — Report generator
Gerar markdown de roadmap a partir dos dados parseados.

### B5 — CLI command
`python -m omnis_control.roadmap generate --group 01 --format md`

### B6 — Status summary
`python -m omnis_control.roadmap status` — printa progresso atual.

### B7 — Next wave suggester
`python -m omnis_control.roadmap next` — sugere proximo prompt de execucao.

### B8 — Tests
Tests para parser, model, generator, CLI.

### B9 — Documentation
Docstring em todos os metodos publicos. Atualizar README.

### B10 — Wave validation and report
Consolidar, gerar `reports/WAVE_007_REPORT.md`.

---

**Status:** PLANNED
