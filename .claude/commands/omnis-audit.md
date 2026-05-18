# /omnis-audit

Auditoria completa do repositório.

## Ações
1. `git status --short` — classificar cada arquivo
2. Verificar secrets: `grep -r "secret\|token=\|api_key=\|password=" src/ config/ --include="*.py" --include="*.yaml" | grep -v "example\|mock\|placeholder\|env\|fake\|test_\|EXAMPLE"`
3. Verificar imports inseguros
4. Rodar suite completa
5. Verificar consistência entre YAMLs e docs
6. Reportar divergências

## Output
```
AUDIT — {{DATE}}
Secrets scan: {{CLEAN/ISSUES_FOUND}}
Suite: {{PASSED}}/{{TOTAL}}
Divergências YAML vs docs: {{COUNT}}
Working tree classificado: {{CLASSIFICATION}}
Recomendação: {{GO/NO-GO/CLEANUP_NEEDED}}
```
