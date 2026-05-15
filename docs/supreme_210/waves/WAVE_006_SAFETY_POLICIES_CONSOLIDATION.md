# WAVE 006 — Safety Policies Consolidation

## Objetivo
Consolidar todas as politicas de seguranca do OMNIS em um unico documento canonic. Revisar W12B1, W12B2, W12B5, W12B6, W12B7. Garantir que nao ha gaps.

## Setor principal
Produto & Tecnologia (Setor 5)

## Skills ativadas
security-review, jarvis-guardrails, sc:document, review

## Dependencias
W005 (governance scaffold)

## Arquivos permitidos
`docs/OMNIS_SAFETY_POLICIES_CONSOLIDATED.md`, `docs/supreme_210/`

## Arquivos proibidos
`src/`, `tests/`, `.env`

## Risco
**LOW** — Documentacao de seguranca, sem alteracao de codigo

## Testes obrigatorios
Import guard scan limpo, verificacao de cobertura de todos os boundaries

## Rollback
Reverter doc se incorreto

---

## Blocos

### B1 — Policy inventory
Listar todos os documentos de seguranca existentes: W12B1-B7, P41, W8B9, W9B7, W11B8.

### B2 — Gap analysis
Comparar politicas documentadas com boundaries necessarios. Algum boundary sem politica?

### B3 — Governance policy review
Revisar W12B1: principios, risk matrix, approval flow, merge/push policy.

### B4 — Consolidated security review
Revisar W12B2: wave-level findings, cross-cutting guarantees, boundary enforcement.

### B5 — Dry-run guarantee audit review
Revisar W12B5: confirmar 100% coverage, zero bypass mechanisms.

### B6 — External write block audit review
Revisar W12B6: forbidden zones, network call audit.

### B7 — Secrets boundary audit review
Revisar W12B7: import scan, .env access audit.

### B8 — Consolidated safety document
Criar `docs/OMNIS_SAFETY_POLICIES_CONSOLIDATED.md` unindo todas as descobertas.

### B9 — Safety checklist
Criar checklist de seguranca para ser usado em cada wave futura.

### B10 — Wave validation and report
Consolidar, gerar `reports/WAVE_006_REPORT.md`.

---

**Status:** PLANNED
