# /omnis-merge-check <source_branch> <target_branch>

Verifica segurança de merge entre branches.

## Ações
1. `git log <target>..<source> --oneline` — commits únicos
2. `git diff --stat <target>...<source>` — arquivos tocados
3. Verificar conflitos de namespace
4. Verificar no-touch zones
5. Verificar worktrees ativos que possam conflitar
6. Recomendar: safe / unsafe / needs-rebase

## Output
```
MERGE CHECK: {{SOURCE}} → {{TARGET}}
Commits: {{COMMIT_COUNT}}
Arquivos: {{FILE_COUNT}}
Conflitos namespace: {{YES/NO}}
No-touch violado: {{YES/NO}}
Worktrees conflitantes: {{YES/NO}}
Veredito: {{SAFE/UNSAFE/NEEDS_REBASE}}
```
