# OMNIS Wave Registry

**Fonte machine-readable:** `omnis_wave_registry.yaml`

## Legenda

| Status | Significado |
|---|---|
| DONE | Concluído e commitado |
| REVIEW | Concluído, precisa review antes de merge |
| ACTIVE | Em progresso |
| PAUSED | Pausado para evitar conflito |
| PENDING | Não iniciado |
| BLOCKED | Bloqueado por risco/erro/segredo |

## Waves

| ID | Grupo | Nome | Status | Commit |
|---|---|---|---|---|
| W131 | AppFactory | Idea Intake | DONE | — |
| W132 | AppFactory | PRD Generator | DONE | d6f61e6 |
| W133-W162 | AppFactory | AppFactory Advanced | ACTIVE | — |
| W181-W185 | Runtime | First Real Missions | DONE | 5dd22c9 |
| W191 | Runtime | Mission Event Bus | DONE | f397eca |
| W192 | Runtime | Mission Logs | DONE | b539c3f |
| W193 | Runtime | Mission Metrics Summary | DONE | 18e234f |
| W194-W195 | Runtime | Failure Taxonomy + Report Export | DONE | 8f48bbb |
| G23 | Health | Health Bridge | REVIEW | ed594dd |
| W201-W205 | Maintenance | Maintenance Audit | REVIEW | Branch separada |
| W206-W215 | Templates | Mission Templates + QA | PAUSED | — |

## Riscos

- **W201-W205:** HIGH — bloqueado por P0 (possível segredo)
- **W133-W162:** MEDIUM — ativo em worktree isolado
- **W206-W215:** MEDIUM — pausado aguardando consolidação
