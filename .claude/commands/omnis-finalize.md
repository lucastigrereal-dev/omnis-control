# /omnis-finalize

Finaliza o bloco atual e prepara handoff.

## Ações
1. Seguir `docs/project-os/FINALIZATION_MANUAL.md`
2. Rodar /omnis-rc para verificar estado
3. Atualizar todos os arquivos de state
4. Gerar handoff em `.claude/state/last-handoff.md`
5. Confirmar que working tree está classificado
6. Reportar GO/NO-GO

## Output
```
FINALIZATION — {{DATE}}
RC: {{GO/NO-GO/CONDITIONAL}}
Handoff: {{GENERATED}}
Working tree: {{CLASSIFIED}}
Próximo bloco: {{NEXT_BLOCK}}
Push autorizado: NÃO (Lucas decide)
```
