# Worktree Stale Removal Review

**Date:** 2026-05-22
**Mode:** REVIEW ONLY — NO removal executed

---

## All Worktrees

| # | Path | Branch | Last Commit | Date | Status |
|---|------|--------|-------------|------|--------|
| 1 | C:\Users\lucas\omnis-control | feature/omnis-5waves-runtime-supreme | 6cd48d2 | May 21 | ACTIVE (current) |
| 2 | C:\Users\lucas\omnis-appfactory | master | 63a012c | May 16 | SHADOW |
| 3 | .claude/worktrees/p23-autonomous-execution | parallel/p23-autonomous-execution | 3507331 | May 14 | STALE |
| 4 | .claude/worktrees/p24-live-cockpit | parallel/p24-live-cockpit | 97616dc | May 14 | STALE |
| 5 | .claude/worktrees/p25-p29-sequential-supreme | parallel/p25-p29-sequential-supreme | 0183528 | May 14 | STALE |
| 6 | C:\Users\lucas\omnis-health | feature/omnis-health-w196-w200 | 190520a | May 17 | ACTIVE |
| 7 | C:\Users\lucas\omnis-maintenance | feature/omnis-maintenance-w201-w205 | e882432 | May 17 | STALE (tagged) |
| 8 | C:\Users\lucas\omnis-runtime | feature/omnis-runtime-w186-w195 | 233cdf4 | May 17 | ACTIVE |
| 9 | C:\Users\lucas\omnis-runtime-bridge | feature/omnis-g14-app-factory | cf47e0b | May 16 | SHADOW |
| 10 | C:\Users\lucas\omnis-templates | feature/omnis-templates-w206-w215 | 233cdf4 | May 17 | ACTIVE |

---

## STALE — Candidate for Removal (4 worktrees)

### 1. p23-autonomous-execution
- **Path:** C:\Users\lucas\omnis-control\.claude\worktrees\p23-autonomous-execution
- **Branch:** parallel/p23-autonomous-execution
- **Last commit:** 3507331 — "feat: add p23 autonomous execution skeleton" (May 14)
- **Razão:** Phase skeleton, 8 dias sem atividade, absorvido pelo autopilot
- **Risco:** Baixo — branch pode ser tagged antes da remoção

### 2. p24-live-cockpit
- **Path:** C:\Users\lucas\omnis-control\.claude\worktrees\p24-live-cockpit
- **Branch:** parallel/p24-live-cockpit
- **Last commit:** 97616dc — "feat: add p24 live cockpit supreme skeleton" (May 14)
- **Razão:** Phase skeleton, 8 dias sem atividade
- **Risco:** Baixo

### 3. p25-p29-sequential-supreme
- **Path:** C:\Users\lucas\omnis-control\.claude\worktrees\p25-p29-sequential-supreme
- **Branch:** parallel/p25-p29-sequential-supreme
- **Last commit:** 0183528 — "feat(p29): add omnis os layer skeleton" (May 14)
- **Razão:** Phase skeleton, 8 dias sem atividade
- **Risco:** Baixo

### 4. omnis-maintenance
- **Path:** C:\Users\lucas\omnis-maintenance
- **Branch:** feature/omnis-maintenance-w201-w205
- **Last commit:** e882432 — "feat(audit): W205 skill reports index" (May 17)
- **Razão:** EG-007 constitutional decision — tagged as archive/omnis-maintenance-execution-graph
- **Risco:** Baixo — tag criado, dados preservados

---

## SHADOW — Manter por enquanto (2 worktrees)

### 5. omnis-appfactory
- **Path:** C:\Users\lucas\omnis-appfactory
- **Branch:** master
- **Razão:** App Factory é ativo separado, pode ser reativado

### 6. omnis-runtime-bridge
- **Path:** C:\Users\lucas\omnis-runtime-bridge
- **Branch:** feature/omnis-g14-app-factory
- **Razão:** G14 App Factory ainda em desenvolvimento

---

## ACTIVE — NÃO remover (4 worktrees)

### 7-10. omnis-runtime, omnis-templates, omnis-health, omnis-control (current)

---

## Comandos de Remoção (NÃO EXECUTAR sem autorização)

```bash
# STALE worktrees — remover com tag de arquivo
git -C C:/Users/lucas/omnis-control worktree remove .claude/worktrees/p23-autonomous-execution
git -C C:/Users/lucas/omnis-control worktree remove .claude/worktrees/p24-live-cockpit
git -C C:/Users/lucas/omnis-control worktree remove .claude/worktrees/p25-p29-sequential-supreme
git -C C:/Users/lucas/omnis-control worktree remove C:/Users/lucas/omnis-maintenance

# Depois, deletar branches correspondentes
git -C C:/Users/lucas/omnis-control branch -d parallel/p23-autonomous-execution
git -C C:/Users/lucas/omnis-control branch -d parallel/p24-live-cockpit
git -C C:/Users/lucas/omnis-control branch -d parallel/p25-p29-sequential-supreme
git -C C:/Users/lucas/omnis-control branch -d feature/omnis-maintenance-w201-w205
```

---

## Verdict
4 worktrees STALE (removíveis com tag) + 2 SHADOW (manter) + 4 ACTIVE (não tocar).
Nenhuma remoção executada — aguardando autorização do operador.
