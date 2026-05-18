# /omnis-status

Estado completo do OMNIS CONTROL.

## Ações
1. `git status --short` — working tree
2. `git branch --show-current` — branch atual
3. `git log --oneline -5` — últimos commits
4. Ler `docs/project-os/CURRENT_STATE.md`
5. Ler `.claude/state/current-state.json`
6. Reportar: branch, commit, suite, blockers, working tree, próxima ação

## Output
```
OMNIS STATUS — {{DATE}} {{TIME}}
Branch: {{BRANCH}}
Commit: {{LAST_COMMIT}} — {{MESSAGE}}
Suite: {{PASSED}}/{{TOTAL}} ({{FAILURES}} failures)
Working tree: {{CLEAN/DIRTY}} ({{UNTRACKED}} untracked)
P0: {{P0_COUNT}} | P1: {{P1_COUNT}}
Próxima ação: {{NEXT_ACTION}}
```
