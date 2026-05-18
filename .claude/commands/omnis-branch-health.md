# /omnis-branch-health [branch_name]

Saúde de uma branch específica.

## Ações
1. Se branch_name fornecido: analisar branch
2. Se não: analisar branch atual
3. `git log <branch> --oneline -10`
4. Verificar se está merged em master
5. Rodar testes se branch tem código
6. Verificar divergência de master

## Output
```
BRANCH HEALTH: {{BRANCH}}
Commits ahead of master: {{AHEAD}}
Commits behind master: {{BEHIND}}
Merged: {{YES/NO}}
Testes: {{PASSED}}/{{TOTAL}}
Divergência: {{SAFE/MODERATE/HIGH}}
Recomendação: {{MERGE/REBASE/KEEP/ARCHIVE}}
```
