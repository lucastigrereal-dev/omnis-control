# /omnis-error [error_message]

Triagem de erro com playbook.

## Ações
1. Se error_message fornecido: classificar contra ERROR_PLAYBOOK.md
2. Se não: mostrar últimos erros da suite
3. Identificar se é pré-existente ou novo
4. Recomendar ação baseada no playbook
5. Se erro novo não catalogado: adicionar ao playbook

## Output
```
ERRO: {{CLASSIFICATION}}
Causa provável: {{CAUSE}}
Diagnóstico: {{DIAGNOSTIC}}
Ação recomendada: {{ACTION}}
Proibido: {{FORBIDDEN}}
Quando parar: {{STOP_CONDITION}}
```
