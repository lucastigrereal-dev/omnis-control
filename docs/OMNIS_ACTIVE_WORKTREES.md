# OMNIS Active Worktrees

**Fonte machine-readable:** `omnis_worktrees.yaml`
**Atualizado:** 2026-05-18

## Worktrees

| Worktree | Branch | Role | Status | Ação |
|---|---|---|---|---|
| omnis-control | feature/omnis-5waves-runtime-supreme | principal_orchestrator | CONSOLIDATED | Merge gate |
| omnis-maintenance | feature/omnis-maintenance-w201-w205 | maintenance_audit | MERGED_ARCHIVE | Arquivar |
| omnis-health | feature/omnis-health-w196-w200 | health_bridge_complete | VALUE_ADDED | Lucas decide |
| omnis-appfactory | master | app_factory_advanced | DONE_ON_MASTER | Manter read-only |
| omnis-templates | feature/omnis-templates-w206-w215 | templates_qa | REDUNDANT | Arquivar |
| omnis-runtime | feature/omnis-runtime-w186-w195 | runtime_parallel | REDUNDANT | Arquivar |
| omnis-p20-supreme | parallel/p20-omnis-supreme | p20_experiment | ARCHIVE_RECOMMENDED | Arquivar |
| omnis-runtime-bridge | feature/omnis-g14-app-factory | app_factory_dev | ACTIVE_DEV | Não tocar |

## Recomendações de Arquivação

```sh
# Worktrees com 0 commits únicos:
git worktree remove C:/Users/lucas/omnis-templates
git worktree remove C:/Users/lucas/omnis-runtime

# Worktrees já mergeados/concluídos:
git worktree remove C:/Users/lucas/omnis-maintenance
git worktree remove C:/Users/lucas/omnis-p20-omnis-supreme
```
