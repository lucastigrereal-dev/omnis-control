# OMNIS Current State

**Fonte machine-readable:** `omnis_state.yaml`
**Atualizado:** 2026-05-17

## Estado Resumido

Fase: `project_os_bootstrap` — criando camada de governança do repositório.

## Entregas Confirmadas

| Domínio | Waves | Commits |
|---|---|---|
| AppFactory Inicial | W131, W132 | d6f61e6 |
| Runtime Missions | W181-W185, W191-W195 | 5dd22c9, f397eca, b539c3f, 18e234f, 8f48bbb |
| Health Bridge | G23 | ed594dd |
| Maintenance | W201-W205 | Branch separada |

## Bloqueadores

| Severidade | ID | Status |
|---|---|---|
| **P0** | secret_litellm_connectors_yaml | Aberto — possível chave em config/connectors.yaml:82 |
| P1 | reports_ccos_logs_not_ignored | Aberto |
| P1 | health_branch_possible_duplicate | Aberto |
| P1 | templates_waiting_runtime_health | Aberto |

## Worktrees Ativos

| Worktree | Branch | Status |
|---|---|---|
| omnis-control | feature/omnis-5waves-runtime-supreme | ACTIVE |
| omnis-maintenance | feature/omnis-maintenance-w201-w205 | REVIEW |
| omnis-appfactory | feature/omnis-appfactory-w133-w162 | ACTIVE |
| omnis-health | feature/omnis-health-w196-w200 | PAUSED |
| omnis-templates | feature/omnis-templates-w206-w215 | PAUSED |
| omnis-runtime | feature/omnis-runtime-w186-w195 | REDUNDANT |

## Próxima Ação Segura

1. **P0:** Tratar segredo LiteLLM sem exibir valor
2. **P0:** Impedir G24 duplicado na principal
3. **P1:** Revisar Maintenance branch
4. **P1:** Comparar Health branch com ed594dd
