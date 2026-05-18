# OMNIS Active Worktrees

**Fonte:** `git worktree list`

| Worktree | Branch | Status | Path |
|---|---|---|---|
| omnis-control | feature/omnis-5waves-runtime-supreme | CONSOLIDATED | C:/Users/lucas/omnis-control |
| omnis-appfactory | master | DONE_ON_MASTER | C:/Users/lucas/omnis-appfactory |
| omnis-health | feature/omnis-health-w196-w200 | MERGED_CANONICAL | C:/Users/lucas/omnis-health |
| omnis-maintenance | feature/omnis-maintenance-w201-w205 | MERGED | C:/Users/lucas/omnis-maintenance |
| omnis-templates | feature/omnis-templates-w206-w215 | REDUNDANT | C:/Users/lucas/omnis-templates |
| omnis-runtime | feature/omnis-runtime-w186-w195 | REDUNDANT | C:/Users/lucas/omnis-runtime |
| omnis-p20-supreme | parallel/p20-omnis-supreme | ARCHIVE | C:/Users/lucas/omnis-p20-omnis-supreme |
| omnis-runtime-bridge | feature/omnis-g14-app-factory | ACTIVE_DEV | C:/Users/lucas/omnis-runtime-bridge |

## Política de Worktree
- **Nunca apagar** sem autorização do Lucas
- **Nunca mergear** worktree sujo
- Stale > 7 dias: reportar, não apagar
- REDUNDANT: recomendar arquivação, não executar

## Recomendações de Arquivação
- omnis-templates (0 commits únicos)
- omnis-runtime (0 commits únicos)
- omnis-maintenance (já mergeado)
- omnis-health (já mergeado)
