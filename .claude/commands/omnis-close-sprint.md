# /omnis-close-sprint <group_id>

Fecha um grupo/sprint concluído.

## Ações
1. Verificar que todas as waves do grupo estão DONE
2. Rodar suite completa
3. Preencher SPRINT_CLOSE_TEMPLATE.md
4. Atualizar ROADMAP.md — mover grupo para verde
5. Atualizar CURRENT_STATE.md
6. Atualizar .claude/state/sprint.json
7. Gerar handoff
8. Comitar

## Stop rules
- Wave do grupo não DONE → não fechar
- Suite quebrando → não fechar
