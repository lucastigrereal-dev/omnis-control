# WAVE 002 — Branch & Worktree Audit

## Objetivo
Auditar branches locais, remotas, worktrees e divergencias. Identificar branches legado e recomendar limpeza futura.

## Setor principal
Operacoes & Organizacao (Setor 7)

## Skills ativadas
jarvis-router, jarvis-brain, sc:git, sc:analyze, review

## Dependencias
W001 (merge readiness context)

## Arquivos permitidos
`docs/OMNIS_BRANCH_*.md`, `docs/supreme_210/`

## Arquivos proibidos
`src/`, `tests/`, `.env`

## Risco
**LOW** — Read-only audit

## Testes obrigatorios
Comandos git read-only executados sem erro

## Rollback
N/A

---

## Blocos

### B1 — Full branch inventory
Listar todas as branches locais e remotas com HEAD e mensagem. Gerar tabela completa.

### B2 — Worktree health check
Listar worktrees, verificar prunable, verificar se ha conflitos entre worktrees.

### B3 — Divergence map
Para cada branch vs master: commits ahead/behind. Identificar branches merged, divergentes, orphan.

### B4 — Legacy branch identification
Marcar branches que aparentam ser legado: snapshots, recovery stashes, sprints antigas merged.

### B5 — Remote branch audit
Listar branches em origin. Verificar quais tem equivalente local. Identificar stale remotes.

### B6 — Merge history trace
Rastrear quais branches ja foram merged segundo relatorios e git history.

### B7 — Fix branch evaluation
Avaliar branches de bug fix: ainda sao necessarias? Conteudo ja foi integrado?

### B8 — Cleanup recommendations
Propor plano de limpeza futura: o que remover, o que manter, ordem segura. NAO EXECUTAR.

### B9 — Branch audit document
Criar/atualizar `docs/OMNIS_BRANCH_AND_WORKTREE_AUDIT.md` com todas as descobertas.

### B10 — Wave validation and report
Consolidar, gerar `reports/WAVE_002_REPORT.md`.

---

**Status:** PLANNED
