# /omnis-safe-commit

Commit seletivo sem riscos.

## Ações
1. `git status --short` — listar TODOS os arquivos
2. Classificar cada arquivo (in-scope / out-of-scope / unknown)
3. Confirmar que NENHUM arquivo out-of-scope será staged
4. `git add <specific files>` — NUNCA git add .
5. `git diff --cached --stat` — revisar o que será commitado
6. Commit com mensagem convencional

## Anti-padrões bloqueados
- `git add .` — PROIBIDO
- `git add -A` — PROIBIDO
- `git commit -a` — PROIBIDO
- Commitar .env, secrets, keys — PROIBIDO

## Output
```
SAFE COMMIT
Staged: {{FILE_LIST}}
Diff: {{DIFF_STAT}}
Mensagem: {{COMMIT_MESSAGE}}
Prosseguir? [YES/NO]
```
