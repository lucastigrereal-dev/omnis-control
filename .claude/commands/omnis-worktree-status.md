# /omnis-worktree-status

Status de todos os worktrees.

## Ações
1. `git worktree list` — worktrees existentes
2. Ler `docs/project-os/ACTIVE_WORKTREES.md`
3. Para cada worktree: branch, último commit, status, recomendação
4. Identificar worktrees para arquivar
5. Identificar conflitos potenciais

## Output
```
WORKTREES — {{DATE}}
{{WORKTREE}} — {{BRANCH}} — {{STATUS}}
  Path: {{PATH}}
  Commit: {{LAST_COMMIT}}
  Recomendação: {{ARCHIVE/KEEP/MERGE}}
  
Total: {{COUNT}} | Arquiváveis: {{ARCHIVABLE}}
```
