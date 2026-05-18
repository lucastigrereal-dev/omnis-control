# /omnis-rc

Release candidate check local.

## Ações
1. Rodar RELEASE_CANDIDATE_CHECKLIST.md completo
2. Suite completa deve passar
3. Secrets scan deve estar limpo
4. Nenhum P0 aberto
5. Working tree classificado
6. Reportar GO/NO-GO/CONDITIONAL

## Output
```
OMNIS RC CHECK — {{DATE}}
[ ] Suite: {{PASSED}}/{{TOTAL}}
[ ] Secrets: {{CLEAN/ISSUES}}
[ ] P0: {{COUNT}}
[ ] Working tree: {{CLASSIFIED}}
[ ] Docs atualizados: {{YES/NO}}

VEREDITO: {{GO / NO-GO / CONDITIONAL}}
Se GO: pronto para push quando Lucas autorizar
Se CONDITIONAL: {{CONDITIONS}}
Se NO-GO: {{REASONS}}
```
