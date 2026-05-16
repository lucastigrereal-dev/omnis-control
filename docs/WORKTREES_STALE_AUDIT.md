# WORKTREES STALE AUDIT

**Date:** 2026-05-16
**Auditor:** agent-qa + docs-release (OMNIS CCOS)
**Status:** AUDITADO — nenhuma remocao executada

---

## Worktrees ativos detectados

```
C:/Users/lucas/omnis-control/.claude/worktrees/p23-autonomous-execution   3507331 [parallel/p23-autonomous-execution]
C:/Users/lucas/omnis-control/.claude/worktrees/p24-live-cockpit           97616dc [parallel/p24-live-cockpit]
C:/Users/lucas/omnis-control/.claude/worktrees/p25-p29-sequential-supreme 0183528 [parallel/p25-p29-sequential-supreme]
C:/Users/lucas/omnis-p20-omnis-supreme                                    88ef666 [parallel/p20-omnis-supreme]
```

---

## Detalhamento

### 1. P20 — `omnis-p20-omnis-supreme`
| Campo | Valor |
|---|---|
| Path | `C:/Users/lucas/omnis-p20-omnis-supreme` |
| Branch | `parallel/p20-omnis-supreme` |
| Commit | `88ef666` |
| Onda | P20 — Omnis Supreme |
| Stale? | SIM — onda concluida ha varias semanas |
| Tem trabalho nao comitado? | NAO verificado |

### 2. P23 — `p23-autonomous-execution`
| Campo | Valor |
|---|---|
| Path | `C:/Users/lucas/omnis-control/.claude/worktrees/p23-autonomous-execution` |
| Branch | `parallel/p23-autonomous-execution` |
| Commit | `3507331` |
| Onda | P23 — Autonomous Execution |
| Stale? | SIM — onda concluida |
| Tem trabalho nao comitado? | NAO verificado |

### 3. P24 — `p24-live-cockpit`
| Campo | Valor |
|---|---|
| Path | `C:/Users/lucas/omnis-control/.claude/worktrees/p24-live-cockpit` |
| Branch | `parallel/p24-live-cockpit` |
| Commit | `97616dc` |
| Onda | P24 — Live Cockpit |
| Stale? | SIM — onda concluida |
| Tem trabalho nao comitado? | NAO verificado |

### 4. P25-P29 — `p25-p29-sequential-supreme`
| Campo | Valor |
|---|---|
| Path | `C:/Users/lucas/omnis-control/.claude/worktrees/p25-p29-sequential-supreme` |
| Branch | `parallel/p25-p29-sequential-supreme` |
| Commit | `0183528` |
| Onda | P25-P29 — Sequential Supreme |
| Stale? | SIM — onda concluida |
| Tem trabalho nao comitado? | NAO verificado |

---

## Analise de Risco

| Risco | Nivel |
|---|---|
| `omnis-sync-claude.ps1` tentara sincronizar .claude/ com worktrees stale | BAIXO — so se paths existirem e script for executado |
| `spawn-worktrees` pode se confundir com paths similares | BAIXO |
| Consumo de disco desnecessario | MEDIO — ~4 copias do repositorio |
| Branches orfas no repositorio | BAIXO — branches `parallel/*` continuam existindo independentemente |

---

## Comandos para remocao (NAO EXECUTAR AINDA)

```powershell
# So executar apos aprovacao explicita de Lucas
# Verificar antes se cada worktree nao tem trabalho nao comitado:
git -C C:/Users/lucas/omnis-p20-omnis-supreme status --short
git -C C:/Users/lucas/omnis-control/.claude/worktrees/p23-autonomous-execution status --short
git -C C:/Users/lucas/omnis-control/.claude/worktrees/p24-live-cockpit status --short
git -C C:/Users/lucas/omnis-control/.claude/worktrees/p25-p29-sequential-supreme status --short

# Se todos limpos, remover:
git worktree remove C:/Users/lucas/omnis-p20-omnis-supreme
git worktree remove C:/Users/lucas/omnis-control/.claude/worktrees/p23-autonomous-execution
git worktree remove C:/Users/lucas/omnis-control/.claude/worktrees/p24-live-cockpit
git worktree remove C:/Users/lucas/omnis-control/.claude/worktrees/p25-p29-sequential-supreme

# Opcional: deletar branches
git branch -d parallel/p20-omnis-supreme
git branch -d parallel/p23-autonomous-execution
git branch -d parallel/p24-live-cockpit
git branch -d parallel/p25-p29-sequential-supreme
```

---

## Recomendacao

Remover os 4 worktrees stale antes de criar novos para Wave 7B. Nao ha razao para mante-los — todos pertencem a ondas ja concluidas e mergeadas.
