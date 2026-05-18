# OMNIS Active Worktrees

**Fonte machine-readable:** `omnis_worktrees.yaml`

| Worktree | Branch | Role | Status | Escopo |
|---|---|---|---|---|
| omnis-control | feature/omnis-5waves-runtime-supreme | principal_orchestrator | ACTIVE | Runtime, Health, Project OS |
| omnis-maintenance | feature/omnis-maintenance-w201-w205 | maintenance_audit | REVIEW | W201-W205 |
| omnis-appfactory | feature/omnis-appfactory-w133-w162 | app_factory_advanced | ACTIVE | W133-W162 |
| omnis-health | feature/omnis-health-w196-w200 | health_bridge | PAUSED_COMPARE | W196-W200 |
| omnis-templates | feature/omnis-templates-w206-w215 | templates_qa | PAUSED | W206-W215 |
| omnis-runtime | feature/omnis-runtime-w186-w195 | runtime_parallel | REDUNDANT_READ_ONLY | W186-W195 |

## Regras por Worktree

### omnis-control (principal)
- Não rodar G24 Maintenance aqui
- Não duplicar W201-W205
- Não fazer push

### omnis-maintenance
- Resolver ou documentar risco de segredo antes de merge
- Sem deleções sem dry-run

### omnis-health
- Comparar com ed594dd antes de continuar

### omnis-appfactory
- Não tocar em Runtime
- Não tocar em Health
- Dry-run para scaffold

### omnis-templates
- Aguardar consolidação Runtime/Health

### omnis-runtime
- Não implementar a menos que auditoria anti-duplicação confirme necessidade
