# /omnis-next

Próxima ação segura a executar.

## Ações
1. Ler `docs/project-os/CURRENT_STATE.md`
2. Ler `docs/project-os/WAVE_REGISTRY.md`
3. Ler `docs/project-os/ROADMAP.md`
4. Verificar P0/P1 em `omnis_blocked_items.yaml`
5. Identificar próxima wave PENDING ou REVIEW
6. Se nenhuma wave ativa, sugerir: audit, cleanup, ou consultar Lucas

## Output
```
PRÓXIMA AÇÃO:
Wave: {{WAVE_ID}} — {{WAVE_NAME}} ({{STATUS}})
Ação: {{CONCRETE_NEXT_STEP}}
Arquivos esperados: {{SCOPE}}
Stop rules: {{STOP_RULES}}
```
