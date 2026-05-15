# WAVE 003 — Test Readiness & Full Suite Verification

## Objetivo
Executar full suite, documentar cobertura, comparar com baseline, garantir que todos os modulos tem testes adequados.

## Setor principal
Produto & Tecnologia (Setor 5)

## Skills ativadas
sc:test, gsd:verify-work, review, jarvis-decide

## Dependencias
W001, W002

## Arquivos permitidos
`docs/OMNIS_TEST_*.md`, `docs/supreme_210/`

## Arquivos proibidos
`src/` (read-only), `tests/` (read-only), `.env`

## Risco
**LOW** — Execucao de testes, sem alteracao de codigo

## Testes obrigatorios
```sh
python -m pytest tests/ --import-mode=importlib -p no:warnings -q
```

## Rollback
N/A

---

## Blocos

### B1 — Test inventory
Listar todos os arquivos de teste, agrupar por modulo. Contar tests por modulo.

### B2 — Baseline comparison
Comparar resultados atuais com baseline do relatorio (5,901 passed, 4 skipped).

### B3 — Module coverage assessment
Para cada modulo: quantos tests, tipos de test (unit, integration, roundtrip, edge).

### B4 — Full suite execution
Rodar full suite. Registrar: passed, skipped, failed, duration, exit code.

### B5 — Skip analysis
Investigar cada skipped test. E condicional legitimo ou bug?

### B6 — Warning analysis
Investigar collection warnings. Sao cosmeticos ou indicam problemas?

### B7 — Slow test identification
Identificar testes mais lentos. Algum acima de 5s?

### B8 — Coverage gaps
Identificar modulos sem testes ou com cobertura insuficiente.

### B9 — Test readiness document
Criar/atualizar `docs/OMNIS_TEST_READINESS_SUMMARY.md`.

### B10 — Wave validation and report
Consolidar, gerar `reports/WAVE_003_REPORT.md`.

---

**Status:** PLANNED
