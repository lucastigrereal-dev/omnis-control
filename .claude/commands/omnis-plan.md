# /omnis-plan

Planeja a próxima wave ou ação com escopo travado.

## Ações
1. Identificar wave alvo (via /omnis-next ou parâmetro)
2. Ler manual relevante (APP_FACTORY_MANUAL.md, CCOS_RUNTIME_MANUAL.md, etc.)
3. Listar arquivos a criar/modificar
4. Confirmar que nenhum arquivo de KRATOS ou outro domínio será tocado
5. Estimar complexidade (baixa/média/alta)

## Output
```
PLAN: {{WAVE_ID}} — {{WAVE_NAME}}
Escopo: {{SCOPE_SUMMARY}}
Arquivos novos: {{NEW_FILES}}
Arquivos modificados: {{MODIFIED_FILES}}
No-touch confirmado: ✅
Complexidade: {{LOW/MEDIUM/HIGH}}
Duração estimada: {{ESTIMATE}}
```
